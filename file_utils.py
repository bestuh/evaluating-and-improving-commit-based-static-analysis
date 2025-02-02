from arguments import read_params
import numpy as np
import json
import csv
import pickle
import os
import glob


def create_directory(filepath):
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory)

def file_exists(filepath):
    return os.path.exists(filepath)

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)
    

def write_csv(filepath, data):
    create_directory(filepath)
    if type(data) is list and type(data[0]) is not list:
        data = [[item] for item in data]
    with open(filepath, "w+", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(data)


def read_csv(filepath):
    with open(filepath, "r") as file:
        reader = csv.reader(file)
        rows = list(reader)
        if len(rows[0]) == 1:
            return [row[0] for row in rows]
        else:
            return rows


def write_json(filepath, data):
    create_directory(filepath)
    with open(filepath, "w+") as file:
        json.dump(data, file, cls=NumpyEncoder, indent=2)


def write_pickle(filepath, data):
    create_directory(filepath)
    with open(filepath, "wb+") as file:
        pickle.dump(data, file)


def read_pickle(filepath):
    with open(filepath, "rb") as file:
        return pickle.load(file)


def get_newest(path):
    list_of_files_and_folders = glob.glob(path)
    latest_file = max(list_of_files_and_folders, key=os.path.getctime)
    return os.path.basename(os.path.normpath(latest_file))

class DataCheckpoint():

    def __init__(self) -> None:
        self.params = read_params()
        self.data_dir = f"data/{self.params.project}/"
        self.repo_dir = f"repositories/{self.params.project}/"

    def build_path(self, filename, data_dir=None):
        if data_dir is None:
            data_dir = self.data_dir
        elif data_dir.endswith("data/"):
            data_dir = f"{data_dir}{self.params.project}/"
        return data_dir + filename
        
    def create(self, filename, data):
        path = self.build_path(filename)
        print("Creating checkpoint", path)
        if filename.endswith(".csv"):
            write_csv(path, data)
        elif filename.endswith(".pkl"):
            write_pickle(path, data)
        else:
            write_json(path, data)

    def get(self, filename):
        path = self.build_path(filename)
        print("Loading checkpoint", path)
        if filename.endswith(".csv"):
            return read_csv(path)
        elif filename.endswith(".pkl"):
            return read_pickle(path)

    def exists(self, filename) -> bool:
        return file_exists(self.build_path(filename))