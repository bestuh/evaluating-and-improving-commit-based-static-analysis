import mysql.connector
import datetime
import warnings
from RepositoryMining.CommitMappingClass import CommitMapping
from mysql.connector.errors import IntegrityError

config = {
    'user': 'mbrack',
    'password': 'GK4zNrqK',
    'host': '130.83.163.37',
    'database': 'vcc',
}


class DBRepository:
    """Class that abstracts DB Operations"""

    def __init__(self):
        self.cnx = mysql.connector.connect(auth_plugin='mysql_native_password', **config)
        self.connection_closed = False

    def save_fixing_commit(self, mapping: CommitMapping, config_code: str) -> None:
        """Inserts a commit entry into the DB and creates a link to a CVE, according to the provided mapping"""
        if self.connection_closed:
            self.__open()

        cursor = self.cnx.cursor()
        insert = '''INSERT INTO commit (com_sha, com_config_code)
SELECT * FROM (SELECT %(com_sha)s, %(com_config_code)s) AS tmp
WHERE NOT EXISTS (
    SELECT com_sha, com_config_code FROM commit WHERE com_sha = %(com_sha)s AND com_config_code =  %(com_config_code)s
) LIMIT 1'''
        cursor.execute(insert, {'com_sha': mapping.id, 'com_config_code': config_code})

        update = '''UPDATE commit
SET com_date_commited = %(com_date)s
, com_author = %(com_author)s
, com_message = %(com_message)s
WHERE com_sha = %(com_sha)s AND com_config_code =  %(com_config_code)s'''

        update_data = {'com_date': mapping.commit.committed_datetime
            , 'com_author': mapping.commit.author.name
            , 'com_message': mapping.commit.message[:5000]
            , 'com_sha': mapping.id
            , 'com_config_code': config_code
                       }
        cursor.execute(update, update_data)

        link_insert = '''INSERT INTO link_cve_fixing_commit (cve_id, com_sha, com_config_code, mapping_type)
SELECT * FROM (SELECT %(cve_id)s, %(com_sha)s, %(config_code)s, %(mapping_type)s) AS tmp
WHERE NOT EXISTS (
    SELECT cve_id, com_sha, com_config_code  FROM link_cve_fixing_commit 
    WHERE com_sha = %(com_sha)s AND com_config_code = %(config_code)s AND cve_id = %(cve_id)s
) LIMIT 1;
'''

        for cve in mapping.cves:
            try:
                cursor.execute(link_insert, {'cve_id': cve, 'com_sha': mapping.id, 'config_code': config_code
                                             , 'mapping_type': mapping.mapping_type})
            except IntegrityError as e:
                print('Mapping could not be added! {0} not in DB \r\n{1}'.format(cve, e) )

        self.cnx.commit()
        cursor.close()

    def save_cve(self, cve:dict, config_code:str) -> None:
        """Inserts a CVE entry into the DB
            cve:parameter is expected in format of the CVE-search tool"""
        if self.connection_closed:
            self.__open()
        cursor = self.cnx.cursor()
        try:
            insert = '''INSERT INTO cve (cve_id)
    SELECT * FROM (SELECT %(cve_id)s) AS tmp
    WHERE NOT EXISTS (
        SELECT cve_id FROM cve WHERE cve_id = %(cve_id)s
    ) LIMIT 1;'''
            cursor.execute(insert, {'cve_id': cve['id']})

            update = '''UPDATE cve
    SET cve_date_created = %(cve_created)s
    , cve_date_last_modified = %(cve_modified)s
    , cve_cwe_id = %(cwe_id)s
    , cve_cvss_score = %(cvss_score)s
    , cve_cvss_time = %(cvss_time)s
    , cve_cvss_vector = %(cvss_vector)s
    , cve_summary = %(cve_summary)s
    WHERE cve_id = %(cve_id)s'''

            update_data = {'cve_id': cve['id']
                           , 'cve_created': cve.get('Published')
                           , 'cve_modified': cve.get('Modified')
                           , 'cvss_score': cve['cvss']
                           , 'cvss_time': cve.get('cvss-time')
                           , 'cvss_vector': cve.get('cvss-vector')
                           , 'cve_summary': cve.get('summary')
                           , 'cwe_id': cve['cwe']
                           }

            cursor.execute(update, update_data)

            self.save_references(cursor, cve)
            self.save_vul_product(cursor, cve)
            self.save_config_code(cursor, cve, config_code)

            self.cnx.commit()
        except Exception as e:
            warnings.warn("CVE {0} could not be saved - {1}".format(cve['id'], str(e)))
        cursor.close()

    @staticmethod
    def save_references(cursor, cve):
        delete = '''DELETE FROM cve_references WHERE cve_id = %(cve_id)s'''
        cursor.execute(delete, {'cve_id': cve['id']})

        insert = '''INSERT INTO cve_references (cve_id, reference) VALUES (%s, %s)'''
        data = list([(cve['id'], x) for x in cve['references']])# Create a list of tuples
        cursor.executemany(insert, data)

    @staticmethod
    def save_vul_product(cursor, cve):
        delete = '''DELETE FROM cve_product WHERE cve_id = %(cve_id)s'''
        cursor.execute(delete, {'cve_id': cve['id']})

        insert = '''INSERT INTO cve_product (cve_id, product) VALUES (%s, %s)'''
        data = list([(cve['id'], x) for x in cve['vulnerable_product']])# Create a list of tuples
        cursor.executemany(insert, data)

    @staticmethod
    def save_config_code(cursor, cve, config_code):
        insert = '''INSERT INTO cve_config_code (cve_id, config_code)
SELECT * FROM (SELECT %(cve_id)s, %(config_code)s) AS tmp
WHERE NOT EXISTS (
    SELECT cve_id, config_code FROM cve_config_code WHERE cve_id = %(cve_id)s AND config_code = %(config_code)s
) LIMIT 1;'''
        cursor.execute(insert, {'cve_id': cve['id'], 'config_code': config_code})

    def close(self):
        """Closes the current cursor"""
        self.cnx.close()
        self.connection_closed = True

    def __open(self):
        """Opens a new cursor for execution"""
        self.cnx = mysql.connector.connect(auth_plugin='mysql_native_password', **config)

