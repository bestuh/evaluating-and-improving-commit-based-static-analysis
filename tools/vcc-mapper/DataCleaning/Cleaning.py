import mysql.connector
import re

config = {
    'user': 'mbrack',
    'password': 'GK4zNrqK',
    'host': '130.83.163.37',
    'database': 'vcc',
}

if __name__ == "__main__":
    cnx = mysql.connector.connect(auth_plugin='mysql_native_password', **config)

    sql = """SELECT cve.cve_id, commit.com_config_code, commit.com_message, commit.com_sha
FROM cve
INNER JOIN cve_config_code ON cve_config_code.cve_id = cve.cve_id
INNER JOIN link_cve_fixing_commit ON link_cve_fixing_commit.cve_id = cve.cve_id AND link_cve_fixing_commit.com_config_code = cve_config_code.config_code
INNER JOIN commit ON commit.com_sha = link_cve_fixing_commit.com_sha AND commit.com_config_code = link_cve_fixing_commit.com_config_code
WHERE link_cve_fixing_commit.mapping_type = 'TypeCVEID'"""
    cursor = cnx.cursor()
    cursor.execute(sql)
    res = cursor.fetchall()
    cursor.close()

    count = 0

    with open('manual_inspection.txt', 'w+', encoding='UTF-8') as f:
        print('{0} mappings up for inspection'.format((len(res))))
        for item in res:
            cve = item[0]
            config_code = item[1]
            commit_message = item[2]
            commit_sha = item[3]

            regex_strings = [r'(F|f)ixes(:)?( )?', r'(S|s)ecurity(:)?( )', '(B|b)ug-(I|i))(|d)(:)?( )?']

            fits_regex = False
            for regex in regex_strings:

                search = re.search(regex + cve, commit_message)
                if search:
                    fits_regex = True
                    continue
            if fits_regex:
                continue
            count += 1
            f.write(cve + ' ' + config_code + ' ' + commit_sha + '' +'\r\n')
            f.write(commit_message+ '\r\n')
            f.write("______________________________________"+ '\r\n')

        print('{0} mappings left for manual inspection'.format(count))