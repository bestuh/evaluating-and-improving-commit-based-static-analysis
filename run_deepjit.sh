#!/bin/bash

# adjust settings here
project="chromium"
data_dir="/opt/data/$project/$project-unbalanced"
raw="-raw" # set to "-raw" to run the DeepJIT-Paper version, set to "" to run the DeepJIT-GitHub version
########################################################################################################

if [ "$raw" == "-raw" ]; then
	model_dir="raw"
else
	model_dir="model"
fi

suffix=""
if [ "$raw" == "-raw" ]; then
	suffix="_raw"
fi

# Copy data (already has to be extracted!) to deepjit folder
sudo docker exec -it lapredict bash -c "zsh -c 'cp -r $data_dir/lapredict/data/$project /home/jit-dp/ISSTA21-JIT-DP/DeepJIT/data/'"

sudo docker exec -it lapredict bash -c "zsh -c 'cd /home/jit-dp/ISSTA21-JIT-DP/DeepJIT && /root/.pyenv/shims/python run.py -RQ4_T8 -train_deepjit -train-split train -project $project $raw'"
sudo docker exec -it lapredict bash -c "zsh -c 'cd /home/jit-dp/ISSTA21-JIT-DP/DeepJIT && /root/.pyenv/shims/python run.py -RQ4_T8 -pred_deepjit -test-split test -project $project $raw'"

# also backup data to the commit-level-vulnerability-detection data dir
sudo docker exec -it lapredict bash -c "zsh -c 'cp /home/jit-dp/ISSTA21-JIT-DP/DeepJIT/snapshot/$project/$model_dir/epoch_50.pt $data_dir/lapredict/deepjit/model$suffix.pt'"
sudo docker exec -it lapredict bash -c "zsh -c 'cp /home/jit-dp/ISSTA21-JIT-DP/DeepJIT/snapshot/$project/$model_dir/epoch_50.pt.result $data_dir/lapredict/deepjit/results$suffix.csv'"
