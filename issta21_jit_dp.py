from file_utils import DataCheckpoint
import docker_utils

class ISSTA21_JIT_DP:

    def __init__(self):
        self.data_checkpoint = DataCheckpoint()
        self.data_dir = "/opt/data/"
        self.docker_app_dir = "/home/jit-dp/ISSTA21-JIT-DP/"
        self.python = "/root/.pyenv/shims/python"

    def preprocess(self, dataset_name, train_split="train", test_split="test"):
        print("Preprocessing dataset")
        self._get_commits(dataset_name)
        self._preprocess_commits(dataset_name)
        self._extract_features()
        self._generate_input_data(dataset_name, "RQ4_T8", train_split, test_split)
        self._move_input_data()

    def _result_analysis(self, research_question):
        print("Generating results")
        command = f"zsh -c 'cd {self.docker_app_dir}ResultAnalysis && {self.python} cp.py -{research_question}'"
        docker_utils.run_in_docker("lapredict", command)

        command = f"zsh -c 'cd {self.docker_app_dir}ResultAnalysis && {self.python} analysis.py -{research_question}'"
        docker_utils.run_in_docker("lapredict", command)

    def _get_commits(self, dataset_name):
        # only gets commits specified (to database)
        print("Getting commits")
        dataset_filepath = self.data_checkpoint.build_path(f"{dataset_name}/dataset.csv", data_dir=self.data_dir)
        command = f"zsh -c 'cd {self.docker_app_dir}Data_Extraction/git_base/ && {self.python} git_extraction.py \
            -get_commits \
            -project linux \
            -skip \
            -after '1900-01-01' \
            -before '2100-01-01' \
            -load_commit_ids {dataset_filepath}'"
        docker_utils.run_in_docker("lapredict", command)

    def _preprocess_commits(self, dataset_name):
        # will actually preprocess all commits in timerange (to database)
        print("Prepocessing commits")
        dataset_filepath = self.data_checkpoint.build_path(f"{dataset_name}/dataset.csv", data_dir=self.data_dir)
        command = f"zsh -c 'cd {self.docker_app_dir}Data_Extraction/git_base/ && {self.python} git_extraction.py \
            -preprocess_commits \
            -project linux \
            -after '1900-01-01' \
            -before '2100-01-01' \
            -load_commit_ids {dataset_filepath}'"
        docker_utils.run_in_docker("lapredict", command)

    def _extract_features(self):
        # will actually preprocess all commits in timerange (to database)
        print("Extracting k-features")
        command = f"zsh -c 'cd {self.docker_app_dir}Data_Extraction/git_base/ && {self.python} extract_k_feature.py \
            -analyse_project \
            -after '1900-01-01' \
            -before '2100-01-01' \
            -project linux'"
        docker_utils.run_in_docker("lapredict", command)

    def _generate_input_data(self, dataset_name, research_question, train_split="train", test_split="test"):
        # processes commits based on train and test splits (deep and k_feature)
        train_split_path = self.data_checkpoint.build_path(f"{dataset_name}/{train_split}.csv", data_dir=self.data_dir)
        test_split_path = self.data_checkpoint.build_path(f"{dataset_name}/{test_split}.csv", data_dir=self.data_dir)

        print("Generating input data")
        command = f"zsh -c 'cd {self.docker_app_dir}Data_Extraction/git_base/ && {self.python} run.py \
            -{research_question} \
            -project {self.data_checkpoint.params.project} \
            -train-split {train_split} \
            -test-split {test_split} \
            -train-path {train_split_path} \
            -test-path {test_split_path}'"
        docker_utils.run_in_docker("lapredict", command)

    def _move_input_data(self):
        print("Moving generated input data")
        command = f"zsh -c '\
            cp -r {self.docker_app_dir}Data_Extraction/git_base/datasets/* {self.docker_app_dir}DeepJIT/data/ && \
            cp -r {self.docker_app_dir}Data_Extraction/git_base/datasets/* {self.docker_app_dir}CC2Vec/data/ && \
            cp -r {self.docker_app_dir}Data_Extraction/git_base/datasets/* {self.docker_app_dir}JIT_Baseline/data/ \
            '"
        docker_utils.run_in_docker("lapredict", command)