from issta21_jit_dp import ISSTA21_JIT_DP
import docker_utils

class LAPredict(ISSTA21_JIT_DP):

    def run(self, dataset_name, research_question="RQ4_T8", train_split="train", test_split="test"):
        print("Running LAPredict")
        command = f"zsh -c 'cd {self.docker_app_dir}JIT_Baseline && {self.python} run.py \
            -{research_question} \
            -project {self.data_checkpoint.params.project} \
            -train_split {self.data_dir}{self.data_checkpoint.params.project}/{dataset_name}/{train_split}.csv \
            -test_split {self.data_dir}{self.data_checkpoint.params.project}/{dataset_name}/{test_split}.csv'"
        docker_utils.run_in_docker("lapredict", command)

        self._result_analysis(research_question)
