from issta21_jit_dp import ISSTA21_JIT_DP
import docker_utils

class CC2Vec(ISSTA21_JIT_DP):

    def train_representations(self, research_question="RQ4_T8"):
        print("Training CC2Vec representations")
        command = f"zsh -c 'cd {self.docker_app_dir}CC2Vec && {self.python} run.py -{research_question} -train_cc2vec -project {self.data_checkpoint.params.project}'"
        docker_utils.run_in_docker("lapredict", command)

    def generate_representations(self, research_question="RQ4_T8"):
        print("Generating CC2Vec representations")
        command = f"zsh -c 'cd {self.docker_app_dir}CC2Vec && {self.python} run.py -{research_question} -pred_cc2vec -project {self.data_checkpoint.params.project}'"
        docker_utils.run_in_docker("lapredict", command)

    def train_classifier(self, research_question="RQ4_T8"):
        print("Training CC2Vec classifier (+ DeepJIT)")
        command = f"zsh -c 'cd {self.docker_app_dir}CC2Vec && {self.python} run.py -{research_question} -train_deepjit -project {self.data_checkpoint.params.project}'"
        docker_utils.run_in_docker("lapredict", command)

    def predict(self, research_question="RQ4_T8"):
        print("Predicting CC2Vec classifier (+ DeepJIT)")
        command = f"zsh -c 'cd {self.docker_app_dir}CC2Vec && {self.python} run.py -{research_question} -pred_deepjit -project {self.data_checkpoint.params.project}'"
        docker_utils.run_in_docker("lapredict", command)
        self._result_analysis(research_question)