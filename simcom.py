from file_utils import DataCheckpoint
import file_utils
import docker_utils
import git_utils
import nltk
from tqdm import tqdm
import string
from sklearn.model_selection import train_test_split

class SimCom():
    
    def __init__(self):
        self.data_checkpoint = DataCheckpoint()
        self.data_dir = "/opt/data/"
        self.docker_app_dir = "/opt/simcom/"
        self.lapredict_data_path = f"data/{self.data_checkpoint.params.project}/<dataset-name>/lapredict/data/" #"tools/lapredict/code/JIT_Baseline/data/"

    def preprocess(self, dataset_name):
        print(f"Generating input data for dataset \"{dataset_name}\"")
        
        self.lapredict_data_path = self.lapredict_data_path.replace("<dataset-name>", dataset_name)
        print("LAPredict data path:", self.lapredict_data_path)

        # simply copy data for simple model from LAPredict
        self.copy_dataset(
            copy_from=f"{self.lapredict_data_path}{self.data_checkpoint.params.project}/{self.data_checkpoint.params.project}_k_feature.csv", 
            copy_to=f"data/{self.data_checkpoint.params.project}/{dataset_name}/simcom/simple/dataset.csv"
        )
        self.copy_dataset(
            copy_from=f"{self.lapredict_data_path}{self.data_checkpoint.params.project}/k_train.csv",
            copy_to=f"data/{self.data_checkpoint.params.project}/{dataset_name}/simcom/simple/train.csv"
        )
        self.copy_dataset(
            copy_from=f"{self.lapredict_data_path}{self.data_checkpoint.params.project}/k_test.csv",
            copy_to=f"data/{self.data_checkpoint.params.project}/{dataset_name}/simcom/simple/test.csv"
        )

        # move it to simcom
        self.copy_dataset(
            copy_from=f"data/{self.data_checkpoint.params.project}/{dataset_name}/simcom/simple/train.csv",
            copy_to=f"tools/simcom/code/data/hand_crafted_features/{self.data_checkpoint.params.project}/k_train.csv"
        )
        self.copy_dataset(
            copy_from=f"data/{self.data_checkpoint.params.project}/{dataset_name}/simcom/simple/test.csv",
            copy_to=f"tools/simcom/code/data/hand_crafted_features/{self.data_checkpoint.params.project}/k_test.csv"
        )

        # generate data for complex model
        self.generate_input_data(dataset_name, "dataset")
        self.generate_input_data(dataset_name, "train")
        self.generate_input_data(dataset_name, "test")
        self.generate_vocabulary(dataset_name)

        # simple and complex samples need to be the same amount => make sure that is the case (since simple samples are generated via LAPredict)
        test_data_complex = self.data_checkpoint.get(f"{dataset_name}/simcom/complex/test.pkl")
        test_data_simple = self.data_checkpoint.get(f"{dataset_name}/simcom/simple/test.csv")
        simple_sample_ids = []
        for i, simple_sample in enumerate(test_data_simple):
            if i == 0: continue
            simple_sample_ids.append(simple_sample[1])
        delete_complex_samples = []
        print("simple", len(test_data_simple), "complex", len(test_data_complex[0]))
        if len(test_data_complex[0]) != len(test_data_simple):
            for complex_sample_id in test_data_complex[0]:
                if complex_sample_id not in simple_sample_ids:
                    delete_complex_samples.append(complex_sample_id)
        print("Need to delete", len(delete_complex_samples), " samples from complex dataset:", delete_complex_samples)
        for delete_id in delete_complex_samples:
            delete_index = test_data_complex[0].index(delete_id)
            del test_data_complex[0][delete_index]
            del test_data_complex[1][delete_index]
            del test_data_complex[2][delete_index]
            del test_data_complex[3][delete_index]
        print("simple", len(test_data_simple), "complex", len(test_data_complex[0]))
        self.data_checkpoint.create(f"{dataset_name}/simcom/complex/test.pkl", test_data_complex)

        # generate validation split (TODO: hacky way => redo it correctly)
        ids, labels, msgs, codes = self.data_checkpoint.get(f"{dataset_name}/simcom/complex/dataset.pkl")
        _, valid_ids = train_test_split(ids, test_size=0.3, shuffle=True)
        valid = ([], [], [], [])
        for commit_index, commit_id in enumerate(ids):
            if commit_id in valid_ids:
                valid[0].append(ids[commit_index])
                valid[1].append(labels[commit_index])
                valid[2].append(msgs[commit_index])
                valid[3].append(codes[commit_index])
        self.data_checkpoint.create(f"{dataset_name}/simcom/complex/val.pkl", valid)

        # move it to simcom
        self.copy_dataset(
            copy_from=f"data/{self.data_checkpoint.params.project}/{dataset_name}/simcom/complex/train.pkl",
            copy_to=f"tools/simcom/code/data/commit_cotents/processed_data/{self.data_checkpoint.params.project}/{self.data_checkpoint.params.project}_train.pkl"
        )
        self.copy_dataset(
            copy_from=f"data/{self.data_checkpoint.params.project}/{dataset_name}/simcom/complex/test.pkl",
            copy_to=f"tools/simcom/code/data/commit_cotents/processed_data/{self.data_checkpoint.params.project}/{self.data_checkpoint.params.project}_test.pkl"
        )
        self.copy_dataset(
            copy_from=f"data/{self.data_checkpoint.params.project}/{dataset_name}/simcom/complex/dict.pkl",
            copy_to=f"tools/simcom/code/data/commit_cotents/processed_data/{self.data_checkpoint.params.project}/{self.data_checkpoint.params.project}_dict.pkl"
        )
        self.copy_dataset(
            copy_from=f"data/{self.data_checkpoint.params.project}/{dataset_name}/simcom/complex/val.pkl",
            copy_to=f"tools/simcom/code/data/commit_cotents/processed_data/{self.data_checkpoint.params.project}/{self.data_checkpoint.params.project}_val.pkl"
        )

    def copy_dataset(self, copy_from, copy_to):
        print(f"Copying dataset from \"{copy_from}\" to \"{copy_to}\"")
        if file_utils.file_exists(copy_to):
            print(f"Dataset \"{copy_to}\" already exists. Please delete, if you want to regenerate it.")
            return

        if copy_from.endswith(".csv"):
            dataset = file_utils.read_csv(copy_from)
        elif copy_from.endswith(".pkl"):
            dataset = file_utils.read_pickle(copy_from)
        else:
            print("Error. Unsupported file-type.")
            exit()

        if copy_from.endswith(".csv"):
            file_utils.write_csv(copy_to, dataset)
        elif copy_from.endswith(".pkl"):
            file_utils.write_pickle(copy_to, dataset)
        else:
            print("Error. Unsupported file-type.")
            exit()
        

    def generate_vocabulary(self, dataset_name):
        read_from = f"{dataset_name}/simcom/complex/dataset.pkl"
        save_to = f"{dataset_name}/simcom/complex/dict.pkl"

        print(f"Generating complex-model input vocabulary based on \"{self.data_checkpoint.build_path(read_from)}\"...")
        if self.data_checkpoint.exists(save_to):
            print(f"The vocabulray \"{self.data_checkpoint.build_path(save_to)}\" already exists. Please delete, if you want to regenerate it.")
            return self.data_checkpoint.get(save_to)
        
        _, _, msgs, codes = self.data_checkpoint.get(read_from)
        
        vocabulary_msg = {"<NULL>": 0, "<null>": 1}
        vocabulary_code = {"<NULL>": 0, "<null>": 1, "added_code:": 2, "removed_code:": 3}
        msg_counter = vocabulary_msg[max(vocabulary_msg)] + 1
        code_counter = vocabulary_code[max(vocabulary_code)] + 1

        for sample_msg in msgs:
            for token in sample_msg.split(" "):
                if not token.lower() in vocabulary_msg:
                    vocabulary_msg[token.lower()] = msg_counter
                    msg_counter = msg_counter + 1
        
        for sample_code in codes:
            for file in sample_code:
                for token in file.split(" "):
                    if not token.lower() in vocabulary_code:
                        vocabulary_code[token.lower()] = code_counter
                        code_counter = code_counter + 1
        
        vocabulary = (vocabulary_msg, vocabulary_code)
        self.data_checkpoint.create(save_to, vocabulary)
        #self.data_checkpoint.create(save_to.replace(".pkl", ".json"), vocabulary)
        return vocabulary

    def generate_input_data(self, dataset_name, split):
        read_from = f"{dataset_name}/{split}.csv"
        save_to = f"{dataset_name}/simcom/complex/{split}.pkl"

        print(f"Generating complex-model input (adjusted DeepJIT format) based on commits in \"{self.data_checkpoint.build_path(read_from)}\"...")
        if self.data_checkpoint.exists(save_to):
            print(f"The input data \"{self.data_checkpoint.build_path(save_to)}\" already exists. Please delete, if you want to regenerate it.")
            return self.data_checkpoint.get(save_to)
        
        samples = self.data_checkpoint.get(read_from)
        id_col = None
        label_col = None
        project_col = None
        commit_ids = []
        labels = []
        repos = []
        for idx, sample in enumerate(samples):
            if idx == 0:
                # header row
                id_col = sample.index("commit_sha")
                label_col = sample.index("label")
                project_col = sample.index("project")
                continue
            commit_ids.append(sample[id_col])
            labels.append(sample[label_col])
            repos.append(f"repositories/{sample[project_col]}/")

        # group by repo, so we can get all commits per repo at once
        commits_per_repo = {}
        for commit_id, repo in zip(commit_ids, repos):
            if repo not in commits_per_repo:
                commits_per_repo[repo] = []
            commits_per_repo[repo].append(commit_id)

        commits = []
        for repo, commits_in_repo in commits_per_repo.items():
            commits += git_utils.get_commits(repo, commits_in_repo)

        ADDED_CODE_SEP = "added_code: "
        REMOVED_CODE_SEP = "removed_code: "
        max_num_files = 10 # number of files to consider at max. (others will be skipped) 
        max_num_lines = 11 # number of lines to consider at max. (others will be skipped) 

        dataset = ([], [], [], []) # ids, labels, msgs, codes

        commit_index = -1 
        for commit in tqdm(commits):
            commit_index = commit_index + 1

            if len(commit.parents) == 0:
                print("Commit has no parents")
                continue
            first_parent = commit.parents[0]
            diffs = first_parent.diff(commit, create_patch=True, unified=0)

            files = []
            for diff in diffs:
                if len(files) == max_num_files: break # only consider the first 10 files

                hunks = str(diff).split("@@ -")
                if self._skip_file(hunks): continue
                del hunks[0]

                additions_in_file = []
                deletions_in_file = []
                for hunk in hunks:
                    hunk_lines = hunk.split("\n")
                    additions_in_hunk, deletions_in_hunk = self._get_additions_and_deletions(hunk_lines)
                    additions_in_file.extend(additions_in_hunk)
                    deletions_in_file.extend(deletions_in_hunk)

                if len(additions_in_file):
                    additions_in_file = additions_in_file[:max_num_lines]
                if len(deletions_in_file):
                    deletions_in_file = deletions_in_file[:max_num_lines]

                addition_string = " " + " ".join(additions_in_file) if len(additions_in_file) else ""
                removal_string = " " + " ".join(deletions_in_file) if len(deletions_in_file) else ""
                file = ADDED_CODE_SEP + addition_string + " " + REMOVED_CODE_SEP + removal_string
                files.append(file)
             
            dataset[0].append(commit.hexsha)
            dataset[1].append(int(float(labels[commit_ids.index(commit.hexsha)])))
            dataset[2].append(self._tokenize(commit.message))
            dataset[3].append(files)
            
        self.data_checkpoint.create(save_to, dataset)
        return dataset

    def _skip_file(self, hunks):
        only_added = "file added in rhs" in hunks[0]
        only_renamed = "file renamed to" in hunks[0] and "lhs: None" in hunks[0] and "rhs: None" in hunks[0] 
        binary_file = "---Binary" in hunks[0]
        return only_added or only_renamed or binary_file
    
    def _get_additions_and_deletions(self, lines):
        additions, deletions = [], []
        for line in lines:
            if line == "": continue
            additions = self._process_line(line, ["+\t", "+"], additions)
            deletions = self._process_line(line, ["-\t", "-"], deletions)
        return additions, deletions
    
    def _process_line(self, line, line_prefixes, lines):
        if line == "" or line == "---": 
            return lines
        
        for line_prefix in line_prefixes:
            if line.startswith(line_prefix):
                line = line.replace(line_prefix, "", 1)
                processed_line = self._tokenize(line, do_lower=False)
                if processed_line != "":
                    lines.append(processed_line)
                else:
                    lines.append("")
        return lines


    def _tokenize(self, string, do_lower=True):
        tokenizer = nltk.tokenize.RegexpTokenizer(r"[a-zA-Z\d'\"#!\$\x93-\xFF\u0080-\u2318`]+|[^\s]")
        tokens = tokenizer.tokenize(string)
        if do_lower:
            tokens = [token.lower() for token in tokens]
        tokens = list(filter(lambda token: token != "_", tokens))
        return " ".join(tokens)

    def run_simple(self):
        print("Running Sim")
        command = f"bash -c 'cd {self.docker_app_dir}Sim && python sim_model.py -project {self.data_checkpoint.params.project}'"
        docker_utils.run_in_docker("simcom", command)

    def train_complex(self):
        print("Training Com")
        command = f"bash -c 'cd {self.docker_app_dir}Com && python main.py -train -do_valid -project {self.data_checkpoint.params.project}'"
        docker_utils.run_in_docker("simcom", command)

    def run_complex(self):
        print("Running Com")
        command = f"bash -c 'cd {self.docker_app_dir}Com && python main.py -predict -project {self.data_checkpoint.params.project}'"
        docker_utils.run_in_docker("simcom", command)

    def run_combined(self):
        print("Running SimCom")
        command = f"bash -c 'cd {self.docker_app_dir} && python combination.py -project {self.data_checkpoint.params.project}'"
        docker_utils.run_in_docker("simcom", command)
