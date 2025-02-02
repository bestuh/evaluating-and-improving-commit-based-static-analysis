import re
from collections import defaultdict
from git import GitCommandError
from .HeuristicInterface import HeuristicInterface


class VuldiggerHeuristic2(HeuristicInterface):

    def __init__(self, repo, java=False):
        if java:
            self.keywords = ['if', 'else', 'return', 'break', 'null']
            self.function_declaration_re = \
                r'(public|private|protected|static|final|native|synchronized|abstract|transient)' \
                r'\s+[\w\<\>\[\]]+\s+(\w+) *\([^\)]*\) *(\{?|[^;])'
        else:
            self.keywords = ['if', 'else', 'goto', 'return', 'sizeof', 'break', 'NULL']
            self.function_declaration_re = r'\s*(?:(?:inline|static)\s+){0,2}\w+\s+\*?\s*\w+\s*\([^!@#$+%^;]+?\)\s*\{'

    def use_heuristic(self, commit, cve: dict = None):

        # get cve data from database
        if cve is not None and 'summary' in cve:
            summary = cve['summary']
        else:
            summary = ""
        if cve is not None and 'cwe' in cve:
            cwe = cve['cwe']
        else:
            cwe = ""

        blames_frequencies = {}
        
        first_parent = commit.parents[0] # in case of merge commit, diffing first parent makes most sense
        diffs = first_parent.diff(commit, create_patch=True, unified=0)

        for diff in diffs:
            # skip non code files
            if not (self.is_code_file(diff.a_path) or self.is_code_file(diff.b_path)):
                continue
            self.apply_heuristic(diff, commit, first_parent, summary, blames_frequencies)

        return blames_frequencies

    def apply_heuristic(self, diff, commit, parent, summary, blames_frequencies):

        # parse diff
        local_changes = str(diff).split("@@ -")
        del local_changes[0]
        for local_change in local_changes:
            weight = 1

            altered_function = re.search('\s([^ ]*)\(', local_change.splitlines()[0])
            if altered_function:
                if altered_function.group(1).lower() in summary.lower():
                    weight = 3 

            lines_and_offset = re.search(r'(.*?) \+(.*?) @@', local_change)
            deletion_anchor = int(lines_and_offset.group(1).split(",")[0])
            addition_anchor = int(lines_and_offset.group(2).split(",")[0])

            if diff.a_path:
                parent_file = self.repo.git.show(parent.hexsha + ":" + diff.a_path).splitlines()
                parent_comments_and_whitespaces = self.get_comments_and_whitespaces(parent_file)
            if diff.b_path:
                child_file = self.repo.git.show(commit.hexsha + ":" + diff.b_path).splitlines()
                child_comments_and_whitespaces = self.get_comments_and_whitespaces(child_file)

            try:
                deletion_offset = int(lines_and_offset.group(1).split(",")[1])
            except IndexError:
                deletion_offset = 1

            # Blame deletions
            for i in range(deletion_offset):
                line_number = deletion_anchor + i

                # check if deleted line was comment/whitespace
                if (deletion_anchor + i - 1) in parent_comments_and_whitespaces:
                    continue

                # blame deleted line
                self.blame(parent, diff.b_path, line_number, blames_frequencies, weight)

            # Blame Additions
            try:
                addition_offset = int(lines_and_offset.group(2).split(",")[1])
                if addition_offset == 0:
                    # no addition in locale change
                    continue
            except IndexError:
                addition_offset = 1
            
            line_number = addition_anchor - 1
            line = child_file[line_number]

            if addition_offset == 1:
                # single line addition
                # Check for keywords
                contains_keyword_or_function_call = False
                for word in self.keywords:
                    if word in line:
                        contains_keyword_or_function_call = True
                        break
                # Check for function calls
                if re.findall(r'[a-zA-Z_][a-zA-Z_0-9$]*\(.*?\)', line):
                    contains_keyword_or_function_call = True

                if not contains_keyword_or_function_call:
                    continue
            else:
                # multi line addition
                # check if added code block is function declaration
                three_lines = ''.join(child_file[line_number:line_number+3]).strip().rstrip()
                if re.match(self.function_declaration_re, three_lines):
                    continue

            before_addition = line_number
            after_addition = addition_anchor + addition_offset
            # blame line before added code
            if before_addition > 0 and not (before_addition-1 in child_comments_and_whitespaces):
                self.blame(commit, diff.b_path, before_addition, blames_frequencies, weight)
            # blame line after added code
            if not (after_addition-1 in child_comments_and_whitespaces):
                self.blame(commit, diff.b_path, after_addition, blames_frequencies, weight)

    def blame(self, commit, path, line_number, blames_frequencies, weight):
        try:
            blamed_commit = self.repo.blame(commit, path, L=str(line_number)+",+1", w=True)[0][0]
            if blamed_commit in blames_frequencies.keys():
                blames_frequencies[blamed_commit] += weight
            else:
                blames_frequencies[blamed_commit] = weight
        except GitCommandError:
            # line doesn't exist
            pass

    @staticmethod
    def get_comments_and_whitespaces(file):
        comments_and_whitespaces = []
        comment = False
        for line_number, line in enumerate(file):
            # Check for single line comments or empty lines
            stripped_line = line.strip().rstrip()
            if stripped_line == '' or stripped_line[:2] == '//':
                comments_and_whitespaces.append(line_number)

            contains_code = not (comment or stripped_line[:2] == "/*")
            for indx, l in enumerate(stripped_line[:-1]):
                ll = l + stripped_line[indx+1]
                if ll == '/*':
                    comment = True
                if ll == '*/':
                    comment = False
                    if not (indx == len(stripped_line) - 2):
                        contains_code = True

            if not contains_code:
                comments_and_whitespaces.append(line_number)
        return comments_and_whitespaces
