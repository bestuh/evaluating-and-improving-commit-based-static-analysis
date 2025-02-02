from Database.db_repository import DBRepository
import re
from git import Repo, BadName
import warnings
from .CommitMappingClass import CommitMapping
from Utility.util import ConfigParse
import xml.etree.ElementTree as ET
import os
from typing import List
from tqdm import tqdm


class RepoMining:
    """Implements repository mining techniques """

    def __init__(self, config_node: ET.Element, db: bool, config_code: str):
        """
        Constructor
        :param config_node: a repo node of the config.xml
        :param db: flag whether to write results to the database
        :param config_code: code of the working project
        """
        self.config_node = config_node

        repo_path = config_node.find('./path').text

        if not os.path.exists(repo_path):
            raise OSError(f'Repository path "{repo_path}" not found!')

        self.repo = Repo(repo_path)
        if self.repo.bare:
            raise Exception('Found bare repository under \'{0}\'!'.format(repo_path))

        print('Successfully loaded repository at \'{0}\''.format(repo_path))

        self.db = db
        if self.db:
            self.db_repo = DBRepository()
            self.config_code = config_code

        print('Starting repository mining...')

    def map_to_list(self, mapping_list: dict, mapping_type: str) -> List[CommitMapping]:
        """
        Performs repository mining with respect to the provided configuration and mapping method
        :param mapping_list: Mappings between CVEs and commits or bug IDs
        :param mapping_type: Type of the mapping
        :return:
        """
        if mapping_type == 'TypeCommitSha':
            # Find commits by their sha
            res = self.__map_from_commitsha(self.config_node, mapping_list)
        elif mapping_type in ["TypeCVEID", "TypeCommonID"]:
            # Load all commits into memory
            commits = list(self.repo.iter_commits())

            print('Loaded {0} commits'.format(len(commits)))

            # find all commits containing a bug Identifier
            res = self.__map(self.config_node, commits, mapping_list, mapping_type)
        else:
            warnings.warn('Unnkown mapping type! \'{0}\' Assuming \'mapping_list\' contains commit shas'
                          .format(mapping_type))
            res = self.__map_from_commitsha(self.config_node, mapping_list, mapping_type)
        return res

    def __map(self, config_node: ET.Element, commits: list, mapping_list: dict, mapping_type: str):
        """Map commits using a common identifier or the CVE-ID itself"""
        unique_mapped_cves = {}
        commit_mappings = []

        # Iterate over every commit in the repository
        for commit in tqdm(commits, desc='Repository Mining'):
            mapping = CommitMapping(commit, mapping_type)

            # Try every regex in the config to see if the commit message matches one of them
            for regex_node in config_node.findall('./regex-list/regex'):
                regex = regex_node.find('./contains').text

                bug_id_search = re.search(regex, commit.message)
                if bug_id_search:
                    # Extract list of IDs from the matched text
                    bug_id_list = ConfigParse.id_extraktion(regex_node, bug_id_search.group(0))

                    for bug_id in bug_id_list:
                        # Add all identified IDs that are also contained in the mapping list to the intermediate set
                        if bug_id in mapping_list:

                            # Respect the difference in mapping_list structure between common IDs and CVE IDs
                            if mapping_type == 'TypeCommonID':
                                mapping.cves.extend(mapping_list[bug_id])
                                for cve in mapping_list[bug_id]:
                                    unique_mapped_cves[cve] = True

                            elif mapping_type == "TypeCVEID":
                                mapping.cves.append(bug_id)
                                unique_mapped_cves[bug_id] = True

                            else:
                                raise NotImplementedError('Mapping type {0} currently not supported ')
            # If atleast one mapping was found add to the result set
            if len(mapping.cves) > 0:
                commit_mappings.append(mapping)
                if self.db:
                    self.db_repo.save_fixing_commit(mapping, self.config_code)

        print('{0} unique CVEs could be mapped to a total of {1} commits'.format(len(unique_mapped_cves), len(commit_mappings)))

        # Make sure to close the DB connection after using it
        if self.db:
            self.db_repo.close()

        return commit_mappings

    def __map_from_commitsha(self, config_node: ET.Element, mapping_list: dict, mapping_type: str = 'TypeCommitSha'):
        """Map commits using their commit sha"""
        unique_mapped_cves = {}
        commit_mappings = []

        # Iterate over all mappings in the provided mapping list
        for commitsha, cves in tqdm(mapping_list.items(), desc='Repository Mining'):

            # Try to retrieve the commit from the repository
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

        # Make sure to close the DB connection after using it

        if self.db:
            self.db_repo.close()

        return commit_mappings

    def inspect_repo(self, mapping_type: str, max_count: int = 100000):
        """
        Perform an inspection of the repository to check the number of commits that can be matched to the provided matching types and regular expressions
        No mapping to CVEs is performed and the resulting data is not stored
        :param mapping_type: Type of the used mapping strategy
        :param max_count: maximum number of commits to consider
        """

        # Load all commits into memory
        commits = list(self.repo.iter_commits(max_count=max_count))

        print('Loaded {0} commits'.format(len(commits)))
        unique_ids = {}
        mapped_commits = 0

        if mapping_type in ['TypeCommonID', 'TypeCVEID']:
            for commit in tqdm(commits, desc='Repository Mining'):
                mapped = False
                for regex_node in self.config_node.findall('./regex-list/regex'):
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
        print('Mapped {0} out of {1} commits: {2:2%}'.format(mapped_commits, len(commits), mapped_commits / len(commits)))


