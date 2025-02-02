import re
import mysql.connector
from git import GitCommandError
from collections import defaultdict
from subprocess import check_output

config = {
    'user': 'mbrack',
    'password': 'GK4zNrqK',
    'host': '130.83.163.37',
    'database': 'vcc',
}

class OwnHeuristic():

    def use_heuristic(self, repo, commit, cve=None):
        frequencies_blames = defaultdict(set)
        
        # get cve details from cve-search
        try:
            sql = """SELECT cve.cve_cwe_id, cve.cve_summary FROM cve WHERE cve.cve_id = %s"""
            cnx = mysql.connector.connect(auth_plugin='mysql_native_password', **config)
            cursor = cnx.cursor()

            cursor.execute(sql, (cve,))
            mappings = cursor.fetchall()
            cnx.close()

            summary = mappings[0][1]
            cwe = mappings[0][0].split("-")[-1]
        except:
            print("Summary/Cwe not available for " + str(cve))
            summary = ""
            cwe = ""

        # diff with each parent. Merges might have multiple parents.
        blames_frequencies = {} 
        for parent in commit.parents:
            diffs = parent.diff(commit, create_patch=True, unified=0)

            for diff in diffs:
                # skip non code files
                if (not (self.is_code_file(diff.a_path) or self.is_code_file(diff.b_path))):
                    continue
                self.apply_heuristic(diff, repo, str(commit), str(parent), summary, blames_frequencies)

        # the number of how many times a commit was blamed is now the key
        if blames_frequencies:
            for blame, frequency in blames_frequencies.items():
                frequencies_blames[frequency].add(blame)
        else: return [blames_frequencies, cve, False]

        # decide whether we are confident in this mapping or not
        confident = False

        all_commits = len(blames_frequencies.keys()) 
        number_of_blames = sorted(frequencies_blames.keys(), reverse=True)
        top_blamed = frequencies_blames[max(frequencies_blames.keys())]

        total_blames = 0
        for count in frequencies_blames.keys():
            total_blames += count * len(frequencies_blames[count])

        if not (cwe in ["264"] or (len(top_blamed) > 1)):
            if len(number_of_blames) > 1:
                difference = number_of_blames[0] - number_of_blames[1]
                if (difference > total_blames/3) and (all_commits < 5):
                    confident = True
            else:
                confident = True

        return [blames_frequencies, cve, confident]


    def apply_heuristic(self, diff, repo, commit, parent, summary, blames_frequencies):
        
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
            try:
                deletion_offset = int(lines_and_offset.group(1).split(",")[1])
            except IndexError:
                deletion_offset = 1
    
            # fwr childs and parents version of the file
            if diff.a_path:
                parent_file = repo.git.show(parent + ":" + diff.a_path).splitlines()
            if diff.b_path:
                child_file = repo.git.show(commit + ":" + diff.b_path).splitlines()

            # Blame deletions
            for i in range(deletion_offset):
                self.blame(repo, parent, diff.a_path, deletion_anchor+i, blames_frequencies, weight)
    
            # Blame Additions
            try:
                addition_offset = int(lines_and_offset.group(2).split(",")[1])
                if addition_offset == 0:
                   continue
            except IndexError:
                addition_offset = 1

            # blame line before added code
            self.blame(repo, commit, diff.b_path, addition_anchor - 1, blames_frequencies, weight)
                
            # blame line after added code
            self.blame(repo, commit, diff.b_path, addition_anchor + addition_offset, blames_frequencies, weight)
    
    
    def blame(self, repo, commit, path, line, blames_frequencies, weight):
        try:
            blamed_commit = repo.blame(commit, path, L=str(line)+",+1", w=True)[0][0]

            if blamed_commit in blames_frequencies.keys():
                blames_frequencies[blamed_commit] += weight
            else:
                blames_frequencies[blamed_commit] = weight

        except GitCommandError:
            # blamed line does not exist
            pass

    def is_code_file(self, file):
        if file: return re.match('^.*\.(c|c\+\+|cpp|cc|h|hpp)$', file)
        return False
