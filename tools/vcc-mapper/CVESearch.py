import re
import sys
from pymongo import MongoClient
#from RepositoryMining.RepoInspection import find_from_list
import warnings
from Utility.util import ConfigParse
from db_repository import DBRepository

config = {}

#Chrome
config['Chrome'] = ['google:chrome', [r'https://crbug.com/\d{1,6}', r'http://crbug.com/\d{1,6}', r'https://bugs.chromium.org/p/chromium/issues/detail\?id=\d{1,6}', r'http://bugs.chromium.org/p/chromium/issues/detail\?id=\d{1,6}', r'https://code.google.com/p/chromium/issues/detail\?id=\d{1,6}', r'http://code.google.com/p/chromium/issues/detail\?id=\d{1,6}', r'http://bugs.chromium.org/\d{1,6}', r'https://bugs.chromium.org/\d{1,6}']]
#----------------------------------------------------------------------
#Firefox
config['Firefox'] = ['mozilla:firefox', [r'https://bugzilla.mozilla.org/show_bug.cgi\?id=\d{1,7}']]
#----------------------------------------------------------------------
#Webkit
config['Webkit'] = ['webkit', [r'https://bugs.webkit.org/show_bug.cgi\?id=\d{1,7}']]
#----------------------------------------------------------------------
#Linux
config['Linux'] = ['linux:linux_kernel', [r'test']]
#----------------------------------------------------------------------
#OpenBSD
config['OpenBSD'] = ['openbsd:openbsd', [r'https://github.com/openbsd/src/commit/[^\s]+']]
#---------------------------------------------------------------------
#Wordpress
config['Wordpress'] = ['wordpress:wordpress', [r'https://core.trac.wordpress.org/ticket/\d{1,6}']] #, r'https://core.trac.wordpress.org/changeset/\d{1,6}']]
#--------------------------------------------------------------------
#Apache
config['Apache'] = ['apache:http_server', [r'http://svn.apache.org/viewvc/httpd/httpd/[^\s]+']]# ['https://bz.apache.org/bugzilla/show_bug.cgi\?id=\d{1,5}']]
#--------------------------------------------------------------------
#Nginx
config['Nginx'] = ['nginx:nginx', [r'https://trac.nginx.org/nginx/ticket/\d{1,4}']]
#--------------------------------------------------------------------
#Mysql
config['Mysql'] = ['oracle:mysql', [r'[^\s]']]

#-------------------------------------------------------------------
#Postgresql
config['Postgresql'] = ['postgresql:postgresql', [r'[^\s]']]

#-------------------------------------------------------------------
#MongoDB
config['Mongodb'] = ['mongodb:mongodb', [r'[^\s]+']]

#------------------------------------------------------------------

#FFmpeg
config['FFmpeg'] = ['ffmpeg:ffmpeg', [r'https://git.ffmpeg.org/gitweb/ffmpeg.git/commit/[^\s]+']]

#------------------------------------------------------------------
#Openssl
config['Openssl'] = ['openssl:openssl', [r'https://git.openssl.org/gitweb/\?p=openssl.git;a=commitdiff;h=[^\s]+']]

#----------------------------------------------------------------------
#Gnutls
config['Gnutls'] = ['gnu:gnutls', [r'https://gitlab.com/gnutls/gnutls/commit/[^\s]+']]

#---------------------------------------------------------------------
#Bcjava
config['Bcjava'] = ['bouncycastle:legion-of-the-bouncy-castle-java-crytography-api', [r'https://github.com/bcgit/bc-java/commit/[^\s]+']]

#----------------------------------------------------------------------
#Openjdk
config['Openjdk'] = ['openjdk', [r'https://bugs.openjdk.java.net/browse/JDK-\d{7}']]

#---------------------------------------------------------------------
#Coreclr
config['Coreclr'] = ['microsoft:microsoft.net_core', [r'[^\s]+']]

#-------------------------------------------------------------------
#Cpython
config['Cpython'] = ['python:python', [r'[^\s]+']]

#-------------------------------------------------------------------



if __name__ == "__main__":
    current_config = config[sys.argv[1]]
    cpe_regex = current_config[0]
    ref_regex = current_config[1]
   
    if(len(sys.argv) > 2):
       bug = False
    else:
        bug = True

    client = MongoClient()
    db = client.cvedb
    cve_collection = db.cves

    cves = cve_collection.find({'vulnerable_configuration': {"$regex": cpe_regex ,'$options': 'i'}})
    cve_list = {}
    total = 0
    mapped ={} 
    for cve in cves:
        cve_id = cve['id']
        total = total + 1
        bug_list = []
        for ref in cve['references']:
            for regex in ref_regex:
                regex_res = re.search(regex, ref)
                if regex_res:
                    mapped[cve_id] = True
                    #print (regex_res.group(0)) 
                    if bug:
                       bug_id = re.search(r'\d{1,7}', regex_res.group(0)).group(0)


                       #bug_id = regex_res.group(0)[len('https://github.com/openbsd/src/commit/'):]
                       #bug_list.append(bug_id)
                       if bug_id in cve_list:
                           cve_list[bug_id].append(cve_id)
                       else:
                           cve_list[bug_id] = [cve_id]

    print("{0} out out {1} CVES for {2} can be mapped to internal id".format(len(mapped), total,cpe_regex))
    #find_from_list(sys.argv[1], cve_list)


class CVESearch:

    def __init__(self, db, config_code):
        self.db = db
        if self.db:
            self.db_repo = DBRepository()
            self.config_code = config_code

    def get_cve_mappings(self, config_node):
        cpe_regex = config_node.find("./cpe").text
        print('Starting CVE search for CPE {0}...'.format(cpe_regex))

        client = MongoClient()
        db = client.cvedb
        cve_collection = db.cves
        cves = cve_collection.find({'vulnerable_configuration': {"$regex": cpe_regex, '$options': 'i'}})
        cve_list = {}
        total = 0
        mapped = {}
        for cve in cves:

            if self.db:
                self.db_repo.save_cve(cve, self.config_code)

            cve_id = cve['id']
            total = total + 1
            bug_list = []
            for ref in cve['references']:
                for regex_node in config_node.findall('./regex-list/regex'):
                    regex = regex_node.find('./contains').text
                    regex_res = re.search(regex, ref)
                    if regex_res:
                        mapped[cve_id] = True

                        bug_id_list = ConfigParse.id_extraktion(regex_node, regex_res.group(0))

                        for bug_id in bug_id_list:
                            if bug_id in cve_list:
                                cve_list[bug_id].append(cve_id)
                            elif bug_id is not None:
                                cve_list[bug_id] = [cve_id]


        print("{0} out out {1} CVES for {2} can be mapped to internal id".format(len(mapped), total,cpe_regex))

        if self.db:
            self.db_repo.close()

        return cve_list


    def get_cves(self, config_node):
        cpe_regex = config_node.find("./cpe").text
        print('Starting CVE search for CPE {0}...'.format(cpe_regex))

        client = MongoClient()
        db = client.cvedb
        cve_collection = db.cves
        cves = cve_collection.find({'vulnerable_configuration': {"$regex": cpe_regex, '$options': 'i'}})
        cve_list = {}

        for cve in cves:

            if self.db:
                self.db_repo.save_cve(cve, self.config_code)

            cve_id = cve['id']
            cve_list[cve_id] = cve_id

        print("{0} CVEs found".format(len(cve_list)))

        if self.db:
            self.db_repo.close()

        return cve_list



