from pymongo import MongoClient
from db_repository import DBRepository
file = './in/missing_kernel_vuls_gt.txt'
if __name__ == '__main__':

    client = MongoClient()
    db = client.cvedb
    cve_collection = db.cves

    db_repo = DBRepository()

    with open(file, 'r') as f:
        for line in f.readlines():
            cve_id = line.replace('\r', '').replace('\n', '')

            cve = cve_collection.findOne({'id': {"$regex": cve_id, '$options': 'i'}})
            db_repo.save_cve(cve, 'kernel')
