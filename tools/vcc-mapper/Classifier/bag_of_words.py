from git import Repo, GitCommandError
import re
import sqlite3

conn = sqlite3.connect('commits.db')
c = conn.cursor()

repo = Repo("/home/rappy/Programs/Repos/linux")
c.execute("SELECT * FROM vccs")
vccs = c.fetchall()
c.execute("SELECT * FROM unclassified2")
unclassified = c.fetchall()

words = set()
with open("bag_of_words.txt", "a+") as bag_of_words:
	for indx, commit in enumerate(vccs+unclassified):
		print(str(indx)+"/"+str(len(vccs+unclassified)))
		commit = repo.commit(commit[0])

		if(len(commit.parents) > 1):
			print("Merge, skipping...")
			continue

		split_message = re.split("\s", commit.message)
		for word in split_message:
			if word not in words and word != "":
				words.add(word)
				bag_of_words.write('"'+word+'",')

		split_code = []
		for parent in commit.parents:
			diffs = parent.diff(commit, create_patch=True, unified=0)
			for diff in diffs:

				local_changes = str(diff).split("@@ -")
				del local_changes[0]
				for local_change in local_changes:
					added_code = ""
					deleted_code = ""
					for line in local_change.splitlines():
						if line != "" and line != "---":
							if line[0] == "+":
								added_code += line[1:]+"\n"
								for word in re.split('[\s\+\-\*\/,;><=()\[\]\{\}]', line):
									if word not in words and word != "":
										words.add(word)
										bag_of_words.write('"'+word+'",')
							elif line[0] == "-":
								deleted_code += line[1:]+"\n"
								for word in re.split('[\s\+\-\*\/,;><=()\[\]\{\}]', line):
									if word not in words and word != "":
										words.add(word)
										bag_of_words.write('"'+word+'",')
