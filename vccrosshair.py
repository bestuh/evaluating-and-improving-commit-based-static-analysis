import importlib
import file_utils
from file_utils import DataCheckpoint
from tqdm import tqdm
import pandas as pd

from scipy.sparse import load_npz
import glob
Svm = importlib.import_module("tools.vcc-mapper.Classifier.Replication.Svm")
Commit = importlib.import_module("tools.vcc-mapper.Classifier.Replication.Commit")


class VCCrosshair:

    def __init__(self):
        self.data_checkpoint = DataCheckpoint()
        self.repo_path = "repositories/"

    
    def preprocess(self, dataset_name):
        print(f"Generating input data for dataset \"{dataset_name}\"")
        self.preprocess_split(dataset_name, "train")
        self.preprocess_split(dataset_name, "test")


    def train(self, dataset_name, model_name="model", split="train"):
        vcc_files = glob.glob(self.data_checkpoint.build_path(f"{dataset_name}/vccrosshair/{split}/vcc/*"))
        non_vcc_files = glob.glob(self.data_checkpoint.build_path(f"{dataset_name}/vccrosshair/{split}/non_vcc/*"))

        if len(vcc_files) == 0 or len(non_vcc_files) == 0:
            print("ERROR: Could not find any input data. Make sure to run preprocess() first.")
            exit(1)

        vccs = [load_npz(feature_vector_file) for feature_vector_file in tqdm(vcc_files, total=len(vcc_files), desc="Loading VCCs")]
        non_vccs = [load_npz(feature_vector_file) for feature_vector_file in tqdm(non_vcc_files, total=len(non_vcc_files), desc="Loading non-VCCs")]

        print(f"Training model \"{model_name}\" on {len(vccs) + len(non_vccs)} samples (VCCs: {len(vccs)}, non VCCs: {len(non_vccs)})")
        model_path = self.data_checkpoint.build_path(f"{dataset_name}/vccrosshair/{model_name}")
        file_utils.create_directory(model_path)
        svm = Svm.Svm()
        svm.train_model(vccs, non_vccs)
        svm.save_model(model_path)
        print("Finished training.")


    def test(self, dataset_name, model_name="model", split="test"):
        vcc_files = glob.glob(self.data_checkpoint.build_path(f"{dataset_name}/vccrosshair/{split}/vcc/*"))
        non_vcc_files = glob.glob(self.data_checkpoint.build_path(f"{dataset_name}/vccrosshair/{split}/non_vcc/*"))

        if len(vcc_files) == 0 or len(non_vcc_files) == 0:
            print("ERROR: Could not find any input data. Make sure to run preprocess() first.")
            exit(1)

        vccs = [load_npz(feature_vector_file) for feature_vector_file in vcc_files]
        non_vccs = [load_npz(feature_vector_file) for feature_vector_file in non_vcc_files]

        vcc_ids = [feature_vector_file.split("/")[-1].split(".")[0] for feature_vector_file in vcc_files]
        non_vcc_ids = [feature_vector_file.split("/")[-1].split(".")[0] for feature_vector_file in non_vcc_files]

        print(f"Predicting on {len(vccs) + len(non_vccs)} samples (VCCs: {len(vccs)}, non VCCs: {len(non_vccs)}) using model \"{model_name}\"")

        model_path = self.data_checkpoint.build_path(f"{dataset_name}/vccrosshair/{model_name}")
        svm = Svm.Svm()
        svm.load_model(model_path)

        Y_id = []
        Y_true = []
        Y_pred = []
        Y_conf = []
        
        for i, vec in enumerate(vccs):
            prediction, confidence = svm.predict_confidence(vec)
            Y_id.append(vcc_ids[i])
            Y_true.append(1)
            Y_pred.append(prediction)
            Y_conf.append(confidence)

        for i, vec in enumerate(non_vccs):
            prediction, confidence = svm.predict_confidence(vec)
            Y_id.append(non_vcc_ids[i])
            Y_true.append(0)
            Y_pred.append(prediction)
            Y_conf.append(confidence)

        results_df = pd.DataFrame({
            "commit_sha": Y_id,
            "y_true": Y_true,
            "y_pred": Y_pred,
            "distance": Y_conf
        })

        results_path = self.data_checkpoint.build_path(f"{dataset_name}/vccrosshair/results_{split}.csv")
        print(f"Saving results to {results_path}")
        results_df.to_csv(results_path, index=False)


    def preprocess_split(self, dataset_name, split):
        samples = self.data_checkpoint.get(f"{dataset_name}/{split}.csv")
        vcc_ids, non_vcc_ids, repositories_vcc, repositories_non_vcc = [], [], [], []

        id_col = None
        label_col = None
        project_col = None

        for idx, sample in enumerate(samples):
            if idx == 0:
                id_col = sample.index("commit_sha")
                label_col = sample.index("label")
                project_col = sample.index("project")
                continue # skip header row
            if int(float(sample[label_col])) == 1:
                repositories_vcc.append(f"{self.repo_path}/{sample[project_col]}")
                vcc_ids.append(sample[id_col])
            else:
                repositories_non_vcc.append(f"{self.repo_path}/{sample[project_col]}")
                non_vcc_ids.append(sample[id_col])

        #repository = self.data_checkpoint.repo_dir
        self.save_feature_vectors(vcc_ids, repositories_vcc, dataset_name, split, commit_type="vcc")
        self.save_feature_vectors(non_vcc_ids, repositories_non_vcc, dataset_name, split, commit_type="non_vcc")


    def save_feature_vectors(self, commit_ids, repo_paths, dataset_name, split, commit_type):
        vccrosshair_data_dir = self.data_checkpoint.build_path(f"{dataset_name}/vccrosshair/")
        save_to = f"{vccrosshair_data_dir}{split}/{commit_type}"
        file_utils.create_directory(save_to + "/")
        print(f"Saving feature vectors to \"{save_to}/\"")

        for idx, commit_id in tqdm(enumerate(commit_ids), total=len(commit_ids)):
            # skip duplicates
            existing_feature_vectors = glob.glob(f"{vccrosshair_data_dir}*/*/*.npz")
            existing_feature_vectors = [path.replace("\\", "/") for path in existing_feature_vectors]
            if f"{save_to}/{commit_id}.npz" in existing_feature_vectors:
                print(f"Duplicate, skipping commit {commit_id}")
                continue

            try:
                commit = Commit.Commit(repo_paths[idx], commit_id)
                commit.store_feature_vector_in(save_to)
            except Exception as e:
                print(f"Failed for commit: {commit_id} from {repo_paths[idx]}")
                print(e)