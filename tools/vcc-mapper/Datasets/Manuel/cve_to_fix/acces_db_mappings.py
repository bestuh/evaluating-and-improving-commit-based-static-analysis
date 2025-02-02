# -*- coding: utf-8 -*-
import mysql.connector

config = {
        'user': 'mbrack',
        'password': 'GK4zNrqK',
        'host': '130.83.163.37',
        'database': 'vcc',
    }

config_codes = ["firefox", "chrome", "apachehttpd", "kernel", "openssl", "thunderbird", "wireshark", "ffmpeg", "postgres", "tcpdump"]

cnx = mysql.connector.connect(auth_plugin='mysql_native_password', **config)
cursor = cnx.cursor()

sql = """SELECT DISTINCT cve.cve_id, commit.com_sha, cve.cve_cwe_id, cve.cve_cvss_score, cve.cve_cvss_vector
FROM cve
INNER JOIN cve_config_code ON cve_config_code.cve_id = cve.cve_id
INNER JOIN link_cve_fixing_commit ON link_cve_fixing_commit.cve_id =  cve.cve_id and link_cve_fixing_commit.com_config_code = cve_config_code.config_code
INNER JOIN commit ON commit.com_sha = link_cve_fixing_commit.com_sha AND commit.com_config_code = link_cve_fixing_commit.com_config_code
WHERE cve_config_code.config_code = 'tcpdump' """ 

cursor.execute(sql)
mappings = cursor.fetchall()
with open("tcpdump_mappings.txt", "w+") as ff:
    for mapping in mappings:
        ff.write(mapping[0] + "  " + mapping[1]+"\n")
cnx.close()
