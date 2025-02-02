#!/bin/bash

# adjust settings here
project="chromium"
data_dir_docker="/opt/data/$project/$project-unbalanced"
base_path = "/<path>"
data_dir="$base_path/commit-level-vulnerability-detection/data/$project/$project-unbalanced"
############################################################################################

# get commits from file and store them in mongodb
sudo docker exec -it lapredict bash -c "zsh -c 'cd /home/jit-dp/ISSTA21-JIT-DP/Data_Extraction/git_base/ && /root/.pyenv/shims/python git_extraction.py -get_commits -project $project -skip -after \"1900-01-01\" -before \"2100-01-01\" -load_commit_ids $data_dir_docker/dataset.csv'"
# preprocesses all commits in the database of the respective project
sudo docker exec -it lapredict bash -c "zsh -c 'cd /home/jit-dp/ISSTA21-JIT-DP/Data_Extraction/git_base/ && /root/.pyenv/shims/python git_extraction.py -preprocess_commits -project $project -after \"1900-01-01\" -before \"2100-01-01\" -load_commit_ids $data_dir_docker/dataset.csv'"
# extracts features for all commits in the database of the respective project
sudo docker exec -it lapredict bash -c "zsh -c 'cd /home/jit-dp/ISSTA21-JIT-DP/Data_Extraction/git_base/ && /root/.pyenv/shims/python extract_k_feature.py -analyse_project -after \"1900-01-01\" -before \"2100-01-01\" -project $project'"
# processes commits based on specified train and test splits (deep and k_feature)
sudo docker exec -it lapredict bash -c "zsh -c 'cd /home/jit-dp/ISSTA21-JIT-DP/Data_Extraction/git_base/ && /root/.pyenv/shims/python run.py -RQ4_T8 -train-split train -test-split test -train-path $data_dir_docker/train.csv -test-path $data_dir_docker/test.csv -project $project'"
# move generated input (inside of lapredict)
sudo docker exec -it lapredict bash -c "zsh -c 'cp -r /home/jit-dp/ISSTA21-JIT-DP/Data_Extraction/git_base/datasets/* /home/jit-dp/ISSTA21-JIT-DP/DeepJIT/data/ && cp -r /home/jit-dp/ISSTA21-JIT-DP/Data_Extraction/git_base/datasets/* /home/jit-dp/ISSTA21-JIT-DP/CC2Vec/data/ && cp -r /home/jit-dp/ISSTA21-JIT-DP/Data_Extraction/git_base/datasets/* /home/jit-dp/ISSTA21-JIT-DP/JIT_Baseline/data/'"

# move data to commit-level-vulnerability-detection dir
sudo docker exec -it lapredict bash -c "zsh -c 'cp -r /home/jit-dp/ISSTA21-JIT-DP/Data_Extraction/git_base/datasets/* $data_dir_docker/lapredict/data/'"

sudo rm -rf $data_dir/lapredict/data/gerrit $data_dir/lapredict/data/go $data_dir/lapredict/data/jdt $data_dir/lapredict/data/openstack $data_dir/lapredict/data/platform $data_dir/lapredict/data/qt $data_dir/lapredict/data/mixed
sudo rm -rf $data_dir/lapredict/data/linux $data_dir/lapredict/data/ffmpeg