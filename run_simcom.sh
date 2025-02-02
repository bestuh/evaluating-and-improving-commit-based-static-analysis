#!/bin/bash

# adjust settings here
project="chromium"
dataset="$project-unbalanced"
data_dir="/opt/data/$project/$project-unbalanced"
#################################################

# Clear data directory (before running)
rm -rf ~/commit-level-vulnerability-detection/tools/simcom/code/data/hand_crafted_features/$project
rm -rf ~/commit-level-vulnerability-detection/tools/simcom/code/data/commit_cotents/processed_data/$project

# Generate data (or copy if it already exists)
source venv/bin/activate
python3 run_models.py -project $project -dataset $dataset -model simcom

# Simple
sudo docker exec simcom bash -c "bash -c 'cd /opt/simcom/Sim && python sim_model.py -project $project'"
# Complex
sudo docker exec simcom bash -c "bash -c 'cd /opt/simcom/Com && python main.py -train -do_valid -project $project'"
sudo docker exec simcom bash -c "bash -c 'cd /opt/simcom/Com && python main.py -predict -project $project'"
# Combined
sudo docker exec simcom bash -c "bash -c 'cd /opt/simcom/ && python combination.py -project $project'"

# also backup data to the commit-level-vulnerability-detection data dir
sudo docker exec -it simcom bash -c "cp /opt/simcom/Sim/pred_scores/test_sim_$project.csv $data_dir/simcom/simple/results.csv"
sudo docker exec -it simcom bash -c "cp /opt/simcom/Com/pred_scores/test_com_$project.csv $data_dir/simcom/complex/results.csv"
sudo docker exec -it simcom bash -c "cp /opt/simcom/Com/model/$project/best_model.pt $data_dir/simcom/complex/model.pt"
sudo docker exec -it simcom bash -c "cp /opt/simcom/results_$project.csv $data_dir/simcom/results.csv"