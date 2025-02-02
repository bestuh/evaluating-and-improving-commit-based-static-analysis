import mysql.connector
from git import Repo, GitCommandError, BadName

from RepositoryMining.VuldiggerHeuristic2 import VuldiggerHeuristic2
from RepositoryMining.OwnHeuristic import  OwnHeuristic
from RepositoryMining.LowerBound import  LowerBound
from RepositoryMining.VccfinderHeuristicSerial import  VccfinderHeuristicSerial
import csv
import warnings
from datetime import datetime, timedelta
import pytz
from tqdm import tqdm
from pymongo import MongoClient


def load_ground_truth_dataset(ground_truth_path, repo):
    res = {}
    with open(ground_truth_path, 'r+') as f:
        fixing_commits_set = set()
        for data in f.readlines()[1:]:
            if data[0] == '#' or data[0] == '%':
                continue
            splits = data.split("  ")
            try:
                vcc = repo.commit(splits[0])
            except ValueError:
                warnings.warn("Commit not found {0}".format(splits[1]))
            except BadName:
                warnings.warn("Commit not found {0}".format(splits[1]))
            if splits[1] in res:
                res[splits[1]].append([vcc, splits[2]])
            else:
                res[splits[1]] = [[vcc, splits[2]]]
    return res

config = {
    'user': 'mbrack',
    'password': 'GK4zNrqK',
    'host': '130.83.163.37',
    'database': 'vcc',
}

def run_heuristic(ground_truth_path: str, repo_path: str, out_path: str):
    #cnx = mysql.connector.connect(auth_plugin='mysql_native_password', **config)
    client = MongoClient()
    db = client.cvedb
    cve_collection = db.cves

    repo = Repo(repo_path)

    ground_truth = load_ground_truth_dataset(ground_truth_path, repo)
    heuristic = VccfinderHeuristicSerial()
    heuristic = VuldiggerHeuristic2()
    #heuristic = OwnHeuristic()
    #heuristic = LowerBound()
    count = 0
    with open(out_path, 'w', newline='') as csvfile:

        spamwriter = csv.writer(csvfile, delimiter=';',
                                quotechar='\'', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(['CVE', 'Fixing sha', 'Fixing date', 'VCC sha', 'VCC date', 'VCC-heuristic sha', 'VCC-heuristic date', 'VCC-oldest sha', 'VCC-oldest date', 'VCC-newest sha', 'VCC-newest date', 'Average date', 'Weighted Average date', 'Heuristic Date', 'Confident'])
        #spamwriter.writerow(['CVE', 'Fixing sha', 'Fixing date', 'VCC sha', 'VCC date', 'VCC-heuristic sha', 'VCC-heuristic date', 'VCC-oldest sha', 'VCC-oldest date', 'VCC-newest sha', 'VCC-newest date', 'Average date', 'Weighted Average date', 'Heuristic Date'])
        #spamwriter.writerow(['CVE', 'Fixing sha', 'Fixing date', 'VCC sha', 'VCC date', 'VCC-newest sha', 'VCC-newest date'])
        for key, fixes in tqdm(ground_truth.items()):
            for fix in fixes:
                count += 1

                try:
                    #cursor = cnx.cursor()
                    sql = '''SELECT DISTINCT cve.cve_id, cve.cve_cwe_id, cve.cve_summary
                FROM cve
                WHERE cve.cve_id = \'{0}\''''.format(fix[1].replace('\r', '').replace('\n', ''))

                    #cursor.execute(sql)
                    #mappings = cursor.fetchall()
                    #cursor.close()
                    cves = cve_collection.find({'id': {"$regex": fix[1].replace('\r', '').replace('\n', ''), '$options': 'i'}})
                    #cwe = mappings[0][1]
                    cwe = cves[0]['cwe']
                    #cve_summary =  mappings[0][2]
                    cve_summary = cves[0]['summary']
                    #cve = mappings[0]['summary']
                    cve = cves[0]['id']
                    cve_object = {'id': cve, 'cwe-id': cwe, 'cve_summary': cve_summary}

                except Exception as e:
                    cve_object = {}
                    print('CVE not found: ' + fix[1])
                #ignore driver removals:
                #if key in ['ef4a0c3173736a957d1495e9a706d7e7e3334613', 'a73e99cb67e7438e5ab0c524ae63a8a27616c839']:
                 #   continue

                try:
                    fixing_commit = repo.commit(key)
                except ValueError:
                     warnings.warn("Commit not found {0}".format(key))
                     continue
                except BadName:
                    warnings.warn("Commit not found {0}".format(key))
                    continue


                #print(fix[1].replace('\n', '') + ': ' + fixing_commit.hexsha + ' - ' +str(count))

                blame_dict, cve, confident = heuristic.use_heuristic(repo, fixing_commit, cve_object, java=True)
                #newest_vcc = heuristic.use_heuristic(repo, fixing_commit)

                #blame_dict = {}
                #heuristic.use_heuristic(repo, fixing_commit, blame_dict)


                most_blamed = None
                newest = None
                oldest = None

                average_days = 0
                weighted_average_days = 0
                weight_count = 0
                ground_date = pytz.utc.localize(datetime.strptime('1900-01-01', '%Y-%m-%d'))

                for commit, blame_count in blame_dict.items():

                    if most_blamed is None or blame_count > most_blamed[0]:
                        most_blamed = [blame_count, commit]
                    if newest is None or commit.committed_datetime > newest[1].committed_datetime:
                        newest = [blame_count, commit]
                    if oldest is None or commit.committed_datetime < oldest[1].committed_datetime:
                        oldest = [blame_count, commit]

                    delta = commit.committed_datetime - ground_date
                    average_days += delta.days
                    weighted_average_days += delta.days * blame_count
                    weight_count += blame_count

                if len(blame_dict) == 0:
                    warnings.warn('no blames')
                    continue

                average = average_days / len(blame_dict)
                weighted_average = weighted_average_days / weight_count
                heuristic_days = (most_blamed[1].committed_datetime - ground_date).days * 50 + (oldest[1].committed_datetime - ground_date).days * 30 + (newest[1].committed_datetime - ground_date).days * 20
                heuristic_average = heuristic_days / 100
                try:
                    spamwriter.writerow([fix[1].replace('\r', '').replace('\n', ''), fixing_commit.hexsha, fixing_commit.committed_datetime,  fix[0].hexsha, fix[0].committed_datetime, most_blamed[1].hexsha, most_blamed[1].committed_datetime, oldest[1].hexsha, oldest[1].committed_datetime, newest[1].hexsha, newest[1].committed_datetime, ground_date + timedelta(days=average) , ground_date + timedelta(days=weighted_average), ground_date + timedelta(days=heuristic_average), confident])
                    #spamwriter.writerow([fix[1].replace('\r', '').replace('\n', ''), fixing_commit.hexsha, fixing_commit.committed_datetime,  fix[0].hexsha, fix[0].committed_datetime, most_blamed[1].hexsha, most_blamed[1].committed_datetime, oldest[1].hexsha, oldest[1].committed_datetime, newest[1].hexsha, newest[1].committed_datetime, ground_date + timedelta(days=average) , ground_date + timedelta(days=weighted_average), ground_date + timedelta(days=heuristic_average)])
                    #spamwriter.writerow([fix[1].replace('\r', '').replace('\n', ''), fixing_commit.hexsha, fixing_commit.committed_datetime,  fix[0].hexsha, fix[0].committed_datetime, newest_vcc.hexsha, newest_vcc.committed_datetime])
                except Exception as e:
                    print(str(e))
                    warnings.warn(str(e))

if __name__ == '__main__':
    run_heuristic('./Datasets/Training/tomcat_vuls.txt',
                  '/srv/vcc_repos/tomcat', './out/vul2_tomcat.csv')
    run_heuristic('./Datasets/Training/struts_vuls.txt.txt',
                  '/srv/vcc_repos/struts', './out/vul2_struts.csv')








