import argparse
import pandas as pd
from sklearn.model_selection import train_test_split
import sys
sys.path.append("..")
import file_utils

def create_dataset(project: str, dataset_name: str, vcc_file: str, non_vcc_file: str, validation_size: float, test_size: float):
    dataset_path = f"./../data/{project}/{dataset_name}/"

    # load VCCs and non-VCCs
    df_vcc = pd.read_csv(vcc_file)
    print(f"Loaded {len(df_vcc)} VCCs from \"{vcc_file}\"")
    df_safe = pd.read_csv(non_vcc_file)
    print(f"Loaded {len(df_safe)} non-VCCs from \"{non_vcc_file}\"")

    # remove non-VCCs that are acutally VCCs
    before = len(df_safe["commit_sha"])
    df_safe = df_safe.merge(df_vcc[["commit_sha"]], on=["commit_sha"], how="left", indicator=True).query("_merge == 'left_only'").drop(columns="_merge")
    print(f"Removed {before - len(df_safe)} commits from the non-VCCs since they are contained in the VCCs")

    # add labels
    df_vcc["label"] = [1] * len(df_vcc)
    df_safe["label"] = [0] * len(df_safe)
    print(f"Dataset: {len(df_vcc)} VCCs, {len(df_safe)} non-VCCs, {len(df_vcc) + len(df_safe)} total")

    # combine VCCs and non-VCCs
    df = pd.concat([df_vcc, df_safe], ignore_index=True)
    df.sort_values(by=["commit_date"], inplace=True, ascending=False)

    # save the full dataset
    save_to = f"{dataset_path}dataset.csv"
    file_utils.create_directory(save_to)
    df.to_csv(save_to, index=False)

    generate_splits(dataset_path, validation_size, test_size)


def generate_splits(dataset_path, validation_size, test_size):
    df_dataset = pd.read_csv(f"{dataset_path}dataset.csv")
    df_dataset.sort_values(by=["commit_date"], inplace=True, ascending=False)

    print(f"Generating train ({(1.0 - validation_size - test_size) * 100}%), validation ({validation_size * 100}%) and test ({test_size * 100}%) splits:")
    
    # generate test split by simply taking the first rows (ordered by date), so test split contains most recent commits
    df_test = df_dataset.head(int(len(df_dataset)*(test_size)))
    df_dataset = pd.concat([df_dataset, df_test]).drop_duplicates(keep=False) # remove extracted test split from dataframe
    
    df_train, df_validation = train_test_split(df_dataset, test_size=1 / (1.0 - test_size) * validation_size, shuffle=True) # split the remaining data into train and validation set
    
    print(f"> Train: {len(df_train)} samples")
    print(f"> Validation: {len(df_validation)} samples")
    print(f"> Test: {len(df_test)} samples")

    df_train.to_csv(f"{dataset_path}train.csv", index=False)
    df_validation.to_csv(f"{dataset_path}validation.csv", index=False)
    df_test.to_csv(f"{dataset_path}test.csv", index=False)


def fix_full_dataset(project: str, dataset_name: str):
    full_dataset_path = get_dataset_path(project, dataset_name, "dataset")
    df_full_dataset = pd.read_csv(full_dataset_path)
    print(f"Updating {full_dataset_path}")
    print(f"Currently contains {len(df_full_dataset)} commits")

    df_train = pd.read_csv(get_dataset_path(project, dataset_name, "train"))
    print(f"{len(df_train)} commits in train.csv")
    df_val = pd.read_csv(get_dataset_path(project, dataset_name, "validation"))
    print(f"{len(df_val)} commits in validation.csv")
    df_test = pd.read_csv(get_dataset_path(project, dataset_name, "test"))
    print(f"{len(df_test)} commits in test.csv")

    new_full_dataset = pd.concat([df_train, df_val, df_test], axis=0)
    new_full_dataset.to_csv(full_dataset_path, index=False)
    print(f"Updated dataset now contains {len(new_full_dataset)} commits")


def mix_datasets(mix: str, dataset_name: str):
    mix_projects = mix.split(",")

    train_data = []
    validation_data = []
    test_data = []
    sizes_data = []
    code_slices_data = []
    for project_dataset in mix_projects:
        project = project_dataset.split("/")[0]
        dataset = project_dataset.split("/")[1]
        print(f"Reading dataset {project_dataset}...")
        df_train = pd.read_csv(get_dataset_path(project, dataset, "train"))
        df_train["project"] = [project] * len(df_train)
        train_data.append(df_train)

        df_val = pd.read_csv(get_dataset_path(project, dataset, "validation"))
        df_val["project"] = [project] * len(df_val)
        validation_data.append(df_val)

        df_test = pd.read_csv(get_dataset_path(project, dataset, "test"))
        df_test["project"] = [project] * len(df_test)
        test_data.append(df_test)

        df_sizes = pd.read_csv(get_dataset_path(project, dataset, "sizes"))
        df_sizes["project"] = [project] * len(df_sizes)
        sizes_data.append(df_sizes)

        df_code_slices = pd.read_csv(get_dataset_path(project, dataset, "code_slices"))
        code_slices_data.append(df_code_slices)
    
    project = "mixed"
    full_dataset_path = f"./../data/{project}/{dataset_name}/dataset.csv"
    file_utils.create_directory(full_dataset_path)

    new_train = pd.concat(train_data, axis=0)
    new_train.to_csv(get_dataset_path(project, dataset_name, "train"), index=False)
    print(f"Created new mixed train split with {len(new_train)} commits")

    new_val = pd.concat(validation_data, axis=0)
    new_val.to_csv(get_dataset_path(project, dataset_name, "validation"), index=False)
    print(f"Created new mixed validation split with {len(new_val)} commits")

    new_test = pd.concat(test_data, axis=0)
    new_test.to_csv(get_dataset_path(project, dataset_name, "test"), index=False)
    print(f"Created new mixed test split with {len(new_test)} commits")

    new_full = pd.concat([new_train, new_val, new_test], axis=0)
    new_full.to_csv(full_dataset_path, index=False)
    print(f"New dataset contains {len(new_full)} commits in total")

    new_sizes = pd.concat(sizes_data, axis=0)
    new_sizes.to_csv(get_dataset_path(project, dataset_name, "sizes"), index=False)

    new_code_slices = pd.concat(code_slices_data, axis=0)
    new_code_slices.to_csv(get_dataset_path(project, dataset_name, "code_slices"), index=False)


def get_dataset_path(project: str, dataset_name: str, split: str):
    return f"./../data/{project}/{dataset_name}/{split}.csv"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-project", type=str, help="Name of the project to create dataset for.")
    parser.add_argument("-dataset-name", type=str, help="Name of the dataset to be created.")
    parser.add_argument("-vcc-file", type=str, help="Path to the file that contains VCCs.")
    parser.add_argument("-non-vcc-file", type=str, help="Path to the file that contains non-VCCs.")
    parser.add_argument("-validation-size", type=float, default=0.15, help="Percentage of samples to use for the validation-set. A value between 0 (0%) and 1 (100%).")
    parser.add_argument("-test-size", type=float, default=0.15, help="Percentage of samples to use for the test-set. A value between 0 (0%) and 1 (100%).")
    
    parser.add_argument("-fix-full-dataset", action="store_true", help="When enabled will read all available splits (train, validation, test) and update the full dataset.csv file accordingly.")
    
    parser.add_argument("-mix", type=str, help="A comma-separated list of project/dataset-name entries which will be joined into a new dataset.")
    
    args = parser.parse_args()

    if args.fix_full_dataset is True:
        fix_full_dataset(args.project, args.dataset_name)
    elif args.mix is not None:
        mix_datasets(args.mix, args.dataset_name)
    else:
        create_dataset(args.project, args.dataset_name, args.vcc_file, args.non_vcc_file, args.validation_size, args.test_size)