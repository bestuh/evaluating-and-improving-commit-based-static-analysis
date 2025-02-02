import argparse
import warnings
import xml.etree.ElementTree as ET
from Database.db_repository import DBRepository
from git import Repo, Commit, BadName
import os
from Heuristics.VuldiggerHeuristic2 import VuldiggerHeuristic2
from Heuristics.VuldiggerHeuristic import VuldiggerHeuristic
from Heuristics.VccfinderHeuristicSerial import VccfinderHeuristicSerial
from typing import Dict, List
import csv
from pymongo import MongoClient
from tqdm import tqdm
from Utility.LifetimeEstimation import LifetimeEstimationHelper, ResultObject


config_path = './config.xml'

parser = argparse.ArgumentParser(description='Generate data files for vulnerability lifetime estimation.'
                                             'Default output write the csv to ./out/{configKey}.csv')
parser.add_argument('key', help='Product key in the config xml')

heuristics = ['vccfinder', 'vuldigger', 'vuldigger2']
parser.add_argument('-he', "--heuristic", required=True, type=str, choices=heuristics
                    , help='Specify the heuristic to use')

parser.add_argument('-c', "--config", type=str, help='Specify different config file')
parser.add_argument('-o', "--output", type=str, help='Specify different output file')
parser.add_argument('-j', "--java",  help='Set flag if the project is written in java', action='store_true')
parser.add_argument('-d', "--dsa",  help='Add boolean if the CVE is contained in the Debian security advisory. '
                                         'Requires a dla MongoDB to be running on the clinet', action='store_true')
parser.add_argument("-p", "--bar"
                    , help='Get a progressbar in the command line instead of a progress report every 100 mappings.'
                    , action='store_true')
parser.add_argument("-m", "--max-count", dest='maxcount', help="Limit the number of mappings", type=int)

parser.add_argument("-gt", "--ground-truth", dest='groundtruth'
                    , help="Specify a ground truth file. Check the readme for allowed configurations", type=str)

parser.add_argument("--delimiter", type=str, help="Specify a delimiter for the output csv file. Default is ';'")
parser.add_argument("--quote-char", dest='quotechar', type=str
                    , help="Specify a quotechar for the output csv file. Default is ' ")


args = parser.parse_args()

product_key = args.key
if args.config:
    config_path = args.config

if args.groundtruth:
    gt_path = args.groundtruth
else:
    gt_path = None

print('Loading config file...')

xml_root = ET.parse(config_path)

product_node = xml_root.find('.//product[@name=\'{0}\']'.format(product_key))

if product_node is None:
    raise ValueError('Product key \'{0}\' is not supported'.format(product_key))

out_path = f'./out/{product_key}.csv'

if args.output:
    out_path = args.output
else:
    if not os.path.exists('./out'):
        os.mkdir('./out')

if args.delimiter:
    delimiter = args.delimiter
else:
    delimiter = ';'

if args.quotechar:
    quotechar = args.quotechar
else:
    quotechar = '\''

if args.maxcount:
    maxcount = args.maxcount
else:
    maxcount = -1

repo_path = product_node.find('./mapping/repo/path').text

if not os.path.exists(repo_path):
    raise OSError(f'Repository path "{repo_path}" not found!')

repo = Repo(repo_path)
if repo.bare:
    raise Exception('Found bare repository under \'{0}\'!'.format(repo_path))

print('Successfully loaded repository at \'{0}\''.format(repo_path))

db_repo = DBRepository()

print('Starting Lifetime estimation...')

if args.heuristic == 'vuldigger2':
    heuristic = VuldiggerHeuristic2(repo, java=args.java)
    run_per_cve = True
elif args.heuristic == 'vuldigger':
    heuristic = VuldiggerHeuristic(repo, java=args.java)
    if args.java:
        warnings.warn('The chosen heuristic is not optimized for java and will therefore use c keywords and syntax!')
    run_per_cve = False
elif args.heuristic == 'vccfinder':
    heuristic = VccfinderHeuristicSerial(repo, java=args.java)
    run_per_cve = False
else:
    raise NotImplementedError(f'The heuristic {args.heuristic} is currently not supported')

if gt_path is not None:
    if not os.path.exists(gt_path):
        raise OSError(f'Ground truth path "{gt_path}" not found!')
    gt_mappings = LifetimeEstimationHelper.gt_mappings(gt_path, repo)
    print(f'{len(gt_mappings)} ground truth mappings loaded!')
    mappings = LifetimeEstimationHelper.annotate_cve_information(gt_mappings)

else:
    mappings = db_repo.get_mappings(product_key, maxcount)
    print(f'{len(mappings)} Mappings loaded from DB for {product_key}')

commit_mappings = LifetimeEstimationHelper.group_mappings(mappings)


with open(out_path, 'w+', newline='') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=delimiter,
                            quotechar=quotechar, quoting=csv.QUOTE_MINIMAL)
    header = ['CVE'
        , 'Fixing sha'
        , 'Fixing date'
        , 'VCC-heuristic sha'
        , 'VCC-heuristic date'
        , 'VCC-oldest sha'
        , 'VCC-oldest date'
        , 'VCC-newest sha'
        , 'VCC-newest date'
        , 'Average date'
        , 'Weighted Average date'
        , 'CWE'
        , 'CVSS-Score'
        , 'CVSS-Vector'
        , 'Commits heuristic'
        , 'Commmits newest'
        , 'Commits oldest'
        , 'Commits weighted'
        , 'Stable']
    if gt_path is not None:
        header.insert(3, 'VCC sha')
        header.insert(4, 'VCC date')
    spamwriter.writerow(header)

    if args.dsa:
        client = MongoClient()
        db = client.admin
        dla = db.dla
        dsa = db.dsa
    else:
        dsa = None

    count = 0

    if args.bar:
        if run_per_cve:
            pbar = tqdm(total=len(mappings), desc='Heuristic execution')
        else:
            pbar = tqdm(total=len(commit_mappings), desc='Heuristic execution')

    for commit_sha, cves in commit_mappings.items():

        try:
            fixing_commit = repo.commit(commit_sha)
        except ValueError:
            warnings.warn("Commit not found {0}".format(commit_sha))
            continue
        except BadName:
            warnings.warn("Commit not found {0}".format(commit_sha))
            continue

        if run_per_cve:
            for cve in cves:
                res = LifetimeEstimationHelper.run_and_calculate(heuristic, fixing_commit, repo, cve)
                if res is None:
                    count += 1
                    if args.bar:
                        pbar.update(1)
                    elif count % 100 == 0:
                        print(f'Heuristic execution: {count}/{len(mappings)}')
                    continue

                res.stable = LifetimeEstimationHelper.check_dsa_vulnerable(cve, args.dsa, dsa)
                LifetimeEstimationHelper.writeline(spamwriter, res, cve, gt=(gt_path is not None))

                count += 1
                if args.bar:
                    pbar.update(1)
                elif count % 100 == 0:
                    print(f'Heuristic execution: {count}/{len(mappings)}')
        else:
            res = LifetimeEstimationHelper.run_and_calculate(heuristic, fixing_commit, repo, None)
            if res is None:
                count += 1
                if args.bar:
                    pbar.update(1)
                elif count % 100 == 0:
                    print(f'Heuristic execution: {count}/{len(mappings)}')
                continue
            for cve in cves:
                res.stable = LifetimeEstimationHelper.check_dsa_vulnerable(cve, args.dsa, dsa)
                LifetimeEstimationHelper.writeline(spamwriter, res, cve, gt=(gt_path is not None))
            count += 1
            if args.bar:
                pbar.update(1)
            elif count % 100 == 0:
                print(f'Heuristic execution: {count}/{len(commit_mappings)}')

print(f'heuristic execution finished. Find your results under {out_path}')

