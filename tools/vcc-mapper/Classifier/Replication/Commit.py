from git import Repo, GitCommandError
import numpy as np
import re
from scipy.sparse import csc_matrix, save_npz
import math
import time

class Commit:

	def __init__(self, repo_path, commit):

		#load repo
		self.repo = Repo(repo_path)
		if self.repo.bare:
			raise Exception('Found bare repository under \'{0}\'!'.format(path))

		# load bag of words
		self.bag_of_words = {}
		with open("bag_of_words.txt", "r+", encoding="utf8") as b:
			for word in b.read().split('\n'):
				self.bag_of_words[word] = 0

		# load commit
		self.commit = self.repo.commit(commit)

		# skip merge commits
		if (len(self.commit.parents) > 1):
			raise ValueError("Merge commit, skipping", str(self.commit))

		# initialize features
		self.past_different_authors = 0
		self.additions = 0
		self.deletions = 0
		self.past_changes = 0
		self.hunk_count = 0
		self.commit_count = 0
		self.added_functions = 0
		self.deleted_functions = 0
		self.authored_date = 0
		self.contributions_percent = 0.0
		self.repo_creation_date = 0
		self.unique_contributors = 0
		self.star_count = 0
		self.fork_count = 0

		# extract features
		skip = self.get_features()
		if skip == 0: return

		# create feature vector
		self.create_feature_vector()


	def get_features(self):

		features = []
				
		# feature: authored date
		self.authored_date = self.commit.authored_date
		# feature: commit message
		self.commit_message = self.commit.message

		# feature: commit count
		self.commit_count = 901253
		# feature: unique contributors
		self.unique_contributors = 23978
		# feature: repo creation date
		self.repo_creation_date = 1113690036
		self.fork_count = 306000
		self.star_count = 875000

		# keywords
		self.added_code = ""
		self.deleted_code = ""
		self.keywords = {
			"auto" : 0,
			"break" : 0,
			"case" : 0,
			"char" : 0,
			"const" : 0,
			"continue" : 0,
			"default" : 0,
			"do" : 0,
			"double" : 0,
			"else" : 0,
			"enum" : 0,
			"extern" : 0,
			"float" : 0,
			"for" : 0,
			"goto" : 0,
			"if" : 0,
			"int" : 0,
			"long" : 0,
			"register" : 0,
			"return" : 0,
			"short" : 0,
			"signed" : 0,
			"sizeof" : 0,
			"static" : 0,
			"struct" : 0,
			"switch" : 0,
			"typedef" : 0,
			"union" : 0,
			"unsigned" : 0,
			"void" : 0,
			"volatile" : 0,
			"while" : 0,
			"asm" : 0,
			"dynamic_cast" : 0,
			"namespace" : 0,
			"reinterpret_cast" : 0,
			"try" : 0,
			"bool" : 0,
			"explicit" : 0,
			"new" : 0,
			"static_cast" : 0,
			"typeid" : 0,
			"catch" : 0,
			"false" : 0,
			"operator" : 0,
			"template" : 0,
			"typename" : 0,
			"class" : 0,
			"friend" : 0,
			"private" : 0,
			"this" : 0,
			"using" : 0,
			"const_cast" : 0,
			"inline" : 0,
			"public" : 0,
			"throw" : 0,
			"virtual" : 0,
			"delete" : 0,
			"mutable" : 0,
			"protected" : 0,
			"true" : 0,
			"wchar_t" : 0,
			"malloc" : 0,
			"calloc" : 0,
			"realloc" : 0,
			"free" : 0,
			"alloca" : 0,
			"allocinteger" : 0
		}

		# handle initial commit
		if len(self.commit.parents) == 0:
			self.commit.parents = [repo.tree("4b825dc642cb6eb9a060e54bf8d69288fbee4904")]

		files = set()
		for parent in self.commit.parents:
			diffs = parent.diff(self.commit, create_patch=True, unified=0)

			for diff in diffs:
				files.add(diff.a_path) if diff.a_path else files.add(diff.b_path)

				local_changes = str(diff).split("@@ -")
				del local_changes[0]
				for local_change in local_changes:
					for line in local_change.splitlines():
						if line != "" and line != "---":
							if line[0] == "+":
								self.added_code += line[1:]+"\n"
								# feature: additions
								self.additions += 1
								# feature: keywords
								for token in re.split('[\s\+\-\*\/,;><=()\[\]\{\}]', line):
									if token in self.keywords.keys():
										self.keywords[token] += 1
							elif line[0] == "-":
								self.deleted_code += line[1:]+"\n"
								self.deletions += 1
								# feature: keywords
								for token in re.split('[\s\+\-\*\/,;><=()\[\]\{\}]', line):
									if token in self.keywords.keys():
										self.keywords[token] += 1

							elif line[0].isdigit():
								self.hunk_count += 1

					if (len((self.added_code.splitlines()) + self.deleted_code.splitlines())) > 2000:
						raise ValueError("Commit too long, skipping", str(self.commit))

		self.added_functions += len(re.findall(r'\s*(?:(?:inline|static)\s+){0,2}\w+\s+\*?\s*\w+\s*\([^!@#$+%^;]+?\)\s*\{', self.added_code))
		self.deleted_functions += len(re.findall(r'\s*(?:(?:inline|static)\s+){0,2}\w+\s+\*?\s*\w+\s*\([^!@#$+%^;]+?\)\s*\{', self.deleted_code))

		past_authors = set()
		for file_name in files:
			history = self.repo.git.rev_list("--format=short","--skip=1", str(self.commit), "--", file_name)
			for line in history.splitlines():
				if line[:7] == "commit ":
					# feature: past changes
					self.past_changes += 1
				if line[:8] == "Author: ":
					if line not in past_authors:
						past_authors.add(line)
						# feature: past different authors
						self.past_different_authors += 1

		author_history = self.repo.git.log("--author", self.commit.author)
		author_contributions = len(re.findall(r'commit \b[0-9a-f]{5,40}\b\nAuthor: ', author_history))
		self.contributions_percent = (author_contributions / self.commit_count) * 100

	def create_feature_vector(self):
		features = []

		# commit features
		put_into_bin(features, self.past_different_authors, 1750, False)
		put_into_bin(features, self.additions, 5000, False)
		put_into_bin(features, self.deletions, 4000, False)
		put_into_bin(features, self.past_changes, 8000, False)
		put_into_bin(features, self.hunk_count, 600, False)
		put_into_bin(features, self.added_functions, 1400, False)
		put_into_bin(features, self.deleted_functions, 60, False)
		put_into_bin(features, self.authored_date, 1561381708, False)

		# author feature
		put_into_bin(features, self.contributions_percent, 5, False)

		# repository features
		put_into_bin(features, self.commit_count, self.commit_count, False)
		put_into_bin(features, self.repo_creation_date, self.repo_creation_date, False)
		put_into_bin(features, self.unique_contributors, self.unique_contributors, False)
		put_into_bin(features, self.star_count, self.star_count, False)
		put_into_bin(features, self.fork_count, self.fork_count, False)

		# keyword features
		for keyword_count in self.keywords.values():
			put_into_bin(features, keyword_count, 20, False)

		# bag of words features
		# extract words from commit message, added and deleted code
		words = re.split("\s", self.commit.message) + re.split("[\s\+\-\*\/,;><=()\[\]\{\}]", self.added_code) + re.split("[\s\+\-\*\/,;><=()\[\]\{\}]", self.deleted_code)
		# remove empty strings
		words = list(filter(None, words))

		# lookup if word is in bag of words
		for word in words:
			if word in self.bag_of_words.keys():
				self.bag_of_words[word] = True

		# sort bag of word keys and append to feature vector accordingly
		for word in sorted(self.bag_of_words.keys()):
			if self.bag_of_words[word] == True:
				features.append(1)
			else:
				features.append(0)

		self.feature_vector = csc_matrix(features)

	def get_feature_vector(self):
		return self.feature_vector

	def store_feature_vector_in(self, type_of_commit):
		save_npz(type_of_commit+"/"+str(self.commit)+".npz", self.feature_vector)

def put_into_bin(features, numeric_value, max_value, unevenly_distributed):
	if unevenly_distributed:
		max_value = math.log(max_value)
		numeric_value = math.log(numeric_value)

	previous_bin = 0
	step = max_value/20

	for bin in np.arange(step, max_value, step):
		features.append(1) if numeric_value >= previous_bin and numeric_value < bin else features.append(0)
		previous_bin = bin

	if numeric_value >= previous_bin:
		features.append(1)
	else:
		features.append(0)
