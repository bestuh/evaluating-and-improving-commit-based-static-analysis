import csv
from pymongo import MongoClient

path = 'firefox.csv'
if __name__ == '__main__':
    with open(path, 'r+') as f:
        with open('openssl_mapped.csv', 'w') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=';',
                                    quotechar='\'', quoting=csv.QUOTE_MINIMAL)
            spamwriter.writerow(['CVE', 'Fixing sha', 'Fixing date', 'VCC-heuristic sha', 'VCC-heuristic date', 'VCC-oldest sha', 'VCC-oldest date', 'VCC-newest sha', 'VCC-newest date', 'Average date', 'Weighted Average date', 'Heuristic Date', 'CWE', 'CVSS-score', 'cvss-vector'])

            for line in f.readlines()[1:]:
                splits = line.split(';')
                cve_id = splits[0]
                client = MongoClient()
                db = client.cvedb
                cve_collection = db.cves

                cves = cve_collection.find({'id': {"$regex": cve_id ,'$options': 'i'}})
                cve = cves[0]
                splits = splits[:-3]
                splits.extend([cve['cwe'], cve['cvss'], cve['cvss-vector']])
                spamwriter.writerow(splits)
