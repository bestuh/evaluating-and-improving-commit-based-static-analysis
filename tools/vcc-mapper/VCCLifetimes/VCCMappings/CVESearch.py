import re
import pymongo
from pymongo import MongoClient
from Utility.util import ConfigParse
from Database.db_repository import DBRepository
from typing import Dict, List
import xml.etree.ElementTree as ET
from tqdm import tqdm

class CVESearch:
    """Performs querying and processing of relevant CVEs"""

    def __init__(self, db: bool, config_code: str):
        """
        Constructor
        :param db: Specifies if matching CVEs should be added to the DB
        :param config_code: Config code of the working project
        """
        self.db = db
        if self.db:
            self.db_repo = DBRepository()
            self.config_code = config_code

    def get_cve_mappings(self, config_node: ET.Element) -> Dict[str, List[str]]:
        """
        According to the provided config node fetches all matching CVEs and extracts ids from the references
        :param config_node: a 'nvd' node from the config.xml
        :return: Dict with identifiers as keys and a list of associated CVE-IDs
        """

        # Fetch CVEs from ccd ve-search's MongoDB
        cves = self.__fetch_cves(config_node)

        cve_list = {}
        total = 0
        mapped = {}
        pbar = tqdm(desc='CVE search')
        for cve in cves:

            # If DB flag has been set, write CVE to the database
            if self.db:
                self.db_repo.save_cve(cve, self.config_code)

            cve_id = cve['id']
            total = total + 1

            # Iterate over all references listed for the CVE
            for ref in cve['references']:
                # Try each of the extraction regex specified in the config
                for regex_node in config_node.findall('./regex-list/regex'):
                    regex = regex_node.find('./contains').text
                    # Check if the text contains text in the required format
                    regex_res = re.search(regex, ref)
                    if regex_res:
                        # Mark this CVE as mapped
                        mapped[cve_id] = True
                        # Extract a list of IDs from the matched text
                        bug_id_list = ConfigParse.id_extraktion(regex_node, regex_res.group(0))

                        # Add the extracted ids to the result set
                        for bug_id in bug_id_list:
                            if bug_id in cve_list:
                                cve_list[bug_id].append(cve_id)
                            elif bug_id is not None:
                                cve_list[bug_id] = [cve_id]

            pbar.update(1)

        print("\n{0} out of {1} CVES can be mapped to internal id\n".format(len(mapped), total))

        # Make sure to close the DB connection after using it
        if self.db:
            self.db_repo.close()

        return cve_list

    def get_cves(self, config_node: ET.Element) -> Dict[str, str]:
        """
        According to the provided config node fetches all matching CVEs
        :param config_node: a 'nvd' node from the config.xml
        :return: Dict with all matching CVE-IDs as key and element
        """
        # Extract all matching CVEs
        cves = self.__fetch_cves(config_node)
        cve_list = {}

        # Add each CVE to the result list
        pbar = tqdm(desc='CVE search')
        for cve in cves:

            if self.db:
                self.db_repo.save_cve(cve, self.config_code)

            cve_id = cve['id']
            cve_list[cve_id] = cve_id

            pbar.update(1)

        print("\n{0} CVEs found\n".format(len(cve_list)))

        # Make sure to close the DB connection after using it
        if self.db:
            self.db_repo.close()

        return cve_list

    @staticmethod
    def __fetch_cves(config_node: ET.Element) -> pymongo.cursor.Cursor:
        """
        Perfoms the fetching of cve entries from the cve-search mongo db
        :param config_node: a 'nvd' node from the config.xml
        :return: pymongo cursor to the results of the query
        """
        cpe_regex = config_node.find("./cpe").text
        print('Starting CVE search for CPE {0}...'.format(cpe_regex))

        try:
            client = MongoClient()
            dbnames = client.list_database_names()

            if 'cvedb' not in dbnames:
                raise Exception('Mongo DB "cvedb" not found. Make sure that cve-search is running on your machine')

        except Exception:
            raise Exception('Mongo DB does not seem to be running on your machine')

        # cve-search stores cves in the db 'cvedb' and collection 'cves'
        db = client.cvedb
        cve_collection = db.cves
        cves = cve_collection.find({'vulnerable_configuration': {"$regex": cpe_regex, '$options': 'i'}})
        return cves

