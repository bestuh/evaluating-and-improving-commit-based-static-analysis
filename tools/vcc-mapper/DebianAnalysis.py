from RepositoryMining.RepoInspection import  RepoMining
import re
import xml.etree.ElementTree as ET

file = './Import/Debian_Security.txt'

cves = {}
cve = None

#xml_text = '''<repo>
#                <path>/srv/vcc_repos/mysql-server</path>
#                <regex-list>
#                    <regex>
#                        <contains>Bug #\d{5,8}</contains>
#                        <id-extraktion>
#                            <type>Regex</type>
#                            <regex>\d{5,7}</regex>
#                        </id-extraktion>
#                    </regex>
#                </regex-list>
#            </repo>'''
xml_text = '''<repo>
                <path>/srv/vcc_repos/wireshark</path>              
            </repo>'''
xml_text = '''<repo>
                 <path>C:/Users/manue/Desktop/ThesisCode/Code/wireshark</path>
             </repo>'''
unique_cves = 0

if __name__ == '__main__':
    with open(file, 'r+') as f:
        for data in f.readlines():
            if data.startswith('CVE-'):
                search = re.search('CVE-\d{4}-\d{4,7}', data)
                if search:
                    cve = search.group(0)
            elif data.startswith('	- mysql-'):
                for res in re.finditer('bug #\d{5,6}', data):
                    bug_id = res.group(0).replace('bug #', '')
#                    if bug_id in cves:
#                       cves[bug_id].append(cve)
#                    else:
#                        cves[bug_id] = [cve]
            elif 'https://code.wireshark.org/review/gitweb' in data:
                for res in re.finditer(';a=commit;h=[^\s]*', data):
                    bug_id = res.group(0).replace(';a=commit;h=', '')
                    if bug_id in cves:
                        cves[bug_id].append(cve)
                    else:
                        cves[bug_id] = [cve]
            elif 'https://github.com/FFmpeg/FFmpeg' in data:
                unique_cves += 1
                for res in re.finditer('/commit/[^\s]*', data):
                    bug_id = res.group(0).replace('/commit/', '')
                    # if bug_id in cves:
                    #     cves[bug_id].append(cve)
                    # else:
                    #     cves[bug_id] = [cve]

    repo_node = ET.fromstring(xml_text)
    print(len(cves))
    print(unique_cves)
    repo = RepoMining(repo_node, True, 'wireshark')
    #repo.map_to_list(repo, cves, 'TypeCVEID')

   # repo = RepoMining(repo_node, False, 'wireshark')
    #repo = RepoMining(repo_node, False, 'ffmpeg')
    repo.map_to_list(repo, cves, 'DebianSecurityTracker')

