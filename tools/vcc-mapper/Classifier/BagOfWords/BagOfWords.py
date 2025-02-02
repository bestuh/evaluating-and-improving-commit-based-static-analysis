import subprocess
import os
from joblib import dump
import glob
import re
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

class BagOfWords:

	def __init__(self):
		self.word_vect = CountVectorizer()
		self.word_transformer = TfidfTransformer()

	def load_bag_of_words(self):
		with open("BagOfWords/words.txt", "r+") as w:
			word_counts = self.word_vect.fit_transform(w)
			self.word_transformer.fit_transform(word_counts)
		
	def create_bag_of_words(self):
		
		all_words = open("BagOfWords/words.txt", "w+")
		
		for path in (glob.glob("Training/vccs/*/*/*.json") + glob.glob("Training/unclassified/*/*.json")):
			with open(path, "r+") as json:
				raw_data = eval(json.read())
				words = raw_data["added_code"]+"\n"
				words += raw_data["deleted_code"]+"\n"
				words += raw_data["commit_message"]+"\n"
		
				all_words.write(words.encode('utf8','replace').decode('utf8'))
		all_words.close()
		
	def get_word_vect(self, words):
		new_word_counts = self.word_vect.transform(words)
		return self.word_transformer.transform(new_word_counts)

	def save_bag_of_words(self, name):
                dump(self, "Models/"+name+"_bag_of_words.joblib")
