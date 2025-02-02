from typing import List, Dict
from datetime import datetime, timedelta
import pytz
import warnings
import pymongo
import csv
from Heuristics.HeuristicInterface import HeuristicInterface
import git
from Database.db_repository import DBRepository

class ResultObject:
    def __init__(self):
        self.fixing_commit = None
        self.most_blamed = None
        self.oldest = None
        self.newest = None
        self.average = None
        self.w_average = None
        self.most_blamed_count = 0
        self.newest_count = 0
        self.oldest_count = 0
        self.w_average_count = 0
        self.stable = None

        self.vcc = None


class LifetimeEstimationHelper:

    @staticmethod
    def group_mappings(mappings: List) -> Dict:
        """
        Group mappings by the fixing commit to allow for more efficient calculation
        :param mappings: mappings as obtained from the db
        :return: dict of cve objects
        """
        commit_mappings = {}
        for x in mappings:
            cve = x[0].replace('\r', '').replace('\n', '')
            commit_sha = x[1]

            cwe = x[2].replace('\r', '').replace('\n', '')
            cvss_score = x[3].replace('\r', '').replace('\n', '')
            cvss_vector = x[4].replace('\r', '').replace('\n', '')
            cve_summary = x[5]
            if len(x) > 6:
                vcc = x[6]
            else:
                vcc = None
            cve_object = {'id': cve, 'cwe-id': cwe, 'cvss-score': cvss_score, 'cvss_vector': cvss_vector
                          , 'cve_summary': cve_summary, 'vcc': vcc}

            if commit_sha in commit_mappings:
                commit_mappings[commit_sha].append(cve_object)
            else:
                commit_mappings[commit_sha] = [cve_object]

        return commit_mappings

    @staticmethod
    def gt_mappings(gt_path: str, repo: git.Repo):
        res = {}
        with open(gt_path, 'r+') as f:

            for data in f.readlines()[1:]:
                if data[0] == '#' or data[0] == '%':
                    continue
                splits = data.split("  ")
                try:
                    vcc = repo.commit(splits[0])
                except ValueError:
                    warnings.warn("Commit not found {0}".format(splits[0]))
                    vcc = None

                except git.BadName:
                    warnings.warn("Commit not found {0}".format(splits[0]))
                    vcc = None
                cve = splits[2].replace('\r', '').replace('\n', '')
                if cve in res:
                    res[cve].append([vcc, splits[1].replace('\r', '').replace('\n', '')])
                else:
                    res[cve] = [[vcc, splits[1].replace('\r', '').replace('\n', '')]]
        return res

    @staticmethod
    def annotate_cve_information(mappings: dict):
        db = DBRepository()
        res = []
        for cve, vcc_fix in mappings.items():
            cve_lookup = db.fetch_cve(cve)
            if cve_lookup is None:
                warnings.warn(f'{cve} not found in DB')
                continue
            for vcc, fix in vcc_fix:
                item = [cve_lookup[0]
                        , fix
                        , cve_lookup[1]
                        , cve_lookup[2]
                        , cve_lookup[3]
                        , cve_lookup[4]
                        , vcc]
                res.append(item)

        db.close()
        return res


    @staticmethod
    def run_and_calculate(heuristic: HeuristicInterface, fixing_commit: git.Commit, repo: git.Repo, cve: dict):
        """Execute the heuristic and calculate all relevant data """
        res = ResultObject
        blames = heuristic.use_heuristic(fixing_commit, cve)
        res.fixing_commit = fixing_commit

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

            delta = commit.committed_datetime - ground_date
            average_days += delta.days
            weighted_average_days += delta.days * blame_count
            weight_count += blame_count
        if len(blames) == 0:
            warnings.warn('no blames')
            return None

        res.most_blamed = most_blamed[1]
        res.oldest = oldest[1]
        res.newest = newest[1]

        average = average_days / len(blames)
        weighted_average = weighted_average_days / weight_count

        res.average = ground_date + timedelta(days=average)
        res.w_average = ground_date + timedelta(days=weighted_average)

        most_blamed_count = repo.git.execute(['git', 'rev-list', '--count', '{0}..{1}'.format(most_blamed[1].hexsha
                                                                                              , fixing_commit.hexsha)])
        oldest_count = repo.git.execute(['git', 'rev-list', '--count', '{0}..{1}'.format(oldest[1].hexsha
                                                                                         , fixing_commit.hexsha)])
        newest_count = repo.git.execute(['git', 'rev-list', '--count', '{0}..{1}'.format(oldest[1].hexsha
                                                                                         , fixing_commit.hexsha)])
        w_average_count = repo.git.execute(['git', 'rev-list', '--count', '--after={0}'
                                           .format(ground_date + timedelta(days=weighted_average))
                                            , fixing_commit.hexsha])
        res.most_blamed_count = most_blamed_count
        res.newest_count = oldest_count
        res.oldest_count = newest_count
        res.w_average_count = w_average_count

        res.vcc = cve['vcc']

        return res

    @staticmethod
    def check_dsa_vulnerable(cve: dict, use_dsa: bool, dsa: pymongo.collection):
        """If the use_dsa flag is set, check if an DSA for that cve exists that marks a stable version as vulnerable"""
        stable = 'no'
        if use_dsa:
            try:
                cursor = dsa.find({'secrefs': {"$regex": cve['id'], '$options': 'i'}})
                for item in cursor:
                    stable = item['is_vulnerable']
            except Exception as e:
                print(str(e))
        return stable

    @staticmethod
    def writeline(spamwriter: csv.writer, res: ResultObject, cve: dict, gt: bool = False):
        row = [cve['id']
            , res.fixing_commit.hexsha
            , res.fixing_commit.committed_datetime.strftime('%Y-%m-%d')
            , res.most_blamed.hexsha
            , res.most_blamed.committed_datetime.strftime('%Y-%m-%d')
            , res.oldest.hexsha
            , res.oldest.committed_datetime.strftime('%Y-%m-%d')
            , res.newest.hexsha
            , res.newest.committed_datetime.strftime('%Y-%m-%d')
            , res.average.strftime('%Y-%m-%d')
            , res.w_average.strftime('%Y-%m-%d')
            , cve['cwe-id']
            , cve['cvss-score']
            , cve['cvss_vector']
            , res.most_blamed_count
            , res.newest_count
            , res.oldest_count
            , res.w_average_count
            , res.stable
               ]

        if gt:
            if res.vcc is None:
                row.insert(3, None)
                row.insert(4, None)
            else:
                row.insert(3, res.vcc.hexsha)
                row.insert(4, res.vcc.committed_datetime.strftime('%Y-%m-%d'))

        spamwriter.writerow(row)





