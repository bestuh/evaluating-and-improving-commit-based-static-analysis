from git import Repo
from tqdm import tqdm

def get_commits(repo_path, commit_ids):
    repo = Repo(repo_path)
    if repo.bare:
        raise Exception(f"Found bare repository under \"{repo_path}\"")
    print(f"Successfully loaded repository under \"{repo_path}\"")

    commits = []
    num_errors = 0
    print(f"Retrieving {len(commit_ids)} commits")
    for commit_id in tqdm(commit_ids):
        try:
            commits.append(repo.commit(commit_id))
        except Exception as e:
            print(e)
            num_errors = num_errors + 1
            continue
    
    error_msg = f"(error while fetching the {num_errors} remaining ones)" if num_errors > 0 else ""
    print(f"Retrieved {len(commits)}/{len(commit_ids)} commits {error_msg}")
    return commits