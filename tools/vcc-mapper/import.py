import csv
from pprint import pprint
import warnings
from RepositoryMining.RepoInspection import RepoMining
import xml.etree.ElementTree as ET
import json
import requests
from CVESearch import CVESearch

ground_truth_path = 'C:/Users/manue/Desktop/ThesisCode/Code/vcc-mapper/Datasets/kernel_vuls.txt'
xml_text = '''<repo>
                <path>C:/Users/manue/Desktop/ThesisCode/Code/linux</path>              
            </repo>'''

xml_procut = '''    <product name="tcpdump">
    <description>TcpDump</description>
    <mapping>
        <type>
            <name>TypeCommitSha</name>
        </type>
        <nvd>
            <cpe>tcpdump:tcpdump</cpe>
            <regex-list>
                <regex>
                    <contains>http(s)?://github.com/the-tcpdump-group/tcpdump/commit/[^\s]+</contains>
                    <id-extraktion>
			    <type>Cut</type>
			    <regex>http(s)?://github.com/the-tcpdump-group/tcpdump/commit/</regex>
                    </id-extraktion>
                </regex>
            </regex-list>
        </nvd>
        <repo>
            <path>/srv/vcc_repos/tcpdump</path>
            <regex-list>
            </regex-list>
        </repo>
    </mapping>
    </product>'''

def merge_dols(dol1, dol2):
    result = dict(dol1, **dol2)
    result.update((k, dol1[k] + dol2[k])
                  for k in set(dol1).intersection(dol2))
    return result

if __name__ == '__main__':


    file = './Import/http/http_commits.csv'
    file = './Import/tomcat/tomcat_commits.csv'
    file = './Import/kernel_cves.json'
    #file = './Datasets/kernel_vuls.txt'

    cves = {}
    unique_cves = {}
    with open(file, 'r', encoding='UTF-8') as myfile:
        data=myfile.read()
        input = json.loads(data)

    for cve_id, item in input.items():
        if 'fixes' in item and item['fixes'] is not None and item['fixes'] != 'None':
            commit = item['fixes']

            if commit in cves:
                cves[commit].append(cve_id)
            else:
                cves[commit] = [cve_id]

    # with open (file, encoding='utf-8') as csvfile:
    #     reader = csv.DictReader(csvfile)
    #     mappings = []
    #     for row in reader:
    #
    #         mappings.append(row)
    #         cve_id = row['cve_id']
    #         commit = row['fix_commit_id']
    #
    #         if commit in cves:
    #             cves[commit].append(cve_id)
    #         else:
    #             cves[commit] = [cve_id]

    #
    # with open(ground_truth_path, 'r+') as f:
    #     fixing_commits_set = set()
    #     for data in f.readlines()[1:]:
    #         if data[0] == '#' or data[0] == '%':
    #             continue
    #         splits = data.split("  ")
    #         commit = splits[1]
    #         cve_id = splits[2].replace('\n', '').replace('\r', '')
    #
    #         unique_cves[cve_id] = cve_id
    #         if commit in cves:
    #             cves[commit].append(cve_id)
    #         else:
    #             cves[commit] = [cve_id]




    print("Total number of unique cves: {0}".format(len(unique_cves)))
    repo_node = ET.fromstring(xml_text)
    repo = RepoMining(repo_node, True, 'kernel')
    repo.map_to_list(repo_node, cves, 'LinuxKernelCVEs')



    # product_node = ET.fromstring(xml_procut)
    # mapping_node = product_node.find('./mapping')
    # mapping_type = mapping_node.find('./type/name').text
    # cve_search = CVESearch(False, 'tcpdump')
    # cve_res = {}
    #
    # for nvd_node in mapping_node.findall('./nvd'):
    #     if mapping_type == 'TypeCVEID':
    #         cve_res = merge_dols(cve_res, cve_search.get_cves(nvd_node))
    #     else:
    #         cve_res = merge_dols(cve_res, cve_search.get_cve_mappings(nvd_node))


    # count = 1
    # url = "https://api.github.com/repos/manuelbrack/tomcat/git/refs"
    # headers = {
    #     "Accept" : "application/json",
    #     "Content-Type" : "application/json",
    #     "Authorization" : "token 18820044f579e623e5e2451aeef6678765b6f61a" # Hier muss dein Token rein
    # }
    #
    # for commit_sha, cve_list in cves.items():
    #     payload = {
    #         "ref": "refs/heads/D-commit-{0}".format(count),
    #         "sha": commit_sha
    #     }
    #     r = requests.post(url, data=json.dumps(payload), headers=headers)
    #     print(r.text)
    #     count+=1

