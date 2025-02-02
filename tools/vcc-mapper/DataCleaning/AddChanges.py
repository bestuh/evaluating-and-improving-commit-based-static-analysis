from RepositoryMining.RepoInspection import RepoMining
import xml.etree.ElementTree as ET
import mysql.connector
from tqdm import tqdm

config = {
    'user': 'mbrack',
    'password': 'GK4zNrqK',
    'host': '130.83.163.37',
    'database': 'vcc',
}

xml = {}
xml['postgres'] = '''<repo>
                <path>C:/Users/manue/Desktop/ThesisCode/Code/postgres</path>              
            </repo>'''
xml['ffmpeg'] = '''<repo>
                <path>C:/Users/manue/Desktop/ThesisCode/Code/FFmpeg</path>              
            </repo>'''
xml['openssl'] = '''<repo>
                <path>C:/Users/manue/Desktop/ThesisCode/Code/openssl</path>              
            </repo>'''

mappings = [
    ['CVE-2012-3488', 'postgres', 'adc97d03b92fef50608c21059f0509fa97d314f6'],
    ['CVE-2016-2326', 'ffmpeg', '7c0b84d89911b2035161f5ef51aafbfcc84aa9e2'],
    ['CVE-2010-1633', 'openssl', '3cbb15ee813453c52694c1d6f9a89eb7ae757943'],
    ['CVE-2016-1898', 'ffmpeg', 'ec4c48397641dbaf4ae8df36c32aaa5a311a11bf']
]
if __name__ == '__main__':
    #cnx = mysql.connector.connect(auth_plugin='mysql_native_password', **config)
    for item in mappings:

        repo_node = ET.fromstring(xml[item[1]])
        cves = {item[2]: [item[0]]}
        print(cves)
        repo = RepoMining(repo_node, True, item[1])
        repo.map_to_list(repo_node, cves, 'ManualInspection')