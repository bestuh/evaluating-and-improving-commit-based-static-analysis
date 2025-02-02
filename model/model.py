import torch
from transformers import AutoConfig, AutoModel, AutoTokenizer, pipeline, BertModel
import more_itertools as mit
import torch.optim as optim
import pandas as pd
import ast
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import re
import shutil
from sklearn.metrics import precision_recall_curve, auc
from torch.optim import lr_scheduler

from huggingface_hub import login

def safe_literal_eval(node):
    try:
        return ast.literal_eval(node)
    except ValueError as e:
        print(e)
        return None # happens when literal eval cannot process node

def create_directory(filepath):
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory)

class CommitClassifier(torch.nn.Module):
    def __init__(self, lm_name: str, device: str, fine_tune_lm=(0, 0), diff="lm", combine="mil"):
        super(CommitClassifier, self).__init__()
        self.device = device
        self.fine_tune_lm = fine_tune_lm[0] > 0
        self.fine_tune_lm_for = fine_tune_lm[1]
        self.diff = diff
        self.combine = combine
        
        # language model
        default_lm = "microsoft/codebert-base"
        self.window_overlap = WINDOW_OVERLAP
        self.lm_type = "bert"
        self.lm_name = lm_name
        if "llama" in lm_name or "starcoder" in lm_name: 
            self.lm_type = "gpt"
        self.language_model_config = AutoConfig.from_pretrained(lm_name if lm_name != "random" else default_lm, token=ACCESS_TOKEN)
        self.embedding_size = self.language_model_config.hidden_size
        self.tokenizer = AutoTokenizer.from_pretrained(lm_name if lm_name != "random" else default_lm, token=ACCESS_TOKEN)
        if lm_name == "random":
            print("LM:", lm_name)
            self.language_model = BertModel(self.language_model_config)
        else:
            print("LM:", lm_name)
            self.language_model = AutoModel.from_pretrained(lm_name, token=ACCESS_TOKEN)
        print(f"Memory footprint: {self.language_model.get_memory_footprint() / 1e6:.2f} MB")
        self.language_model.to(device)
        self.freeze_lm(do_not_freeze_layers=fine_tune_lm[0]) # freeze all layers except the ones that should be finetuned
        if self.fine_tune_lm:
            self.language_model.gradient_checkpointing_enable()
        
        if self.lm_type == "gpt":
            self.pipe = pipeline("feature-extraction", 
                framework="pt", 
                model=self.language_model, 
                tokenizer=self.tokenizer,
                torch_dtype=torch.float16,
                device_map="auto",
                #device=device # leads to: ValueError: The model has been loaded with `accelerate` and therefore cannot be moved to a specific device. Please discard the `device` argument when creating your pipeline object.
            )
            self.pipe.tokenizer.pad_token_id = self.language_model.config.eos_token_id
        
        self.dropout_lm = torch.nn.Dropout(p=DROPOUT)

        if self.diff == "funcs":
            self.bi_linear = torch.nn.Bilinear(
                self.embedding_size, 
                self.embedding_size, 
                self.embedding_size
            ).to(device)
        elif self.diff == "transformer":
            self.change_transformer = torch.nn.TransformerEncoder(
                encoder_layer=torch.nn.TransformerEncoderLayer(
                    d_model=self.embedding_size, # input and output dim
                    nhead=DIFF_TRANSFORMER_HEADS,
                    dim_feedforward=DIFF_TRANSFORMER_SIZE # hidden dim
                ),
                num_layers=DIFF_TRANSFORMER_LAYERS
            ).to(device)
        elif self.diff == "linear":
            self.project = torch.nn.Linear(int(self.embedding_size * 2), self.embedding_size).to(device)
            self.dropout_after_proj = torch.nn.Dropout(p=DROPOUT)
               
        if self.combine == "mil":
            # MIL attention
            self.L = self.embedding_size
            self.D = MIL_SIZE
            self.K = 1
            self.mil_attention = torch.nn.Sequential(
                torch.nn.Linear(self.L, self.D),
                torch.nn.Tanh(),
                torch.nn.Linear(self.D, self.K)
            ).to(device)
        elif self.combine == "gmil":
            self.L = self.embedding_size
            self.D = MIL_SIZE
            self.K = 1
            self.mil_attention_V = torch.nn.Sequential(
                torch.nn.Linear(self.L, self.D),
                torch.nn.Tanh()
            ).to(device)
            self.mil_attention_U = torch.nn.Sequential(
                torch.nn.Linear(self.L, self.D),
                torch.nn.Sigmoid()
            ).to(device)
            self.mil_attention_weights = torch.nn.Linear(self.D, self.K).to(device)
        elif self.combine == "transformer":
            self.transformer = torch.nn.TransformerEncoder(
                encoder_layer=torch.nn.TransformerEncoderLayer(
                    d_model=self.embedding_size, # input and output dim
                    nhead=TRANSFORMER_HEADS,
                    dim_feedforward=TRANSFORMER_SIZE # hidden dim
                ),
                num_layers=TRANSFORMER_LAYERS
            ).to(device)
        elif self.combine == "mean":
            pass
        else:
            raise ValueError("Invalid type for parameter 'combine'")

        self.dropout_combine = torch.nn.Dropout(p=DROPOUT)

        # classifier
        self.classifier = torch.nn.Sequential(
            #torch.nn.Linear(int(self.embedding_size * 1), int(self.embedding_size * 1)),
            #torch.nn.ReLU(),

            torch.nn.Linear(int(self.embedding_size * 1), 1),
            torch.nn.Sigmoid()
        ).to(device)
        
    def freeze_lm(self, do_not_freeze_layers=0):
        num_layers = len(self.language_model.encoder.layer if self.lm_type == "bert" else self.language_model.layers)
        #print(f"Freezing {num_layers} layers except last {do_not_freeze_layers}")
        for i, layer in enumerate(self.language_model.encoder.layer if self.lm_type == "bert" else self.language_model.layers):
            fine_tune_layer = num_layers - i <= do_not_freeze_layers
            #print(f"Fine-tune-layer {i+1}: {fine_tune_layer}")
            for param in layer.parameters():
                param.requires_grad = fine_tune_layer

    def _not_empty(self, code_slice):
        return code_slice != None and code_slice != "None" and code_slice != ""
        
    def embed(self, commit):
        code_change_embeddings = []
        for code_change in commit:
            if code_change[0] == "None" and code_change[1] == "None":
                # no extracted code for pre- AND post-version
                code_change_embeddings.append(torch.zeros(self.embedding_size))
            if self.diff == "lm":
                code = (code_change[0] if code_change[0] != "None" else "") + "</s>" + (code_change[1] if code_change[1] != "None" else "")
                code_change_embedding = self.do_embed(code)
                code_change_embeddings.append(code_change_embedding)
            elif self.diff == "funcs":
                code_slice_embedding_pre = self.do_embed(code_change[0]) if code_change[0] != "None" else None
                code_slice_embedding_post = self.do_embed(code_change[1]) if code_change[1] != "None" else None
                code_change_embedding = self.apply_comparison_functions(code_slice_embedding_pre, code_slice_embedding_post)
                code_change_embeddings.append(code_change_embedding) 
            elif self.diff == "transformer":
                code_slice_embedding_pre = self.do_embed(code_change[0]) if self._not_empty(code_change[0]) else torch.zeros(self.embedding_size).to(self.device)
                code_slice_embedding_post = self.do_embed(code_change[1]) if self._not_empty(code_change[1]) else torch.zeros(self.embedding_size).to(self.device)
                
                # transformer to merge pre- and post-versions
                code_change_embedding = self.change_transformer(torch.stack([code_slice_embedding_pre, code_slice_embedding_post]))
                
                if DIFF_POOLING == "mean":
                    code_change_embedding = torch.mean(code_change_embedding, dim=0)
                else:
                    attention_weights = torch.softmax(code_change_embedding, dim=0)  # Apply softmax along sequence dimension
                    code_change_embedding = torch.sum(attention_weights * code_change_embedding, dim=0) # pool

                code_change_embeddings.append(code_change_embedding)
            elif self.diff == "mean":
                code_slice_embedding_pre = self.do_embed(code_change[0]) if self._not_empty(code_change[0]) else torch.zeros(self.embedding_size).to(self.device)
                code_slice_embedding_post = self.do_embed(code_change[1]) if self._not_empty(code_change[1]) else torch.zeros(self.embedding_size).to(self.device)
                code_change_embedding = torch.mean(torch.stack([code_slice_embedding_pre, code_slice_embedding_post]), dim=0)
            elif self.diff == "linear":
                code_slice_embedding_pre = self.do_embed(code_change[0]) if self._not_empty(code_change[0]) else torch.zeros(self.embedding_size).to(self.device)
                code_slice_embedding_post = self.do_embed(code_change[1]) if self._not_empty(code_change[1]) else torch.zeros(self.embedding_size).to(self.device)
                # simple concatenate of pre- and post-versions into one vector
                code_change_embedding = torch.cat([code_slice_embedding_pre, code_slice_embedding_post])
                code_change_embeddings.append(code_change_embedding)

        if len(code_change_embeddings) == 0:
            code_change_embeddings.append(torch.zeros(self.embedding_size))
        return torch.stack(code_change_embeddings).to(self.device)
    
    def windows(self, input_list: list, window_size: int, overlap: int):
        windows = list(mit.windowed(input_list, n=window_size, step=window_size - overlap))
        windows = [list(filter(None, window)) for window in windows]
        windows = [torch.tensor(window) for window in windows]
        return windows

    def do_embed(self, code: str):
        if self.lm_type == "gpt":
            return self._get_embedding_from_gpt([code]).squeeze().to(self.device)

        tokenized = self.tokenizer.encode_plus(code, return_tensors="pt", add_special_tokens=False, padding=False, truncation=False)
        
        # split into windows
        if "codebert" in self.lm_name:
            # for some reason max_position_embeddings is 514 for codebert, which then leads to an error during forward pass
            window_size = 512
        else:
            window_size = self.language_model.config.max_position_embeddings # self.tokenizer.model_max_length
        input_id_windows = self.windows(tokenized["input_ids"][0], window_size - 2, self.window_overlap)
        mask_windows = self.windows(tokenized["attention_mask"][0], window_size - 2, self.window_overlap)

        for i in range(len(input_id_windows)):
            # add special tokens
            input_id_windows[i] = torch.cat([torch.tensor([0]), input_id_windows[i], torch.tensor([2])])
            mask_windows[i] = torch.cat([torch.tensor([1]), mask_windows[i], torch.tensor([1])])

            # add padding
            padding_length = window_size - input_id_windows[i].shape[0]
            if padding_length > 0:
                padding = torch.Tensor([0] * padding_length)
                input_id_windows[i] = torch.cat([input_id_windows[i], padding])
                mask_windows[i] = torch.cat([mask_windows[i], padding])

        input_dict = {
            "input_ids": torch.stack(input_id_windows).long(),
            "attention_mask": torch.stack(mask_windows).int()
        }

        embedding = self._get_embedding_from_bert(input_dict)
        embedding = embedding.mean(dim=0) # combine by taking the mean

        return embedding

    def _get_embedding_from_bert(self, input_dict):
        if self.training and self.fine_tune_lm:
            embedding = self.language_model(
                input_dict["input_ids"].to(self.device),
                attention_mask=input_dict["attention_mask"].to(self.device)
            ).last_hidden_state[:, 0] # [CLS] token
        else:
            with torch.no_grad():
                embedding = self.language_model(
                    input_dict["input_ids"].to(self.device),
                    attention_mask=input_dict["attention_mask"].to(self.device)
                ).last_hidden_state[:, 0] # [CLS] token
        return embedding

    def _get_embedding_from_gpt(self, codes):
        outputs = self.pipe(codes, return_tensors = "pt", truncate=True)
        outputs, attention_mask = self._pad_output(outputs)
        sum_embeddings = torch.sum(outputs * attention_mask, 1)
        sum_mask = torch.clamp(attention_mask.sum(1), min=1e-9)
        embedding = sum_embeddings / sum_mask
        return embedding

    def _pad_output(self, outputs):
        attention_masks = []
        target_size = (self.language_model.config.max_position_embeddings, self.embedding_size)
        for i, _ in enumerate(outputs):
            outputs[i] = outputs[i].squeeze()
            padding = [max(0, target_size[dimension_index] - outputs[i].size(dimension_index)) for dimension_index in range(len(target_size))]
            outputs[i] = torch.nn.functional.pad(outputs[i], (0, padding[1], 0, padding[0]), mode="constant", value=0)
            attention_mask = torch.ones_like(outputs[i])
            attention_mask[outputs[i] == 0] = 0
            attention_masks.append(attention_mask)
        return torch.stack(outputs), torch.stack(attention_masks)
    
    def apply_comparison_functions(self, code_slice_embedding_pre, code_slice_embedding_post):
        if code_slice_embedding_pre is None:
            code_slice_embedding_pre = torch.zeros(code_slice_embedding_post.size())
        if code_slice_embedding_post is None:
            code_slice_embedding_post = torch.zeros(code_slice_embedding_pre.size())

        subtracted = code_slice_embedding_pre - code_slice_embedding_post
        summed = torch.add(code_slice_embedding_pre, code_slice_embedding_post)
        hadamard = torch.mul(code_slice_embedding_pre, code_slice_embedding_post)
        cosine_sim = torch.cosine_similarity(code_slice_embedding_pre, code_slice_embedding_post, dim=0)
        bi = self.bi_linear(code_slice_embedding_pre, code_slice_embedding_post)

        merged = torch.cat((subtracted, summed, hadamard, bi, cosine_sim.view(-1)))
        return merged

    def forward(self, commit):        
        code_change_embeddings = self.embed(commit)
        code_change_embeddings = self.dropout_lm(code_change_embeddings)

        if self.diff == "linear":
            # linear projection (combines concatenated pre & post embeddings into one of smaller size)  
            code_change_embeddings = self.project(code_change_embeddings)
            code_change_embeddings = self.dropout_after_proj(code_change_embeddings)
        
        if self.combine == "mean":
            commit_embedding = torch.mean(code_change_embeddings, dim=0).unsqueeze(0)
        elif self.combine == "mil":
            H = code_change_embeddings
            A = self.mil_attention(H)
            A = torch.transpose(A, 1, 0)
            A = torch.nn.functional.softmax(A, dim=1) # instance-weights
            commit_embedding = torch.mm(A, H)  # apply the weights to the instances
        elif self.combine == "gmil":
            H = code_change_embeddings # input already are the features
            A_V = self.mil_attention_V(H)  # NxD
            A_U = self.mil_attention_U(H)  # NxD
            A = self.mil_attention_weights(A_V * A_U) # element wise multiplication # NxK
            
            A = torch.transpose(A, 1, 0)  # KxN
            A = torch.nn.functional.softmax(A, dim=1) # instance-weights
            commit_embedding = torch.mm(A, H)  # apply the weights to the instances (feature-vectors)
        elif self.combine == "transformer":               
            commit_embedding = self.transformer(code_change_embeddings)
            
            if POOLING == "self-attention":
                attention_weights = torch.softmax(commit_embedding, dim=0)  # apply softmax along sequence dimension
                commit_embedding = torch.sum(attention_weights * commit_embedding, dim=0) # pool
                commit_embedding = commit_embedding.unsqueeze(0)
            elif POOLING == "mean":
                commit_embedding = torch.mean(commit_embedding, dim=0).unsqueeze(0)
            elif POOLING == "max":
                commit_embedding, _ = torch.max(commit_embedding, dim=0)
                commit_embedding = commit_embedding.unsqueeze(0)
            
        commit_embedding = self.dropout_combine(commit_embedding)
        Y_prob = self.classifier(commit_embedding)

        #print("Weights:", A)
        
        return Y_prob#, A

class MILLoss(torch.nn.Module):
    def forward(self, Y_prob, Y_true):
        Y_true = Y_true.float()
        Y_prob = torch.clamp(Y_prob, min=1e-5, max=1. - 1e-5)
        neg_log_likelihood = -1. * (Y_true * torch.log(Y_prob) + (1. - Y_true) * torch.log(1. - Y_prob))  # negative log bernoulli
        return neg_log_likelihood
    
class FocalLoss(torch.nn.Module):
    def __init__(self, alpha=0.25, gamma=2):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, Y_prob, Y_true):
        ce = torch.nn.functional.binary_cross_entropy(Y_prob, Y_true, reduction='none')
        alpha = Y_true * self.alpha + (1. - Y_true) * (1. - self.alpha)
        pt = torch.where(Y_true == 1,  Y_prob, 1 - Y_prob)
        return alpha * (1. - pt) ** self.gamma * ce

class Commits(Dataset):
    def __init__(self, path: str, features_path: str, name:str):
        print(f"Loading dataset {name}")
        # load commit-data
        df_commits = pd.read_csv(path)
        # load features
        df_features = pd.read_csv(features_path)
        df_features["changed_functions"] = df_features["changed_functions"].apply(safe_literal_eval)
        # format changes into correct format for the model
        df_features["data"] = df_features["changed_functions"].apply(lambda changed_functions: self._extract_data(changed_functions))
        # merge commits with features
        df_commits = df_commits.merge(df_features, on="commit_sha", how="left")
        # remove data that is not required to train the model
        df_commits = df_commits.filter(items=["commit_sha", "label", "data"])
        
        # remove commits without features
        df_commits = df_commits.dropna(subset=["data"])
        # remove commits with too many features
        condition = df_commits.apply(lambda row: (len(row["data"]) > 200), axis=1)
        df_commits = df_commits[~condition]
        # remove commits that are vulnerable but no data was extracted for
        condition = df_commits.apply(lambda row: (len(row["data"]) == 0 and row["label"] == 1), axis=1)
        df_commits = df_commits[~condition]
        # remove commits with changes that are too long
        condition = df_commits.apply(lambda row: (self._count_words(row["data"]) > 10000), axis=1)
        df_commits = df_commits[~condition]
        # remove commits without code-changes
        condition = df_commits.apply(lambda row: (len(row["data"]) == 0), axis=1)
        df_commits = df_commits[~condition]
        
        df_commits = df_commits.reset_index(drop=True)
        self.commit_data = df_commits.sample(frac = 1).reset_index(drop=True) # shuffle dataset

    def _extract_data(self, commit) -> list:
        codes = []
        if commit is None:
            return {}
        for file_path, changes in commit.items():
            for line_range, code_slices in changes.items():
                codes.append((code_slices["pre"], code_slices["post"]))
        return codes

    def _count_words(self, codes):
        num_words = 0 
        for code_pre, code_post in codes:
            words_pre = re.split(r'\s+|\\t+|\\n+', code_pre) if code_pre is not None else []
            words_post = re.split(r'\s+|\\t+|\\n+', code_post) if code_post is not None else []
            num_words += len(words_pre) + len(words_post)
        return num_words

    def shuffle(self):
        self.commit_data = self.commit_data.sample(frac = 1).reset_index(drop=True)

    def __len__(self):
        return len(self.commit_data)

    def __getitem__(self, idx):
        # None to "None" to avoid issues with dataloader
        changes = [(pre if pre is not None else "None", post if post is not None else "None") for pre, post in self.commit_data.loc[idx, "data"]] 
        return {
            "commit_sha": self.commit_data.loc[idx, "commit_sha"],
            "changes": changes, 
            "label": self.commit_data.loc[idx, "label"]
        }
    
def commit_collate(batch):
    return [item["commit_sha"] for item in batch], [item["changes"] for item in batch], [item["label"] for item in batch]


all_train_y_preds = []

def train(dataset, epoch_data):
    epoch, num_epochs = epoch_data
    batch_size = 1
    #dataset.shuffle()
    loader = DataLoader(dataset, batch_size=batch_size, collate_fn=commit_collate)
        
    model.train()
    
    if model.fine_tune_lm is True and epoch == model.fine_tune_lm_for + 1:
        print(f"Epoch {epoch}/{num_epochs}: Freezing language model for remaining epochs")
        model.freeze_lm()
    
    train_loss = 0.0
    acc_step_loss = None

    optimizer.zero_grad()

    y_trues = []
    y_preds = []
    for batch_id, batch in tqdm(enumerate(loader), total=len(loader), desc="Training", unit="batch" if batch_size > 1 else "it"):   
        commit_sha = batch[0][0]
        commit = batch[1][0]
        label = torch.FloatTensor([batch[2]]).to(DEVICE)
        
        if DEVICE == "cpu" or DEVICE == "cuda":
            predicted_proba = model.forward(commit)
            loss = criterion(predicted_proba, label) / ACC_STEPS # normalize loss by accumulation steps
            loss.backward() # will accumulate the gradients
            train_loss += loss.item()

            y_trues.append(label.item())
            y_preds.append(predicted_proba.item())

            acc_step_loss = acc_step_loss + loss if acc_step_loss is not None else loss
            if DEBUG:
                print(f"Sample: Label: {label.item()}, Prediction: {predicted_proba.item()}, Loss: {loss.item()}, Running Loss: {(train_loss / (batch_id + 1)):.4f}")
            
            if (batch_id + 1) % ACC_STEPS == 0 or batch_id + 1 == len(loader):
                if DEBUG:
                    print("Step")
                #acc_step_loss /= ACC_STEPS
                #acc_step_loss.backward()
                #torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step() # updates weights based on the accumulated gradients
                optimizer.zero_grad() # reset gradients
                acc_step_loss = None
                    
    # save model after epoch
    save_to = f"{MODEL_PATH}epoch_{epoch}.pt"
    create_directory(save_to)
    torch.save(model.state_dict(), save_to)
    
    all_train_y_preds.append(y_preds)
    total_loss_train = train_loss
    train_loss /= len(loader)
    auc_score = pr_auc(y_true=y_trues, y_pred=y_preds)
    
    plot_prediction_probabilities_3d(all_train_y_preds, bins=20, filename=f"{MODEL_PATH}prediction_probabilities_train.png")
    print(f"Epoch {epoch}/{num_epochs}: Train loss {train_loss:.4f}, Total: {total_loss_train:.4f}, PR AUC: {auc_score:.4f}")
    
    return train_loss

def test(dataset):
    loader = DataLoader(dataset, collate_fn=commit_collate)
    model.eval()
    
    if LOSS == "mil":
        criterion = MILLoss() 
    if LOSS == "bce":
        criterion = torch.nn.BCELoss()
    elif LOSS == "focal":
        if FOCAL_LOSS_ALPHA == "auto":
            alpha = 1 - (sum(dataset.commit_data["label"].values) / len(dataset.commit_data["label"].values))
        else:
            alpha = FOCAL_LOSS_ALPHA
        print(f"Focal Loss alpha: {alpha}")
        criterion = FocalLoss(alpha=alpha, gamma=FOCAL_LOSS_GAMMA)

    total_loss = 0.
    y_id = []
    y_true = []
    y_pred = []
    
    for batch_id, batch in tqdm(enumerate(loader), total=len(loader), desc="Evaluating"):         
        commit_sha = batch[0][0]
        commit = batch[1][0]
        label = torch.FloatTensor([batch[2]]).to(DEVICE)
        
        predicted_proba = model.forward(commit)
        loss = criterion(predicted_proba, label)

        if DEBUG:
            print(f"Sample: Label: {label.item()}, Prediction: {predicted_proba.item()}, Loss: {loss.item()}")
            
        
        total_loss += loss
        y_id.append(commit_sha)
        y_true.append(label.cpu().detach().numpy()[0][0])
        y_pred.append(predicted_proba.cpu().detach().numpy()[0][0])
    
    total_loss /= len(loader)
    return y_id, y_true, y_pred, total_loss.item()


class EarlyStopping:
    def __init__(self, patience=1, min_delta=0.0):
        self.patience = patience  # number of times to allow for no improvement before stopping the execution
        self.min_delta = min_delta  # the minimum change to be counted as improvement
        self.counter = 0  # count the number of times the loss not improving
        self.min_loss = np.inf

    # return True when encountering _patience_ times decrease in loss 
    def check_stop(self, loss):
        print(loss, self.min_loss)
        print("Delta: ", self.min_loss - loss)
        if (loss + self.min_delta < self.min_loss):
            self.min_loss = loss
            self.counter = 0  # reset the counter if loss decreased at least by min_delta
        elif (loss + self.min_delta > self.min_loss):
            self.counter += 1 # increase the counter if loss is not decreased by the min_delta
            if self.counter >= self.patience:
                return True
        return False

def pr_auc(y_true, y_pred):
    precision, recall, _ = precision_recall_curve(y_true, y_pred)
    return auc(recall, precision)

def plot_loss(train_losses, validation_losses, filename=""):
    if train_losses is not None:
        plt.plot(train_losses, label="Training Loss", marker="x")
    if validation_losses is not None:
        plt.plot(validation_losses, label="Validation Loss", marker="x")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.savefig(filename)
    plt.show()
    plt.clf()

def plot_prediction_probabilities_3d(y_preds_per_epoch, bins=10, filename=""):
    my_cmap = plt.cm.inferno
    fig = plt.figure(figsize=(10,10))
    ax = fig.add_subplot(projection="3d")
    #define the yticks, i.e., the column numbers
    yticks = np.arange(1, len(y_preds_per_epoch) + 1, 1)
    #we create evenly spaced bins between the minimum and maximum of the entire dataframe
    xbins = np.linspace(0, 1, bins + 1)
    #and calculate the center and widths of the bars
    xcenter = np.convolve(xbins, np.ones(2), "valid")/2
    xwidth = np.diff(xbins)
    #calculate now the histogram and plot it for each column
    for i, ytick in enumerate(yticks):
        #determine the histogram values, here you have to adapt it to your needs
        histvals, _ = np.histogram(y_preds_per_epoch[i], bins=xbins)
        #plot the histogram as a bar for each bin
        #now with continuous color mapping and edgecolor, but thinner lines, so we can better see all bars
        ax.bar(left=xcenter, height=histvals, width=xwidth, zs=ytick, zdir="y", color=my_cmap(i/len(y_preds_per_epoch)), alpha=0.666, edgecolor="grey", linewidth=0.3)
    ax.set_xlabel("Probabilities")
    ax.set_ylabel("Epoch")
    ax.set_zlabel("Frequency")
    ax.set_xticks(xbins[::2])
    ax.set_yticks(yticks)
    ax.view_init(35, -90 + 10)
    plt.savefig(filename)
    plt.clf()

def get_existing_checkpoint():
    if not os.path.exists(MODEL_PATH) or not os.path.isdir(MODEL_PATH):
        return False, None

    pattern = r'epoch_(\d+)\.pt'
    highest_epoch = 0

    for filename in os.listdir(MODEL_PATH):
        match = re.match(pattern, filename)
        if match:
            epoch_number = int(match.group(1))
            highest_epoch = epoch_number if epoch_number > highest_epoch else highest_epoch

    if highest_epoch > 0:
        return f"{MODEL_PATH}epoch_{highest_epoch}.pt", highest_epoch
    else:
        return False, None


def print_param(param_name):
    print(f"{param_name}: {globals()[param_name]}")

def print_params():
    print("Settings:")
    print("------------------------------------------------------------------------------------------")
    print("Paths")
    print_param("BASE_PATH")
    print_param("MODEL_PATH")
    print_param("RESULTS_PATH")
    print_param("IN_FILE_TRAIN")
    print_param("IN_FILE_VAL")
    print_param("IN_FILE_TEST")
    print_param("IN_FILE_FEATURES_TRAIN")
    print_param("IN_FILE_FEATURES_VAL")
    print_param("IN_FILE_FEATURES_TEST")
    print()
    print("Controls")
    print_param("TRAIN")
    print_param("CHECKPOINT")
    print_param("DEVICE")
    print()
    print("Model")
    print_param("LM")
    print_param("DIFF")
    print_param("COMBINE")
    print_param("DROPOUT")
    print_param("DIFF_TRANSFORMER_LAYERS")
    print_param("DIFF_TRANSFORMER_HEADS")
    print_param("DIFF_TRANSFORMER_SIZE")
    print_param("DIFF_POOLING")
    print_param("TRANSFORMER_LAYERS")
    print_param("TRANSFORMER_HEADS")
    print_param("TRANSFORMER_SIZE")
    print_param("POOLING")
    print_param("MIL_SIZE")
    print()
    print("Training")
    print_param("EPOCHS")
    print_param("ACC_STEPS")
    print_param("FINE_TUNE_LAYERS")
    print_param("FINE_TUNE_LAYERS_FOR")

    print_param("LOSS")
    print_param("FOCAL_LOSS_GAMMA")
    print_param("FOCAL_LOSS_ALPHA")

    print_param("OPTIM")
    print_param("WEIGHT_DECAY")
    print_param("MOMENTUM")
    
    print_param("WARMUP_STEPS")
    print_param("WARMUP_FACTOR")
    print_param("SCHEDULER")
    print_param("LEARNING_RATE")
    print_param("SCHEDULER_EPOCHS")
    print_param("SCHEDULER_GAMMA")

    print_param("EARLY_STOPPING_EPOCHS")
    print_param("EARLY_STOPPING_DELTA")
    print_param("WINDOW_OVERLAP")

    print("------------------------------------------------------------------------------------------")

if __name__ == "__main__":
    ACCESS_TOKEN = "" # put huggingface access token (required for downloading some of the models)
    login(token=ACCESS_TOKEN)

    # paths
    BASE_PATH = os.path.expanduser(f"../data/linux/linux-unbalanced/")
    MODEL_PATH = f"{BASE_PATH}model_linux/"
    RESULTS_PATH = f"{BASE_PATH}model_linux/"
    MODEL_NAME = os.path.basename(os.path.normpath(MODEL_PATH))

    IN_FILE_TRAIN = f"{BASE_PATH}train.csv"
    IN_FILE_VAL = f"{BASE_PATH}validation.csv"
    IN_FILE_TEST = f"{BASE_PATH}test.csv"

    IN_FILE_FEATURES_TRAIN = f"{BASE_PATH}code_slices.csv"
    IN_FILE_FEATURES_VAL = f"{BASE_PATH}code_slices.csv"
    IN_FILE_FEATURES_TEST = f"{BASE_PATH}code_slices.csv"

    # controls
    # set TRAIN to False and CHECKPOINT to the respective model checkpoint, if you only want to evaluate an already trained model
    TRAIN = True
    CHECKPOINT = None #f"{MODEL_PATH}epoch_18.pt"
    DEVICE = "cuda" # "cuda" or "cpu"

    # model
    LM = "random" # microsoft/codebert-base, bigcode/starencoder, random, codellama/CodeLlama-7b-hf
    DIFF = "transformer" # mean, lm, funcs, transformer, linear
    COMBINE = "gmil" # mean, mil, gmil, transformer
    DROPOUT = 0.5
    # if DIFF set to: transformer
    DIFF_TRANSFORMER_LAYERS = 2
    DIFF_TRANSFORMER_HEADS = 4
    DIFF_TRANSFORMER_SIZE = 786
    DIFF_POOLING = "mean" # self-attention, mean
    # if COMBINE set to: transformer
    TRANSFORMER_LAYERS = 1
    TRANSFORMER_HEADS = 4
    TRANSFORMER_SIZE = 200
    POOLING = "mean" # self-attention, mean, max, cls
    # if COMBIINE set to: mil or gmil
    MIL_SIZE = 384

    # training
    EPOCHS = 40 
    ACC_STEPS = 8
    FINE_TUNE_LAYERS = 0 # number of (last) layers of the language model to be fine-tuned. 0 = the LM will not be finetuned at all
    FINE_TUNE_LAYERS_FOR = EPOCHS - 0 # number of epochs the language model will be fine-tuned. After this number of epochs, the language model will be frozen
    
    LOSS = "focal" # mil, bce, focal
    FOCAL_LOSS_GAMMA = 2
    FOCAL_LOSS_ALPHA = 0.75
    
    OPTIM = "adamw"
    WEIGHT_DECAY = 0.01
    MOMENTUM = 0.9

    SCHEDULER = "ExponentialLR"
    LEARNING_RATE = 0.0001
    WARMUP_STEPS = 2 # decreases lr for the first n epochs by factor below
    WARMUP_FACTOR = 0.03
    SCHEDULER_EPOCHS = 1
    SCHEDULER_GAMMA = 0.9
    
    EARLY_STOPPING_EPOCHS = 5
    EARLY_STOPPING_DELTA = 0.0001
    WINDOW_OVERLAP = 256

    DEBUG = False

    if TRAIN is True:
        # write parameters to file in model-dir
        original_stdout = sys.stdout
        create_directory(f"{MODEL_PATH}settings.txt")
        with open(f"{MODEL_PATH}settings.txt", "w+") as log_file:
            sys.stdout = log_file
            print_params()
        sys.stdout = original_stdout
    print_params()

    print("Creating model")
    model = CommitClassifier(LM, device=DEVICE, fine_tune_lm=(FINE_TUNE_LAYERS, FINE_TUNE_LAYERS_FOR), diff=DIFF, combine=COMBINE)
    epoch_with_min_val_loss = None
    existing_checkpoint_epoch = None
    if TRAIN is True:
        if CHECKPOINT is not None:
            print(f"Loading specified model checkpoint {CHECKPOINT}")
            model.load_state_dict(torch.load(CHECKPOINT))
        else:
            existing_checkpoint, existing_checkpoint_epoch = get_existing_checkpoint()
            if existing_checkpoint is not False:
                print(f"Loading existing model checkpoint {existing_checkpoint}")
                model.load_state_dict(torch.load(existing_checkpoint))

        dataset_train = Commits(IN_FILE_TRAIN, IN_FILE_FEATURES_TRAIN, "train")
            
        dataset_val = Commits(IN_FILE_VAL, IN_FILE_FEATURES_VAL, "validation")
        if OPTIM == "adam":
            optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
        if OPTIM == "adamw":
            optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
        if OPTIM == "sgd": 
            optimizer = optim.SGD(model.parameters(), lr=LEARNING_RATE, momentum=MOMENTUM, weight_decay=WEIGHT_DECAY)
        early_stopper = EarlyStopping(patience=EARLY_STOPPING_EPOCHS, min_delta=EARLY_STOPPING_DELTA)  

        if SCHEDULER is not None:
            warmup_scheduler = optim.lr_scheduler.ConstantLR(optimizer, factor=WARMUP_FACTOR, total_iters=WARMUP_STEPS)
            if SCHEDULER == "ExponentialLR":
                lr_scheduler = optim.lr_scheduler.ExponentialLR(optimizer, gamma=SCHEDULER_GAMMA)
            scheduler = optim.lr_scheduler.SequentialLR(optimizer, schedulers=[warmup_scheduler, lr_scheduler], milestones=[WARMUP_STEPS])

        if LOSS == "mil":
            criterion = MILLoss() 
        if LOSS == "bce":
            criterion = torch.nn.BCELoss()
        elif LOSS == "focal":
            if FOCAL_LOSS_ALPHA == "auto":
                alpha = 1 - (sum(dataset_train.commit_data["label"].values) / len(dataset_train.commit_data["label"].values))
            else:
                alpha = FOCAL_LOSS_ALPHA
            print(f"Focal Loss alpha: {alpha}")
            criterion = FocalLoss(alpha=alpha, gamma=FOCAL_LOSS_GAMMA)
            
        loss_values_train = []
        loss_values_val = []
        predicted_probabilities_val = []
        last_epoch = 0

        # evaluate before starting the training (with initialized but untrained model)
        _, y_trues, y_preds, val_loss = test(dataset_val)
        loss_values_val.append(val_loss)
        predicted_probabilities_val.append(y_preds)
        auc_score = pr_auc(y_true=y_trues, y_pred=y_preds)
        plot_loss(None, loss_values_val, filename=f"{MODEL_PATH}loss.png")
        plot_prediction_probabilities_3d(predicted_probabilities_val, bins=20, filename=f"{MODEL_PATH}prediction_probabilities_val.png")
        print(f"Before training: Validation-Loss: {val_loss:.4f}, PR AUC: {auc_score:.4f}")

        _, y_trues, y_preds, train_loss = test(dataset_train)
        loss_values_train.append(train_loss)
        predicted_probabilities_val.append(y_preds)
        auc_score = pr_auc(y_true=y_trues, y_pred=y_preds)
        plot_loss(loss_values_train, loss_values_val, filename=f"{MODEL_PATH}loss.png")
        print(f"Before training: Training-Loss: {train_loss:.4f}, PR AUC: {auc_score:.4f}")

        for epoch in range(1, EPOCHS + 1):
            train_loss = train(dataset_train, (epoch, EPOCHS))
            loss_values_train.append(train_loss)
            _, y_trues, y_preds, val_loss = test(dataset_val)
            loss_values_val.append(val_loss)
            predicted_probabilities_val.append(y_preds)
            if SCHEDULER != None:
                scheduler.step()
            
            print(f"Epoch {epoch}/{EPOCHS} validation loss {val_loss:.4f}")#, PR AUC: {auc_score:.4f}")
            last_epoch = epoch

            plot_loss(loss_values_train, loss_values_val, filename=f"{MODEL_PATH}loss.png")
            plot_prediction_probabilities_3d(predicted_probabilities_val, bins=20, filename=f"{MODEL_PATH}prediction_probabilities_val.png")
            
            if early_stopper.check_stop(val_loss):
                print(f"Stopping training since no improvement since {early_stopper.counter} epochs")
                break
        print("Losses of all epochs (train):", loss_values_train)
        print("Losses of all epochs (valid):", loss_values_val)

        epoch_with_min_val_loss = max(loss_values_val.index(min(loss_values_val)) + 1 - 1, 1) # -1 because first value is untrained and does not correspond to an epoch

        # load model from last epoch
        model.load_state_dict(torch.load(f"{MODEL_PATH}epoch_{last_epoch}.pt"))
    else:
        # load model from specified checkpoint
        model.load_state_dict(torch.load(CHECKPOINT))

    dataset_test = Commits(IN_FILE_TEST, IN_FILE_FEATURES_TEST, "test")
    y_id, y_true, y_pred, test_loss = test(dataset_test)
    print(f"Test loss: {test_loss:.4f}")
    results = pd.DataFrame({
        "commit_sha": y_id,
        "y_true": y_true,
        "y_pred": y_pred
    })
    results.to_csv(f"{RESULTS_PATH}results.csv", index=False)

    if epoch_with_min_val_loss is not None:
        # load model from best epoch (on validation data)
        model.load_state_dict(torch.load(f"{MODEL_PATH}epoch_{epoch_with_min_val_loss}.pt"))
        y_id, y_true, y_pred, test_loss = test(dataset_test)
        print(f"Test loss (model of epoch {epoch_with_min_val_loss}): {test_loss:.4f}")
        results = pd.DataFrame({
            "commit_sha": y_id,
            "y_true": y_true,
            "y_pred": y_pred
        })
        results.to_csv(f"{RESULTS_PATH}results_{MODEL_NAME}_epoch_{epoch_with_min_val_loss}.csv", index=False)

    # persist output log
    #if TRAIN is True:
    #    if existing_checkpoint_epoch is None:
    #        shutil.copy(f"{BASE_PATH}res.txt", f"{MODEL_PATH}log.txt")
    #    else:
    #        shutil.copy(f"{BASE_PATH}res.txt", f"{MODEL_PATH}log_from_{existing_checkpoint_epoch}.txt")