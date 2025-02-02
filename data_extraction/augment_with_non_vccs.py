import argparse
import pandas as pd
import random
import git
from tqdm import tqdm
import sys
sys.path.append("..")
import file_utils
import time


def get_non_vccs(project: str, repo_path: str, ratio=1.0):
    # get the VCCs
    df = pd.read_csv(f"./vccs/{project}_vccs.csv")
    df["commit_date"] = pd.to_datetime(df["commit_date"])
    # see how many there are
    print(f"Loaded {len(df.index)} VCCs")
    # determine how many non-vccs to get (ratio 1 means same amount, 0.5 means half the amount, 2 means double the amount (of vccs))
    print(f"Ratio is set to {ratio}")
    print(f"Going to get ~{len(df.index) * ratio} non-vccs")

    if df["commit_date"].isnull().any():
        print("Data does not contain commit-dates for all commits.")
        commit_dates = []
        repo = git.Repo(repo_path)
        for commit_sha in tqdm(df["commit_sha"], total=len(df), desc="Retrieving commit-dates"):
            commit = repo.commit(commit_sha)
            date = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(commit.committed_date))
            commit_dates.append(date)
        df["commit_date"] = commit_dates
        df["commit_date"] = pd.to_datetime(df["commit_date"])
        df.to_csv(f"./vccs/{project}_vccs.csv", index=False)

    # get min and max dates => timerange
    print("Oldest commit:", min(df["commit_date"]))
    print("Most recent commit:", max(df["commit_date"]))

    # get X commits from that timerange
    # make a bucket per month (how many vccs do we have per month)
    df["year"] = df["commit_date"].dt.year
    df["month"] = df["commit_date"].dt.month
    by_month = df.groupby(["year", "month"]).agg(vcc_count=("commit_sha", "count")).reset_index()
    # multiply the amount of commits per bucket with the ratio
    by_month["non_vcc_count"] = (by_month["vcc_count"] * ratio).round(0)
    # get that amount of non-vcc commits from the repository within that same year
    non_vccs = []
    for _, bucket in tqdm(by_month.iterrows(), total=len(by_month.index)):
        commit_ids, commit_dates = get_random_commits(int(bucket["year"]), int(bucket["month"]), repo_path, int(bucket["non_vcc_count"]))
        non_vccs = non_vccs + list(zip(commit_ids, commit_dates))
    
    file_path = f"./non_vccs/{project}_non_vccs.csv"
    header = [["commit_sha", "commit_date"]]
    data = header + non_vccs
    print(f"Writing {len(non_vccs)} commits to {file_path}")
    file_utils.write_csv(file_path, data)


def get_random_commits(year: int, month: int, repo_path: str, num_commits: int):
    if num_commits <= 0:
        return [], []
    
    repo = git.Repo(repo_path)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{(month+1):02d}-01" if month < 12 else f"{year+1}-01-01"
    #print(f"Getting {num_commits} random commits from {repo_path} between {start_date} and {end_date}")
    commit_history = list(repo.iter_commits(all=True, since=start_date, until=end_date))
    random_commits = random.sample(commit_history, min(num_commits, len(commit_history)))
    commit_shas = [commit.hexsha for commit in random_commits]
    commit_dates = [commit.committed_datetime for commit in random_commits]
    return commit_shas, commit_dates


def extend_split(project: str, repo_path: str, ratio: float, dataset_name: str, split: str, update_dataset: bool):
    file_path = f"./../data/{project}/{dataset_name}/{split}.csv"
    df_original = pd.read_csv(file_path)

    df = df_original.copy()

    if df["commit_date"].isnull().any():
        print("Data does not contain commit-dates for all commits.")
        commit_dates = []
        repo = git.Repo(repo_path)
        for commit_sha in tqdm(df["commit_sha"], total=len(df), desc="Retrieving commit-dates"):
            commit = repo.commit(commit_sha)
            date = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(commit.committed_date))
            commit_dates.append(date)
        df["commit_date"] = commit_dates
        df["commit_date"] = pd.to_datetime(df["commit_date"])
        df.to_csv(file_path, index=False)

    df["commit_date"] = df["commit_date"].map(lambda date_string: date_string.split(" ")[0])
    df["commit_date"] = pd.to_datetime(df["commit_date"], errors="raise")

    dummy_row = pd.DataFrame([{
        "commit_sha": "dummy", 
        "commit_date": pd.to_datetime("2010-09-10 22:46:52"), 
        "project": "chromium", 
        "sources": "dummy",
        "label": 0
    }])
    df = pd.concat([df, dummy_row], ignore_index=True)

    num_non_vccs, num_vccs, total = get_stats(df)
    num_to_add = int(num_vccs * ratio - num_non_vccs - 1)
    print(f"Currently there are {num_vccs} VCCs and {num_non_vccs} non-VCCs in the dataset. This corresponds to a split of {(100 / total * num_vccs):.2f}%/{(100 / total * num_non_vccs):.2f}%")
    print(f"The wanted ratio is {(100 - (ratio * 10)):.2f}%/{(ratio * 10):.2f}%. Hence augmenting with ~{num_to_add} non-VCCs.")

    if num_to_add == 0:
        exit(0)
    elif num_to_add < 0:
        print("ERROR: Cannot add a negative amount of non-vccs.")
        exit(1)

    df["year"] = df["commit_date"].dt.year
    df["month"] = df["commit_date"].dt.month

    by_month = df.groupby(["year", "month", "label"]).size().unstack(fill_value=0).reset_index()
    by_month.columns = ["year", "month", "non_vcc_count", "vcc_count"]
    # multiply the amount of commits per bucket with the ratio
    by_month["non_vcc_count_add"] = (by_month["vcc_count"] * ratio - by_month["non_vcc_count"]).round(0)
    # get that amount of non-vcc commits from the repository within that same year
    new_ids = []
    new_dates = []
    for _, bucket in tqdm(by_month.iterrows(), total=len(by_month.index)):
        commit_ids, commit_dates = get_random_commits(int(bucket["year"]), int(bucket["month"]), repo_path, int(bucket["non_vcc_count_add"]))
        new_ids += commit_ids
        new_dates += commit_dates
        new_non_vccs = pd.DataFrame({
            "commit_sha": commit_ids,
            "commit_date": commit_dates,
            "label": [0] * len(commit_ids),
            "project": project,
            "sources": "augmented"
        })
        merged_df = df_original.merge(new_non_vccs, on="commit_sha", how="outer", indicator=True)
        merged_df["label"] = merged_df["label_x"].combine_first(merged_df["label_y"])
        merged_df["commit_date"] = merged_df["commit_date_x"].combine_first(merged_df["commit_date_y"])
        merged_df["project"] = merged_df["project_x"].combine_first(merged_df["project_y"])
        merged_df["sources"] = merged_df["sources_x"].combine_first(merged_df["sources_y"])
        df_original = merged_df[["commit_sha", "commit_date", "project", "label", "sources"]]
        df_original.to_csv(file_path, index=False)
    
    if update_dataset is True:
        full_dataset_path = f"./../data/{project}/{dataset_name}/dataset.csv"
        df_full_dataset = pd.read_csv(full_dataset_path)
        new_commits = pd.DataFrame({
            "commit_sha": new_ids,
            "commit_date": new_dates,
            "label": [0] * len(new_ids),
            "project": project,
            "sources": "augmented"
        })
        merged_df = df_full_dataset.merge(new_commits, on="commit_sha", how="outer", indicator=True)
        merged_df["label"] = merged_df["label_x"].combine_first(merged_df["label_y"])
        merged_df["commit_date"] = merged_df["commit_date_x"].combine_first(merged_df["commit_date_y"])
        merged_df["project"] = merged_df["project_x"].combine_first(merged_df["project_y"])
        merged_df["sources"] = merged_df["sources_x"].combine_first(merged_df["sources_y"])
        df_full_dataset = merged_df[["commit_sha", "commit_date", "project", "label", "sources"]]
        df_full_dataset.to_csv(full_dataset_path, index=False)
        print(f"Added {len(new_ids)} commits to {full_dataset_path}")

    print(f"Added {len(df_original) - total} commits to {file_path}")
    num_non_vccs, num_vccs, total = get_stats(df_original)
    print(f"Now there are {num_vccs} VCCs and {num_non_vccs} non-VCCs in the dataset. This corresponds to a split of {(100 / total * num_vccs):.2f}%/{(100 / total * num_non_vccs):.2f}%")


def get_stats(df: pd.DataFrame):
    grouped = df.groupby("label").agg(
        count=("label", "count")
    )

    try:
        num_non_vccs = grouped.loc[0, "count"]
    except KeyError:
        num_non_vccs = 0

    try:
        num_vccs = grouped.loc[1, "count"]
    except KeyError:
        num_vccs = 0

    return num_non_vccs, num_vccs, (num_non_vccs + num_vccs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-project", type=str, help="Name of the project (cve_config_code) to extract non-VCCs for.")
    parser.add_argument("-repo", type=str, help="Path to the repository that non-VCCs should be sampled from.")
    parser.add_argument("-ratio", type=float, default=1.0, help="How many non-VCCs to get. Ratio of 1.0 means same amount, 0.5 means half the amount of VCCs, 2 means double the amount of of VCCs, ...")
    
    parser.add_argument("-split", type=str, choices=["train", "validation", "test", "dataset"], help="The split to augment with further non-VCCs until specified ratio is met.")
    parser.add_argument("-dataset", type=str, help="Name of the dataset to augment split for. Required when -split is used.")
    parser.add_argument("-update-dataset", action="store_true", help="When enabled, the dataset.csv will be updated to contain the newly augmented commits.")
    
    args = parser.parse_args()

    if not args.split:
        get_non_vccs(args.project, args.repo, args.ratio)
    else:
        if args.dataset is None:
            print(f"ERROR: Argument -dataset is required when using -split")
            exit(1)
        extend_split(args.project, args.repo, args.ratio, args.dataset, args.split, args.update_dataset)