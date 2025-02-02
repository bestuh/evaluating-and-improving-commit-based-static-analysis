import argparse


def read_params():
    parser = argparse.ArgumentParser()

    parser.add_argument("-project", type=str, required=True, help="Name of the project (GitHub repository name) to use.")
    parser.add_argument("-dataset", type=str, required=True, help="Name of the dataset to use.")
    parser.add_argument("-model", type=str, required=True, choices=["vccrosshair", "lr-jit", "dbn-jit", "lapredict", "deepjit", "cc2vec", "simcom"], help="Name of the model you want to run.")
    parser.add_argument("-test-split", type=str, default="test", help="Name of the split to use for testing the model.")

    return parser.parse_args()