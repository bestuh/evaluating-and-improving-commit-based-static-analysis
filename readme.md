# Evaluating and improving code-change representations for commit-level vulnerability detection

## Setup
1. Create a new virtual environment:
    ```bash
    python3 -m venv venv
    ```
2. Activate it:
    ```bash
    source venv/bin/activate
    ```
3. Install packages:
    ```bash
    pip install -r requirements.txt
    ```
4. [Download data](https://figshare.com/articles/dataset/Commit-level_vulnerability_detection_-_datasets_and_models/24494980) and add it to a folder called `data` in the root directory of the project.

## Tools

### MySQL database
To start up a mysql database, please take a look at the `database` folder.

### VCCrosshair
To run [VCCrosshair](https://github.com/jp-wagner/vccrosshair/tree/master) use `run_models.py`.

### LR-JIT
To setup [LR-JIT](https://ieeexplore.ieee.org/document/6341763), please take a look at the `tools/lapredict` folder.
Run `run_extract_lapredict_data.sh` to generate input data and then run the model via `run_baselines.sh`. Alternatively take a look at `run_models.py`.

### Deeper/DBN-JIT
To setup [Deeper/DBN-JIT](https://ieeexplore.ieee.org/document/7272910), please take a look at the `tools/lapredict` folder.
Run `run_extract_lapredict_data.sh` to generate input data and then run the model via `run_baselines.sh`. Alternatively take a look at `run_models.py`.

### LAPredict
To setup [LAPredict](https://dl.acm.org/doi/pdf/10.1145/3460319.3464819), please take a look at the `tools/lapredict` folder.
Run `run_extract_lapredict_data.sh` to generate input data and then run the model via `run_baselines.sh`. Alternatively take a look at `run_models.py`.

### DeepJIT
To setup [DeepJIT](https://posl.ait.kyushu-u.ac.jp/~kamei/publications/Thong_MSR2019.pdf), please take a look at the `tools/lapredict` folder.
Run `run_extract_lapredict_data.sh` to generate input data and then run the model via `run_deepjit.sh`. Alternatively take a look at `run_models.py`.

### CC2Vec
To setup [CC2Vec](https://arxiv.org/pdf/2003.05620.pdf), please take a look at the `tools/lapredict` folder.
Run `run_extract_lapredict_data.sh` to generate input data and then run the model via `run_cc2vec.sh`. Alternatively take a look at `run_models.py`.

### SimCom
To setup [SimCom](https://dl.acm.org/doi/10.1145/3524610.3527910), please take a look at the `tools/simcom` folder.
Run `run_extract_lapredict_data.sh` to generate input data and then run the model via `run_simcom.sh`. Alternatively take a look at `run_models.py`.

### New proposed model
Refer to the `model` directory.

## Acknowledgements
This repository is partially based on code from the following repositories:
- [VCCrosshair](https://github.com/nikalexo/vcc-mapper): Model implementation for the VCCrosshair model.
- [ISSTA21-JIT-DP](https://github.com/ZZR0/ISSTA21-JIT-DP): The data-extraction pipeline was adjusted and used to extract commit-data for the utilized datasets. Also, contained model implementations for LAPredict, LR-JIT, DBN-JIT, DeepJIT and CC2Vec were reused.
- [SimCom](https://github.com/soarsmu/SimCom_JIT): Model implementation for the SimCom model.
- [Studying the Effect of Data in Commit-Based Static Analysis](https://git.rwth-aachen.de/rawel.ahmad/commit-analysis-ml): Data for dataset creation.
  

## License
Distributed under the GPLv3 License. See `LICENSE` for more information.
