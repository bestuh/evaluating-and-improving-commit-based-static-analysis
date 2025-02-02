from git import Repo, GitCommandError, BadName
import os
import re
from datetime import datetime
import pytz
import numpy as np
from random import random
from multiprocessing import Pool, Manager
import time



repo_path = '/dev/shm'
repo_path = 'C:/Users/manue/Desktop/ThesisCode/Code/openssl'

#manager = Manager()
#global_ages = manager.list([])

def is_code_file(file):
    if file:
        return re.match('^.*\.(c|c\+\+|cpp|h|hpp|php|cc)$', file) and (not "test" in file.lower()) #('^.*\.(c|c\+\+|cpp|h|hpp|php)$', file)
    return False



def blame_file(filepath, repo, reference_date):
    if random() > 1:
        return []
    if not is_code_file(filepath):
        return []
    try:
        ages = []
        blames = repo.blame('HEAD', filepath)
        for commit, lines in blames:
            delta = reference_date - commit.committed_datetime
            ages.append(delta.days)
        return ages
    except:
        return []
    #global_ages.extend(ages)


def blame_subdir(root, subdir, files, reference_date):
    repo = Repo(repo_path)
    ages = []
    for file in files:
        filepath = os.path.join(root, file)
        ages.extend(blame_file(filepath, repo, reference_date))

    return ages

def perform_sampling(reference_date, branch, ratio=1):
    blame_repo = Repo(repo_path)


    files_count = 0
    lines = 0
    ages = []
    pool = Pool()

    walk_result = [(root, subdir, files, reference_date) for root, subdir, files in os.walk(repo_path)]
    results = pool.starmap(blame_subdir, walk_result)

        #filepaths = [(os.path.join(root, x), blame_repo, reference_date) for x in files]
        #results = pool.starmap(blame_file, filepaths)

    for age in results:
       ages.extend(age)
    # for root, subdir, files in os.walk(repo_path):
    #     if '.git' in subdir:
    #         subdir.remove('.git')
    #
    #     for file in files:
    #          filepath = os.path.join(root, file)
    #          ages.extend(blame_file(filepath, blame_repo, reference_date))

    print('Average lifetime over {0} lines: {1}'.format(len(ages), np.mean(ages)))
    return np.mean(ages)

if __name__ == "__main__":
    branches = ['2015', '2014', '2013']#'2012', '2011', '2010', '2009', '2008', '2007', '2006']
              # , '2005', '2004', '2003', '2002', '2001', '2000']
    repo = Repo(repo_path)
    for branch in branches:
        print(repo_path)
        print('################################################')
        print('Year:{0}'.format(branch))
        utc = pytz.timezone('UTC')
        date = datetime(int(branch), 7, 1, tzinfo=utc)
        start_time = time.time()
        repo.git.execute(['git', 'checkout', '-f', branch])
        res = perform_sampling(date, branch, 1)
        #with open('./out/{0}.text', 'r') as f:
         #   f.write(res)

        print("--- %s seconds ---" % (time.time() - start_time))
