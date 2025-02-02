from git import Repo
import re
import pandas as pd
from tqdm import tqdm
import argparse


def extract_sizes(project: str, dataset_name: str):
    dataset = pd.read_csv(f"../data/{project}/{dataset_name}/test.csv")

    commit_shas = []
    additions = []
    deletions = []
    changes = []
    for _, row in tqdm(dataset.iterrows(), total=len(dataset)):
        adds, dels = extract_size(row["commit_sha"], "../repositories/" + row["project"])
        commit_shas.append(row["commit_sha"])
        additions.append(adds)
        deletions.append(dels)
        changes.append(adds + dels)

    sizes = pd.DataFrame({
        "commit_sha": commit_shas,
        "lines_added": additions,
        "lines_deleted": deletions,
        "lines_added_or_deleted": changes
    })
    sizes.to_csv(f"../data/{project}/{dataset_name}/sizes.csv", index=False)


def extract_size(commit_id, repository_path):
    repo = Repo(repository_path)
    commit = repo.commit(commit_id)
    first_parent = commit.parents[0]
    diff = first_parent.diff(commit, create_patch=True, unified=0)
    
    adds = 0
    dels = 0
    for change in diff:
        try:
            patch = change.diff.decode("utf-8")
        except UnicodeDecodeError:
            patch = change.diff.decode("latin-1")

        lines = patch.split("\n")
        for line in lines:
            if line.startswith("+"):
                adds += 1
            elif line.startswith("-"):
                dels += 1

    return adds, dels


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-project", type=str)
    parser.add_argument("-dataset", type=str)
    
    args = parser.parse_args()

    extract_sizes(args.project, args.dataset)