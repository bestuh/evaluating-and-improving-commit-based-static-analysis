from db_repository import DBRepository

commit_limit = -1
config = {}
#Chrome
config['Chrome'] = ['C:/Users/manue/Desktop/ThesisCode/Code/chromium', [r'Bug: \d{1,7}', r'Bug: chromium: \d{1,7}', r'Bug: chromium:\d{1,7}', r'BUG=\d{1,7}', r'BUG=http://crbug.com/\d{1,7}'], r'\d{1,7}']

#----------------------------------------------------------------------
#Firefox
config['Firefox'] = ['/srv/vcc_repos/gecko-dev', [r'Bug \d{1,7}', r'bug \d{1,7}'], r'\d{1,7}']

#----------------------------------------------------------------------
#WebKit
config['Webkit'] = ['/srv/vcc_repos/webkit',[r'https://bugs.webkit.org/show_bug.cgi\?id=\d{1,7}'], r'\d{1,7}']

#----------------------------------------------------------------------
#Linux Kernel
config['Linux'] = ['/srv/vcc_repos/linux', [r'CVE-\d{4}-\d{4,7}']]

#----------------------------------------------------------------------
#OpenBSD
config['OpenBSD'] = ['/srv/vcc_repos/openbsd/src', [r'CVE-\d{4}-\d{4,7]']]

#----------------------------------------------------------------------
#Wordpress
config['Wordpress'] = ['/srv/vcc_repos/wordpress-develop', [r'Fixes #\d{1,6}', r'fixes #\d{1,6}', r'see #\d{1,6}', r'See #\d{1,6}'], r'\d{1,6}']

#----------------------------------------------------------------------
#Mysql
#config['MySQL'] = ['/srv/vcc_repos/mysql-server', [r'Bug #\d{1,8}', r'Bug#\d{1,8}']]
config['MySQL'] = ['/srv/vcc_repos/mysql-server', [r'https://www.oracle.com/technetwork/security-advisory']]

#----------------------------------------------------------------------
#Postgresql
config['Postgresql'] = ['/srv/vcc_repos/postgres', [r'CVE-\d{4}-\d{4,7}']]

#----------------------------------------------------------------------
#MongoDB
config['Mongodb'] = ['/srv/vcc_repos/mongo', [r'CVE-\d{4}-\d{4,7}']]

#---------------------------------------------------------------------
#Angular
config['Angular'] = ['/srv/vcc_repos/angular', [r'(#\d{1,5})']]

#---------------------------------------------------------------------
#Apache
config['Apache'] = ['/srv/vcc_repos/httpd', [r'PR: \d{1,5}', r'PR \d{1,5}']]

#---------------------------------------------------------------------
#Nginx
config['Nginx'] = ['/srv/vcc_repos/nginx', [r'(ticket #\d{1,4})']]

#---------------------------------------------------------------------
#FFmpeg
config['FFmpeg'] = ['/srv/vcc_repos/FFmpeg', [r'CVE-\d{4}-\d{4,7}']]

#---------------------------------------------------------------------
#Openssl
config['Openssl'] = ['/srv/vcc_repos/openssl', [r'CVE-\d{4}-\d{4,7}']]

#--------------------------------------------------------------------
#Openjdk
config['Openjdk'] = ['/srv/vcc_repos/jdk', [r'\d{7}: ']]

#--------------------------------------------------------------------
#Coreclr
config['Coreclr'] = ['/srv/vcc_repos/coreclr', [r'CVE-\d{4}-\d{4,7}']]

#--------------------------------------------------------------------
#Cpython
config['Cpython'] = ['/srv/vcc_repos/cpython', [r'CVE-\d{4}-\d{4,7}']]

#--------------------------------------------------------------------

import re
from git import Repo, GitCommandError, BadName
import sys
import warnings
from RepositoryMining.CommitMappingClass import CommitMapping
from Utility.util import ConfigParse
import xml.etree.ElementTree as ET

class RepoMining:

    def __init__(self, config_node, db, config_code):
        repo_path = config_node.find('./path').text
        self.repo = Repo(repo_path)
        if self.repo.bare:
            raise Exception('Found bare repository under \'{0}\'!'.format(repo_path))

        print('Successfully loaded repository at \'{0}\''.format(repo_path))

        self.db = db
        if self.db:
            self.db_repo = DBRepository()
            self.config_code = config_code
        print('Starting repository mining...')

    def map_to_list(self, config_node: ET.Element, mapping_list: dict, mapping_type: str):

        if mapping_type == 'TypeCommitSha':
            res = self.map_from_commitsha(config_node, mapping_list)
        elif mapping_type in ["TypeCVEID", "TypeCommonID"]:
            commits = list(self.repo.iter_commits())

            print('Loaded {0} commits'.format(len(commits)))

            # find all commits containing a bug Identifier
            res = self.map(config_node, commits, mapping_list, mapping_type)
        else:
            warnings.warn('Unnkown mapping type! \'{0}\' Assuming \'mapping_list\' contains commit shas'
                          .format(mapping_type))
            res = self.map_from_commitsha(config_node, mapping_list, mapping_type)
        return res

    def map(self, config_node: ET.Element, commits: list, mapping_list: dict, mapping_type: str):
        unique_mapped_cves = {}
        commit_mappings = []
        for commit in commits:
            mapping = CommitMapping(commit, mapping_type)
            for regex_node in config_node.findall('./regex-list/regex'):
                regex = regex_node.find('./contains').text

                bug_id_search = re.search(regex, commit.message)
                if bug_id_search:
                    bug_id_list = ConfigParse.id_extraktion(regex_node, bug_id_search.group(0))

                    for bug_id in bug_id_list:
                        if bug_id in mapping_list:

                            if mapping_type == 'TypeCommonID':
                                mapping.cves.extend(mapping_list[bug_id])
                                for cve in mapping_list[bug_id]:
                                    unique_mapped_cves[cve] = True

                            elif mapping_type == "TypeCVEID":
                                mapping.cves.append(bug_id)
                                unique_mapped_cves[bug_id] = True

                            else:
                                raise NotImplementedError('Mapping type {0} currently not supported ')
            if len(mapping.cves) > 0:
                commit_mappings.append(mapping)
                if self.db:
                    self.db_repo.save_fixing_commit(mapping, self.config_code)

        print('{0} unique CVEs could be mapped to a total of {1} commits'.format(len(unique_mapped_cves), len(commit_mappings)))

        if self.db:
            self.db_repo.close()

        return commit_mappings

    def map_from_commitsha(self, config_node: ET.Element, mapping_list: dict, mapping_type: str = 'TypeCommitSha'):
        unique_mapped_cves = {}
        commit_mappings = []
        for commitsha, cves in mapping_list.items():
            try:
                commit = self.repo.commit(commitsha)
            except ValueError:
                warnings.warn("Commit not found {0}".format(commitsha))
                continue
            except BadName:
                warnings.warn("Commit not found {0}".format(commitsha))
                continue
            mapping = CommitMapping(commit, mapping_type)
            mapping.cves.extend(cves)
            for cve in cves:
                unique_mapped_cves[cve] = True
            commit_mappings.append(mapping)

            if len(mapping.cves) > 0:
                commit_mappings.append(mapping)
                if self.db:
                    self.db_repo.save_fixing_commit(mapping, self.config_code)

        print('{0} unique CVEs could be mapped to a total of {1} commits'.format(len(unique_mapped_cves), len(commit_mappings)))

        if self.db:
            self.db_repo.close()

        return commit_mappings

    def inspect_repo(self, config_node, mapping_type):

        commits = list(self.repo.iter_commits(max_count=100000))

        print('Loaded {0} commits'.format(len(commits)))
        unique_ids = {}
        mapped_commits = 0

        if mapping_type in ['TypeCommonID', 'TypeCVEID']:
            for commit in commits:
                mapped = False
                for regex_node in config_node.findall('./regex-list/regex'):
                    regex = regex_node.find('./contains').text

                    bug_id_search = re.search(regex, commit.message)
                    if bug_id_search:
                        mapped = True
                        bug_id_list = ConfigParse.id_extraktion(regex_node, bug_id_search.group(0))

                        for bug_id in bug_id_list:
                            if bug_id is not None:
                                unique_ids[bug_id] = True

                if mapped:
                    mapped_commits += 1
        else:
            raise NotImplementedError('Mapping type {0} currently not supported ')

        print('Found {0} unique Identifiers'.format(len(unique_ids)))
        print('Mapped {0} out of {1} commits: {2: 00%}'.format(mapped_commits, len(commits), mapped_commits / len(commits)))

if __name__ == "__main__":
    current_config = config[sys.argv[1]]
    repo_path = current_config[0]
    regex_list = current_config[1]

    if len(sys.argv) > 2:
        commit_limit = sys.argv[2]

    repo = Repo(repo_path)
    if commit_limit > 0:
        commits = list(repo.iter_commits(max_count=commit_limit))
    else:
        commits = list(repo.iter_commits())
    print("Repo at {0} contains {1} commits".format(repo_path, len(commits)))
    bug_commits = []
    bug_ids = []
    mappings = {}
    # find all commits containing a bug Identifier
    for commit in commits:
        identified = False
        for regex in regex_list:
            bug_id = re.search(regex, commit.message)
            if bug_id:
                mappings[bug_id.group(0)] = True
                bug_ids.append(bug_id.group(0))
                bug_commits.append(commit)
                identified = True
                break
        if not identified and 'Bug: none' not in commit.message and 'Bug: None' not in commit.message:
            print("-----------------------------------------------------------------------------")
            print()
            try:
                print(commit.message)
            except:
                print("Commit message not printed")


        #if not bug_id:
        #    print(commit.message)

    print('{0} unique IDs found'.format(len(mappings)))
    print('{0} out of {1} commits identified: {2}' .format(len(bug_ids), len(commits), float(len(bug_commits) / len(commits))))


