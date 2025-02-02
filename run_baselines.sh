#!/bin/bash

# adjust settings here
project="chromium"
data_dir_docker="/opt/data/$project/$project-unbalanced-test"
base_path = "/<path>"
data_dir="$base_path/commit-level-vulnerability-detection/data/$project/$project-unbalanced-test"
#################################################################################################

# Copy data (already has to be extracted!) to JIT-Baseline folder
sudo docker exec -it lapredict bash -c "zsh -c 'cp -r $data_dir_docker/lapredict/data/$project /home/jit-dp/ISSTA21-JIT-DP/JIT_Baseline/data/'"

sudo docker exec -it lapredict bash -c "zsh -c 'cd /home/jit-dp/ISSTA21-JIT-DP/JIT_Baseline && /root/.pyenv/shims/python run.py -RQ4_T8 -train_split $data_dir_docker/train.csv -test_split $data_dir_docker/test.csv -project $project'"

# also backup data to the commit-level-vulnerability-detection data dir
cp -r $base_path/commit-level-vulnerability-detection/tools/lapredict/code/JIT_Baseline/result/$project $data_dir/lapredict/baselines

sudo docker exec -it lapredict bash -c "zsh -c 'cp /home/jit-dp/ISSTA21-JIT-DP/JIT_Baseline/data/$project/k_train.csv $data_dir_docker/lapredict/data/$project/k_train.csv'"
sudo docker exec -it lapredict bash -c "zsh -c 'cp /home/jit-dp/ISSTA21-JIT-DP/JIT_Baseline/data/$project/k_test.csv $data_dir_docker/lapredict/data/$project/k_test.csv'"