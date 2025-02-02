#!/bin/bash

# adjust settings here
project="chromium"
data_dir="/opt/data/$project/linux-unbalanced"
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

# Copy data (already has to be extracted!) to CC2Vec folder
sudo docker exec -it lapredict bash -c "zsh -c 'cp -r $data_dir/lapredict/data/$project /home/jit-dp/ISSTA21-JIT-DP/CC2Vec/data/'"

# Training CC2Vec
sudo docker exec lapredict bash -c "zsh -c 'cd /home/jit-dp/ISSTA21-JIT-DP/CC2Vec && /root/.pyenv/shims/python run.py -RQ4_T8 -train_cc2vec -project $project'"
# Generating CC2Vec representations
sudo docker exec lapredict bash -c "zsh -c 'cd /home/jit-dp/ISSTA21-JIT-DP/CC2Vec && /root/.pyenv/shims/python run.py -RQ4_T8 -pred_cc2vec -project $project'"
# Training CC2Vec classifier (DeepJIT)
sudo docker exec lapredict bash -c "zsh -c 'cd /home/jit-dp/ISSTA21-JIT-DP/CC2Vec && /root/.pyenv/shims/python run.py -RQ4_T8 -train_deepjit -project $project $raw'"
# Predicting CC2Vec classifier (DeepJIT)
sudo docker exec lapredict bash -c "zsh -c 'cd /home/jit-dp/ISSTA21-JIT-DP/CC2Vec && /root/.pyenv/shims/python run.py -RQ4_T8 -pred_deepjit -project $project $raw'"

# also backup data to the commit-level-vulnerability-detection data dir
sudo docker exec -it lapredict bash -c "zsh -c 'cp /home/jit-dp/ISSTA21-JIT-DP/CC2Vec/snapshot/$project/ftr/epoch_50.pt $data_dir/lapredict/cc2vec/model_cc2vec.pt'"
sudo docker exec -it lapredict bash -c "zsh -c 'cp /home/jit-dp/ISSTA21-JIT-DP/CC2Vec/snapshot/$project/$model_dir/epoch_50.pt $data_dir/lapredict/cc2vec/model_deepjit$suffix.pt'"
sudo docker exec -it lapredict bash -c "zsh -c 'cp /home/jit-dp/ISSTA21-JIT-DP/CC2Vec/snapshot/$project/$model_dir/epoch_50.pt.result $data_dir/lapredict/cc2vec/results$suffix.csv'"
