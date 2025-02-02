from git import Repo, GitCommandError
import subprocess
import re
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

class BagOfWords:

	def __init__(self):
		self.count_vect = CountVectorizer(stop_words="english")
		self.add_vect = CountVectorizer(stop_words=["+", "-", "*", "/", ",", ";", ">", "<", "=", "(", ")", "[", "]", "{", "}"])
		self.del_vect =  CountVectorizer(stop_words=["+", "-", "*", "/", ",", ";", ">", "<", "=", "(", ")", "[", "]", "{", "}"])
		self.add_transformer = TfidfTransformer()
		self.del_transformer = TfidfTransformer()
		self.message_transformer = TfidfTransformer()

		'''		
		vul_path = "../Datasets/Training/"
		messages = "" 
		added_code = ""
		deleted_code = ""
		messages = open("messages.txt", "a+")
		additions = open("additions.c", "a+")
		deletions = open("deletions.c", "a+")
		
		
		repos = ["linux", "httpd", "chromium"]
		for repo_indx, path in enumerate(["../Datasets/Training/kernel_old.txt", "../Datasets/Training/httpd_vuls.txt", "../Datasets/Training/chromium_vuls.txt"]):
			with open(path, "r+") as p:
				
				repo = Repo("/home/rappy/Programs/Repos/"+repos[repo_indx])
				commits = p.readlines()
				commits = list(set(commits))
		
				for commit in commits:
					count = 0
					adds = ""
					dels = ""
					commit = commit.split("  ")[0][-40:]
					try:
						commit = repo.commit(commit)
					except:
						print("Couldn't find commit.")
						continue

		
					if(len(commit.parents) > 1):
						print("Merge, skipping...")
						continue
		
					split_code = []
					for parent in commit.parents:
						diffs = parent.diff(commit, create_patch=True, unified=0)
		
						for diff in diffs:
							# skip non code files
							if (not (is_code_file(diff.a_path) or is_code_file(diff.b_path))):
								continue
		
							try:
								old_file = repo.git.show(str(parent) + ":" + diff.a_path).splitlines()
								old_comments = get_comments(old_file)
							except:
								pass
		
							try:
								new_file = repo.git.show(str(commit) + ":" + diff.b_path).splitlines()
								new_comments = get_comments(new_file)
							except:
								pass
		
							local_changes = str(diff).split("@@ -")
							del local_changes[0]
							for local_change in local_changes:
								deleted_code = ""
								comment = False
								for line in local_change.splitlines():
									if line != "" and line != "---":
										if line[0] == "+":
											count += 1
											adds += line[1:]+"\n"
										elif line[0] == "-":
											count += 1
											dels += line[1:]+"\n"

					if count > 2000:
						continue
					additions.write(adds)
					deletions.write(dels)
					messages.write(commit.message + "\n")
		additions.close()
		deletions.close()
		messages.close()
		
		subprocess.call(["./remove_comments.sh", "additions"])
		subprocess.call(["./remove_comments.sh", "deletions"])
		'''
		
		with open("BagOfWords/additions.txt", "r+") as m:
			add_counts = self.add_vect.fit_transform(m)
			self.add_transformer.fit_transform(add_counts)
		
		with open("BagOfWords/deletions.txt", "r+") as m:
			del_counts = self.del_vect.fit_transform(m)
			self.del_transformer.fit_transform(del_counts)
		
		with open("BagOfWords/messages.txt", "r+") as m:
			message_counts = self.count_vect.fit_transform(m)
			self.message_transformer.fit_transform(message_counts)

	def get_add_vect(self, additions):
		new_add_counts = self.add_vect.transform(additions)
		return self.add_transformer.transform(new_add_counts)

	def get_del_vect(self, deletions):
		new_del_counts = self.del_vect.transform(deletions)
		return self.del_transformer.transform(new_del_counts)

	def get_message_vect(self, additions):
		new_message_counts = self.count_vect.transform(additions)
		return self.message_transformer.transform(new_message_counts)



def is_code_file(file):
    if file:
        return re.match('^.*\.(c|c\+\+|cpp|h|hpp|cc)$', file) #('^.*\.(c|c\+\+|cpp|h|hpp|php)$', file)
    return False
	
	