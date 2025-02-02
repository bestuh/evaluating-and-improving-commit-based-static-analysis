import argparse
import pandas as pd
import os

def show(file_path: str):
    df = pd.read_csv(file_path)
    label_counts = df["label"].value_counts()
    num_non_vccs = label_counts[0]
    num_vccs = label_counts[1]
    total = len(df)

    print(f"{file_path}: There are {num_vccs} VCCs and {num_non_vccs} non-VCCs in the dataset ({total} in total). This corresponds to a split of {(100 / total * num_vccs):.2f}%/{(100 / total * num_non_vccs):.2f}%")

    project_counts = df["project"].value_counts()
    for project_name in project_counts.index:
        print(f"> Project {project_name}: {(100 / total * project_counts[project_name]):.2f}%")


def get_file_path(project: str, dataset: str, split: str):
    return f"./../data/{project}/{dataset}/{split}.csv"


if __name__ == "__main__":
    splits = ["dataset", "train", "validation", "test", "test-unbalanced"]
    parser = argparse.ArgumentParser()
    parser.add_argument("-project", type=str, required=True, help="Name of the project to show dataset summary for.")
    parser.add_argument("-dataset", type=str, required=True, help="Name of the dataset to show summary for.")
    parser.add_argument("-split", type=str, choices=splits, help="The split to show the summary for. If not set, will show the summary for all splits.")
    args = parser.parse_args()

    if args.split:
        show(get_file_path(args.project, args.dataset, args.split))
    else:
        for split in splits:
            file_path = get_file_path(args.project, args.dataset, split)
            if os.path.exists(file_path):
                show(file_path)