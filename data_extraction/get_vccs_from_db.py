import argparse
import sys
sys.path.append("..")
import sql
import file_utils


parser = argparse.ArgumentParser()
parser.add_argument("-project", type=str, help="Name of the project (cve_config_code) to extract VCCs for. Use -list-projects to see a list of projects.")
parser.add_argument("-list-projects", action="store_true", help="See a list of projects.")
parser.add_argument("-threshold", default=50, type=int, help="Minimum number off VCC for a project to be considered.")
parser.add_argument("-include-heuristics", action="store_true", help="When enabled, heuristic-based VCCs will also be included.")
args = parser.parse_args()


def get_heuristics_filter(include_heuristics: bool):
    return f"""
        AND vcc.determined_by_heuristic = FALSE
        AND vcc.mapping_type != "VulnerabilityHistoryProject_automatic"
        AND vcc.mapping_type != "Syzkaller"
    """ if not include_heuristics else ""

def get_projects(threshold, include_heuristics=False):
    query = f"""
        SELECT vcc.vcc_config_code, COUNT(DISTINCT vcc_sha) AS num_vccs
        FROM `link_fixing_commit_vcc` vcc 
        WHERE vcc.vcc_sha IS NOT NULL
        {get_heuristics_filter(include_heuristics)}
        GROUP BY vcc.vcc_config_code HAVING (num_vccs >= {threshold}) 
        ORDER BY `num_vccs` DESC;
        ;
    """
    results = sql.query(query, database_name="vcc_mappings")
    projects = [row[0] for row in results]
    return projects


def get_vccs(project: str, heuristic=False):
    query = f"""
        SELECT vcc.vcc_sha AS commit_id, commit.com_date_committed AS date, GROUP_CONCAT(DISTINCT vcc.mapping_type) AS mapping_types
        FROM `link_fixing_commit_vcc` vcc 
        LEFT JOIN commit ON (commit.com_sha = vcc.vcc_sha)
        WHERE vcc.vcc_sha IS NOT NULL
        AND vcc.vcc_config_code = "{project}"
        AND commit.com_config_code = "{project}" 
        {get_heuristics_filter(heuristic)} 
        GROUP BY vcc.vcc_sha, commit.com_date_committed
        ORDER BY commit.com_date_committed DESC
        ;
    """
    results = sql.query(query, database_name="vcc_mappings")

    file_path = f"./vccs/{project}_vccs.csv"
    header = [["commit_sha", "commit_date", "sources"]]
    data = header + [list(row) for row in results]
    print(f"Writing {len(results)} commits to {file_path}")
    file_utils.write_csv(file_path, data)


if args.list_projects is True or args.project.lower() == "all":
    projects = get_projects(args.threshold, args.include_heuristics)

if args.list_projects is True:
    print(projects)
    exit()

if args.project.lower() == "all":
    print(f"Getting VCCs for {len(projects)} projects...")
    for project in projects:
        get_vccs(project, args.include_heuristics)
    exit()
elif args.project : 
    get_vccs(args.project, args.include_heuristics)