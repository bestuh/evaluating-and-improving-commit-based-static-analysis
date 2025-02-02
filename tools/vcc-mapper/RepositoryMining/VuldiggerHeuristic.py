import re
from git import GitCommandError
import subprocess

class VuldiggerHeuristic():

    def use_heuristic(self, repo, commit, blames):

        # diff with each parent. Merges might have multiple parents
        for parent in commit.parents:
            diffs = parent.diff(commit, create_patch=True, unified=0)

            '''
            if (len(diffs) > 1):
                print("More than 1 file changed, skipping")
                continue
            '''

            a_path = None
            b_path = None
            for diff in diffs:
                if (not (is_code_file(diff.a_path) or is_code_file(diff.b_path))):
                    continue

                local_changes = str(diff).split("@@ -")
                del local_changes[0]
                for local_change in local_changes:
                    lines_and_offset = re.search(r'(.*?) \+(.*?) @@', local_change)
                    deletion_anchor = int(lines_and_offset.group(1).split(",")[0])
                    addition_anchor = int(lines_and_offset.group(2).split(",")[0])

                    if diff.a_path and diff.a_path != a_path:
                        old_file = repo.git.show(str(parent) + ":" + diff.a_path).splitlines()
                        old_comments_and_whitespaces = get_comments_and_whitespaces(old_file)
                        a_path = diff.a_path
                    if diff.b_path and diff.b_path != b_path:
                        new_file = repo.git.show(str(commit) + ":" + diff.b_path).splitlines()
                        new_comments_and_whitespaces = get_comments_and_whitespaces(new_file)
                        b_path = diff.b_path

                    try:
                        deletion_offset = int(lines_and_offset.group(1).split(",")[1])
                    except IndexError:
                        deletion_offset = 1

                    # Blame deletions
                    for i in range(deletion_offset):
                        line_number = deletion_anchor + i
                        try:
                            line_to_blame = old_file[line_number - 1].strip().rstrip() # -1 because line count starts with 1 not 0
                        except:
                            continue # if line does not exist continue

                        if ((deletion_anchor + i - 1) in old_comments_and_whitespaces):
                            # print("Skipping: " + line_to_blame)
                            continue

                        # print("Blaming: " + line_to_blame)
                        blame(repo, blames, parent, diff.a_path, line_number)

                    # Blame Additions
                    try:
                        addition_offset = int(lines_and_offset.group(2).split(",")[1])
                        if addition_offset == 0:
                            continue
                    except IndexError:
                        addition_offset = 1

                    line_number = addition_anchor - 1
                    try:
                        line_to_blame_around = new_file[line_number]
                    except:
                        line_to_blame_around = None

                    # single line insertion
                    if (addition_offset == 1):
                        keywords = ['if', 'else', 'goto', 'return', 'sizeof', 'break', 'NULL']
                        contains_keyword = False
                        if line_to_blame_around:
                            for word in keywords:
                                # Check for keywords
                                if (word in line_to_blame_around):
                                    contains_keyword = True
                                    break
                            # Check for function calls
                            if re.findall(r'[a-zA-Z_][a-zA-Z_0-9$]*\(.*?\)', line_to_blame_around):
                                contains_keyword = True
                            if (not contains_keyword):
                                # print("Skipping: " + line_to_blame_around)
                                continue
                            # else:
                                # print("Blaming: " + line_to_blame_around)
                                # blame(repo, blames, commit, diff.b_path, line_number + 1)
                    else:
                        try:
                            three_lines = line_to_blame_around+new_file[line_number+1]+new_file[line_number+2]
                        except:
                            try:
                                three_lines = line_to_blame_around+new_file[line_number+1]
                            except:
                                three_lines = line_to_blame_around

                        three_lines = three_lines.strip().rstrip()
                        if re.match(r'(static)?[ \t]*(inline)?[ \t]*[a-zA-Z_][a-zA-Z_0-9$]+[ \t]+[a-zA-Z_][a-zA-Z_0-9$]+\(.+\)[ \t]*{', three_lines):
                            # print("Inserted function, skipping: ", three_lines)
                            continue

                    # block insertion
                    before_block = line_number
                    after_block = addition_anchor + addition_offset
                    if before_block > 0 and not (before_block-1 in new_comments_and_whitespaces):
                        # print("Blaming: ", new_file[before_block-1])
                        blame(repo, blames, commit, diff.b_path, before_block)
                    # else:
                        # print("2 Skipping: ", new_file[before_block-1])

                    # blame line after
                    if not (after_block-1 in new_comments_and_whitespaces):
                        # print("Blaming: ", new_file[after_block-1])
                        blame(repo, blames, commit, diff.b_path, after_block)
                    # else:
                        # print("Skipping: ", new_file[after_block-1])

def is_code_file(file):
    if file:
        return re.match('^.*\.(c|c\+\+|cpp|h|hpp|php|cc)$', file) and (not "test" in file.lower()) #('^.*\.(c|c\+\+|cpp|h|hpp|php)$', file)
    return False

def blame(repo, blames, commit, path, line):
    try:
        blamed_commits = repo.blame(commit.hexsha, path, L=str(line)+",+1", w=True)    #, M=True, w=True, C=True
        for blamed_commit in blamed_commits[0][:int((len(blamed_commits[0])/2))]:
                if blamed_commit.hexsha in blames:
                    blames[blamed_commit.hexsha][0] += 1
                else:
                    blames[blamed_commit.hexsha] = [1, blamed_commit]
    except GitCommandError:
        print('Blame unsuccessful, line does not exist')
    except KeyError as e:
        print('Key error during blame: {}'.format(str(e)))

def get_comments_and_whitespaces(altered_file):
    comments_and_whitespaces = []
    comment = False
    for line_number, line in enumerate(altered_file):
        # Check for single line comments or empty lines
        stripped_line = line.strip().rstrip()
        if (stripped_line == '' or stripped_line[:2] == '//'):
            comments_and_whitespaces.append(line_number)

        contains_code = not (comment or stripped_line[:2] == "/*")

        for indx, l in enumerate(stripped_line[:-1]):
            ll = l + stripped_line[indx+1]
            if (ll == '/*'):
                comment = True
            if (ll == '*/'):
                comment = False
                if not (indx == len(stripped_line) - 2):
                    contains_code = True

        if not contains_code:
            comments_and_whitespaces.append(line_number)
    return comments_and_whitespaces
