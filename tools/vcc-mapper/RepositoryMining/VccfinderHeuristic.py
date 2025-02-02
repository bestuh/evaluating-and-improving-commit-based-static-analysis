import re
from git import GitCommandError, Repo
from multiprocessing import Pool, Manager
import sys
from collections import defaultdict

sys.setrecursionlimit(1000000)

class VccfinderHeuristic():

    def use_heuristic(self, repo, commit, blames):
        # diff with each parent. Merges might have multiple parents
        for parent in commit.parents:
            diffs = parent.diff(commit, create_patch=True, unified=0)

            manager = Manager()
            blame_list = manager.list()
            p = Pool() #(processes=8)
            for diff in diffs:
                apply_heuristic(diff, repo, str(commit), str(parent), blame_list, p)
            p.close()
            p.join()

            if blame_list:
                for blamed_commit in blame_list:
                    if blamed_commit in blames:
                        blames[blamed_commit] += 1
                    else:
                        blames[blamed_commit] = 1

        new_blames = defaultdict(list)
        for commit, frequency in blames.items():
            new_blames[frequency].append(commit)

        return new_blames



def log_e(e):
  print(e)


def apply_heuristic(diff, repo, commit, parent, blame_list, p):
    # Skip non code files
    if (not (is_code_file(diff.a_path) or is_code_file(diff.b_path))):
       return

    local_changes = str(diff).split("@@ -")
    del local_changes[0]
    for local_change in local_changes:
        lines_and_offset = re.search(r'(.*?) \+(.*?) @@', local_change)
        deletion_anchor = int(lines_and_offset.group(1).split(",")[0])
        addition_anchor = int(lines_and_offset.group(2).split(",")[0])
        try:
            deletion_offset = int(lines_and_offset.group(1).split(",")[1])
        except IndexError:
            deletion_offset = 1

        # Blame deletions

        for i in range(deletion_offset):
           blame(repo, parent, diff.a_path, deletion_anchor + i, blame_list)

        # Blame Additions
        try:
            addition_offset = int(lines_and_offset.group(2).split(",")[1])
            if addition_offset == 0:
               continue
        except IndexError:
            addition_offset = 1

        # blame line before
        if addition_anchor - 1 > 0:
            blame(repo, commit, diff.b_path, addition_anchor - 1, blame_list)
        # blame line after
        blame(repo, commit, diff.b_path, addition_anchor + addition_offset, blame_list)


def is_code_file(file):
    if file: return re.match('^.*\.(c|c\+\+|cpp|h|hpp|cc)$', file)
    return False

def blame(repo, commit, path, line, blames):
    try:
        blamed_commits = repo.blame(commit, path, L=str(line)+",+1", w=True)    #, M=True, w=True, C=True
        for blamed_commit in blamed_commits[0][:int((len(blamed_commits[0])/2))]:
            if blamed_commit.hexsha in blames:
                blames[blamed_commit.hexsha][0] += 1
            else:
                blames[blamed_commit.hexsha] = [1, blamed_commit]
    except GitCommandError:
        print('Blame unsuccessful, line does not exist')
