import warnings
warnings.simplefilter("ignore", UserWarning)

import os
import argparse

import pandas as pd


parser = argparse.ArgumentParser()

parser.add_argument('-split_data', action='store_true', default=False)
parser.add_argument('-split_size', action='store_true', default=False)
parser.add_argument('-split_old', action='store_true', default=False)
parser.add_argument('-project', type=str,
                    default='qt')
parser.add_argument('-data', type=str,
                    default='k')
parser.add_argument('-train', type=int, default=10000)
parser.add_argument('-test', type=int, default=2000)
parser.add_argument('-train_split', type=str, default=None)
parser.add_argument('-test_split', type=str, default=None)


def split_list(args, data, size=False):
    if args.train_split is not None and args.test_split is not None:
        train = pd.read_csv(args.train_split)
        test = pd.read_csv(args.test_split)
        train_ids = train.iloc[:, 0].values
        test_ids = test.iloc[:, 0].values
        print("train_ids:", len(train_ids))
        print("test_ids:", len(test_ids))
        train_features, test_features = [], []
        for _, sample in data.iterrows():
            if sample["_id"] in train_ids:
                train_features.append(sample)
            if sample["_id"] in test_ids:
                test_features.append(sample)
        return pd.DataFrame(train_features, columns=data.columns), pd.DataFrame(test_features, columns=data.columns)
    
    idx1 = args.train + args.test
    idx2 = args.test
    idx = int(len(data)*0.8)

    if size:
        return data[-idx1:-idx2], data[-idx2:]
    return data[:idx], data[idx:]

def split_size(args):
    for size in ['10k', '20k', '30k', '40k', '50k']:
        k_feature = pd.read_csv("data/{}/{}/{}_{}_feature.csv".format(args.project, size, args.project, args.data))

        if size == '50k':
            args.train = 50000
        elif size == '40k':
            args.train = 40000
        elif size == '30k':
            args.train = 30000
        elif size == '20k':
            args.train = 20000
        elif size == '10k':
            args.train = 10000

        train, test = split_list(args, k_feature, size=True)
        train.to_csv('data/{}/{}/{}_train.csv'.format(args.project, size, args.data), index=False)
        test.to_csv('data/{}/{}/{}_test.csv'.format(args.project, size, args.data), index=False)


def split_data(args):
    k_feature = pd.read_csv("data/{}/{}_{}_feature.csv".format(args.project, args.project, args.data))
    train, test = split_list(args, k_feature)

    train.to_csv('data/{}/{}_train.csv'.format(args.project, args.data), index=False)
    test.to_csv('data/{}/{}_test.csv'.format(args.project, args.data), index=False)

def split_old(args):
    k_feature = pd.read_csv("data/{}/old/{}_{}_feature.csv".format(args.project, args.project, args.data))
    train, test = split_list(args, k_feature)

    train.to_csv('data/{}/old/{}_train.csv'.format(args.project, args.data), index=False)
    test.to_csv('data/{}/old/{}_test.csv'.format(args.project, args.data), index=False)

def sp():
    projects = ['qt', 'openstack', 'jdt', 'platform', 'gerrit', 'go']
    cmd = 'python prepare_data.py -data k -split_data -project {}'

    for project in projects:
        print(cmd.format(project))
        os.system(cmd.format(project))


if __name__ == "__main__":
    args = parser.parse_args()

    if args.split_data:
        split_data(args)
    elif args.split_size:
        split_size(args)
    elif args.split_old:
        split_old(args)
    else:
        sp()
    


