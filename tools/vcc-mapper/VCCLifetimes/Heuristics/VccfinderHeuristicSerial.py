import re
from git import GitCommandError
from .HeuristicInterface import HeuristicInterface


class VccfinderHeuristicSerial(HeuristicInterface):

    def use_heuristic(self, commit, cve):

        blames_frequencies = {}
        # diff with each parent. Merges might have multiple parents
        for parent in commit.parents:
            diffs = parent.diff(commit, create_patch=True, unified=0)

            for diff in diffs:
                # Skip non code files
                if not (self.is_code_file(diff.a_path) or self.is_code_file(diff.b_path)):
                    continue

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
                        self.blame(blames_frequencies, parent, diff.a_path, deletion_anchor + i)

                    # Blame Additions
                    try:
                        addition_offset = int(lines_and_offset.group(2).split(",")[1])
                        if addition_offset == 0:
                            continue
                    except IndexError:
                        addition_offset = 1

                    # blame line before
                    if addition_anchor - 1 > 0:
                        self.blame(blames_frequencies, commit, diff.b_path, addition_anchor-1)

                    # blame line after
                    self.blame(blames_frequencies, commit, diff.b_path, addition_anchor + addition_offset)
        return blames_frequencies

    def blame(self, blames, commit, path, line):
        try:
            blamed_commit = self.repo.blame(commit.hexsha, path, L=str(line)+",+1")[0][0]
            if blamed_commit in blames:
                blames[blamed_commit] += 1
            else:
                blames[blamed_commit] = 1
        except GitCommandError:
            print('Blame unsuccessful, line does not exist')
