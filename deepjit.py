from issta21_jit_dp import ISSTA21_JIT_DP
import docker_utils

class DeepJIT(ISSTA21_JIT_DP):

    def train(self, research_question="RQ4_T8", train_split="train"):
        print("Training DeepJIT")
        command = f"zsh -c 'cd {self.docker_app_dir}DeepJIT && {self.python} run.py -{research_question} -train_deepjit -epoch 2 -train-split {train_split} -project {self.data_checkpoint.params.project}'"
        docker_utils.run_in_docker("lapredict", command)

    def predict(self, research_question="RQ4_T8", test_split="test"):
        print("Predicting DeepJIT")
        command = f"zsh -c 'cd {self.docker_app_dir}DeepJIT && {self.python} run.py -{research_question} -pred_deepjit -epoch 2 -test-split {test_split} -project {self.data_checkpoint.params.project}'"
        docker_utils.run_in_docker("lapredict", command)
        self._result_analysis(research_question)