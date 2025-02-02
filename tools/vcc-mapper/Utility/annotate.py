from pymongo import MongoClient
import re
import sys
from pprint import pprint
import csv
from git import Repo, GitCommandError, BadName
from datetime import datetime

filepath = './firefox-mapped.csv'
filepath = './chrome-mapped.csv'
filepath = './kernel_gt_mapped_stable.csv'
filepath = './in/httpd-mapped.csv'

repo_path = 'C:/Users/manue/Desktop/ThesisCode/Code/gecko-dev'
repo_path = 'C:/Users/manue/Desktop/ThesisCode/Code/chromium'
repo_path = 'C:/Users/manue/Desktop/ThesisCode/Code/httpd'

def asses_stable_vul():
    client = MongoClient()
    db = client.admin
    dla = db.dla
    dsa = db.dsa

    cves = {}
    with open(filepath, 'r+') as f:
        spamreader = csv.reader(f, delimiter=";", quotechar='\'')
        with open('kernel_mapped_stable.csv', 'w') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=';',
                                    quotechar='\'', quoting=csv.QUOTE_MINIMAL)


            row_count = 0
            for row in spamreader:

                splits = row
                if row_count == 0:
                    splits.append('Stable')
                    spamwriter.writerow(splits)
                    row_count += 1
                    continue

                cve_id = splits[0]
                stable = 'no'
                try:
                    cursor = dsa.find({'secrefs': {"$regex": cve_id, '$options': 'i'}})
                    for item in cursor:
                        stable = item['is_vulnerable']
                except Exception as e:
                    print(str(e))
                splits.append(stable)
                spamwriter.writerow(splits)

def count_lifetime_in_commits(is_ground_truth=False):
    offset = 2 if is_ground_truth else 0
    repo = Repo(repo_path)

    if repo.bare:
        print("Repo is bare under {0}".format(repo_path))
        return
    count = 0
    with open(filepath, 'r+') as f:
        with open('./out/httpd-mapped_commitcount.csv', 'w') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=';',
                                    quotechar='\'', quoting=csv.QUOTE_MINIMAL)
            spamwriter.writerow(['CVE', 'Fixing sha', 'Fixing date',  'VCC-heuristic sha', 'VCC-heuristic date', 'VCC-oldest sha', 'VCC-oldest date', 'VCC-newest sha', 'VCC-newest date', 'Average date', 'Weighted Average date', 'Heuristic Date', 'CWE', 'CVSS-score', 'CVSS-Vector', 'Commits', 'Commits heuristic', 'Commmits newest', 'Commits oldest', 'Commits weighted'])
            for line in f.readlines()[1:]:
                count += 1
                print(count)

                splits = line.split(';')
                fixing_sha = splits[1]

                vcc_count = None
                if is_ground_truth:
                    vcc_sha = splits[3]
                    vcc_count = repo.git.execute(['git', 'rev-list', '--count', '{0}..{1}'.format(vcc_sha, fixing_sha)])

                heuristic_sha = splits[3 + offset]
                oldest_sha = splits[5 + offset]
                newest_sha = splits[7 + offset]

                heuristic_count = repo.git.execute(['git', 'rev-list', '--count', '{0}..{1}'.format(heuristic_sha, fixing_sha)])

                oldest_count = repo.git.execute(['git', 'rev-list', '--count', '{0}..{1}'.format(oldest_sha, fixing_sha)])

                newest_count =  repo.git.execute(['git', 'rev-list', '--count', '{0}..{1}'.format(newest_sha, fixing_sha)])

                w_average_date = splits[11 + is_ground_truth][:10]
                w_average_count = repo.git.execute(['git', 'rev-list', '--count', '--after={0}'.format(w_average_date), fixing_sha])

                splits.extend([vcc_count, heuristic_count, newest_count, oldest_count, w_average_count])
                spamwriter.writerow(splits)

if __name__ == "__main__":
   # count_lifetime_in_commits(False)
    asses_stable_vul()
