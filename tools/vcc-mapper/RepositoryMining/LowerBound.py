import re
from git import GitCommandError

class LowerBound():

    def use_heuristic(self, repo, commit):
        self.authored_date = 0
        self.vcc = None

        # diff with each parent. Merges might have multiple parents
        for parent in commit.parents:
            diffs = parent.diff(commit, create_patch=True, unified=0)

            for diff in diffs:

                local_changes = str(diff).split("@@ -")
                local_changes.pop(0)
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
                        self.blame(repo, parent, diff.a_path, deletion_anchor + i)

        return self.vcc

    def blame(self, repo, commit, path, line):
        try:
            blamed_commit = repo.blame(commit.hexsha, path, L=str(line)+",+1")[0][0]

            if blamed_commit.authored_date > self.authored_date:
                self.authored_date = blamed_commit.authored_date
                self.vcc = blamed_commit

        except GitCommandError:
            print('Blame unsuccessful, line does not exist')
