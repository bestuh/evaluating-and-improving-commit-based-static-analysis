from pymongo import MongoClient
import re
import sys
from pprint import pprint

def get_cves_from_debian(product):
    client = MongoClient()
    db = client.admin
    dla = db.dla
    dsa = db.dsa

    cves = {}

    cursor = dla.find({'packages': {"$regex": product, '$options': 'i'}})

    for item in cursor:
        for cve in item['secrefs'].split():
            if re.match(r'CVE-\d{4}-\d{4,7}', cve):
                cves[cve] = cve

    cursor = dsa.find({'packages': {"$regex": product, '$options': 'i'}})

    for item in cursor:
        for cve in item['secrefs'].split():
            if re.match(r'CVE-\d{4}-\d{4,7}', cve):
                cves[cve] = cve
    return cves


if __name__ == "__main__":
    product = sys.argv[1]
    cves = get_cves_from_debian()
    pprint(cves)