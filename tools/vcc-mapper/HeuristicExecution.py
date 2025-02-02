import mysql.connector
from git import Repo, GitCommandError, BadName
import warnings
from RepositoryMining.VuldiggerHeuristic2 import VuldiggerHeuristic2
from RepositoryMining.OwnHeuristic import OwnHeuristic
from datetime import datetime, timedelta
import pytz
import csv
from pymongo import MongoClient
from tqdm import tqdm

config = {
        'user': 'mbrack',
        'password': 'GK4zNrqK',
        'host': '130.83.163.37',
        'database': 'vcc',
    }
repo_path = 'C:/Users/manue/Desktop/ThesisCode/Code/php-src'
#repo_path = 'C:/Users/manue/Desktop/ThesisCode/Code/httpd'
#repo_path = '/srv/vcc_repos/wireshark'

if __name__ == "__main__":
    cnx = mysql.connector.connect(auth_plugin='mysql_native_password', **config)
    cursor = cnx.cursor()
    sql = '''SELECT DISTINCT cve.cve_id, commit.com_sha, cve.cve_cwe_id, cve.cve_cvss_score, cve.cve_cvss_vector, cve.cve_summary
FROM cve
INNER JOIN cve_config_code ON cve_config_code.cve_id = cve.cve_id
INNER JOIN link_cve_fixing_commit ON link_cve_fixing_commit.cve_id =  cve.cve_id and link_cve_fixing_commit.com_config_code = cve_config_code.config_code
INNER JOIN commit ON commit.com_sha = link_cve_fixing_commit.com_sha AND commit.com_config_code = link_cve_fixing_commit.com_config_code
WHERE cve_config_code.config_code = 'php' '''
    cursor.execute(sql)
    mappings = cursor.fetchall()
    cnx.close()

    repo = Repo(repo_path)
    heuristic = VuldiggerHeuristic2()

    commit_mappings = {}
    for x in mappings:
        cve = x[0]
        commit_sha = x[1]

        cwe = x[2]
        cvss_score = x[3]
        cvss_vector = x[4]
        cve_summary = x[5]
        cve_object = {'id': cve, 'cwe-id': cwe, 'cvss-score':cvss_score, 'cvss_vector': cvss_vector, 'cve_summary': cve_summary}

        if commit_sha in commit_mappings:
            commit_mappings[commit_sha].append(cve_object)
        else:
            commit_mappings[commit_sha] = [cve_object]
    count = 0
    with open('./out/php.csv', 'w') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=';',
                                quotechar='\'', quoting=csv.QUOTE_MINIMAL)

        spamwriter.writerow(['CVE', 'Fixing sha', 'Fixing date', 'VCC-heuristic sha', 'VCC-heuristic date', 'VCC-oldest sha', 'VCC-oldest date', 'VCC-newest sha', 'VCC-newest date', 'Average date', 'Weighted Average date', 'Heuristic Date', 'CWE', 'CVSS-Score', 'CVSS-Vector', 'Commits heuristic', 'Commmits newest', 'Commits oldest', 'Commits weighted', 'Confident', 'Stable'])

        client = MongoClient()
        db = client.admin
        dla = db.dla
        dsa = db.dsa

        for commit_sha, cves in tqdm(commit_mappings.items()):
            for cve in cves:
                #if commit_sha in ['af98b64566c0fb42c069d76d0b8dae4329120680', '62d958a2bed1fc382826b4d9553e210f913db3d4', 'f7423b5b9a012586bd6a778a10d767c4060e1043']: #firefox
                #if commit_sha in ['b3a6082223369203d7e7db7e81253ac761377644', 'd64c2a76123f0300b08d0557ad56e9d599872a36', '727dede0ba8afbd8d19116d39f2ae8d19d00033d']:
                if commit_sha in ['d3fbdf0048cd0d99a57720c589b8d7a1d5f223af', '864d69bef784d303e2664c943c4281d34f62b09d', 'd539e61c303eea2058cc5b99b4bbfec92438132f']:
                    continue
                count += 1

                print(commit_sha + " " + str(count))

                try:
                    fixing_commit = repo.commit(commit_sha)
                except ValueError:
                    warnings.warn("Commit not found {0}".format(commit_sha))
                    continue
                except BadName:
                    warnings.warn("Commit not found {0}".format(commit_sha))
                    continue

                blames, _, confident = heuristic.use_heuristic(repo, fixing_commit, cve, False)

                most_blamed = None
                newest = None
                oldest = None

                average_days = 0
                weighted_average_days = 0
                weight_count = 0
                ground_date = pytz.utc.localize(datetime.strptime('1900-01-01', '%Y-%m-%d'))

                for commit, blame_count in blames.items():

                    if most_blamed is None or blame_count > most_blamed[0]:
                        most_blamed = [blame_count, commit]
                    if newest is None or commit.committed_datetime > newest[1].committed_datetime:
                        newest = [blame_count, commit]
                    if oldest is None or commit.committed_datetime < oldest[1].committed_datetime:
                        oldest = [blame_count, commit]

                    delta =commit.committed_datetime - ground_date
                    average_days += delta.days
                    weighted_average_days += delta.days * blame_count
                    weight_count += blame_count
                if len(blames) == 0:
                    warnings.warn('no blames')
                    print('no blames')
                    continue

                heuristic_count = repo.git.execute(['git', 'rev-list', '--count', '{0}..{1}'.format(most_blamed[1].hexsha, commit_sha)])
                oldest_count = repo.git.execute(['git', 'rev-list', '--count', '{0}..{1}'.format(oldest[1].hexsha, commit_sha)])
                newest_count =  repo.git.execute(['git', 'rev-list', '--count', '{0}..{1}'.format(oldest[1].hexsha, commit_sha)])


                average = average_days / len(blames)
                weighted_average = weighted_average_days / weight_count
                heuristic_days = (most_blamed[1].committed_datetime - ground_date).days * 50 + (oldest[1].committed_datetime - ground_date).days * 30 + (newest[1].committed_datetime - ground_date).days * 20
                heuristic_average = heuristic_days / 100

                w_average_count = repo.git.execute(['git', 'rev-list', '--count', '--after={0}'.format(ground_date + timedelta(days=weighted_average)), commit_sha])

                stable = 'no'
                try:
                    cursor = dsa.find({'secrefs': {"$regex": cve['id'].replace('\r', '').replace('\n', ''), '$options': 'i'}})
                    for item in cursor:
                        stable = item['is_vulnerable']
                except Exception as e:
                    print(str(e))

                try:
                    spamwriter.writerow([cve['id'].replace('\r', '').replace('\n', ''), fixing_commit.hexsha,
                                         fixing_commit.committed_datetime, most_blamed[1].hexsha,
                                         most_blamed[1].committed_datetime, oldest[1].hexsha,
                                         oldest[1].committed_datetime, newest[1].hexsha,
                                         newest[1].committed_datetime, ground_date + timedelta(days=average) ,
                                         ground_date + timedelta(days=weighted_average),
                                         ground_date + timedelta(days=heuristic_average),
                                         cve['cwe-id'], cve['cvss-score'],
                                         cve['cvss_vector'].replace('\r', '').replace('\n', ''),
                                         heuristic_count, newest_count, oldest_count, w_average_count
                                         , confident, stable])
                except Exception as e:
                    print(str(e))
                    warnings.warn(str(e))

