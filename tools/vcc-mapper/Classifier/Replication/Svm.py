import sys
from sklearn import svm
import sqlite3
from joblib import dump, load
import numpy as np
from scipy.sparse import csc_matrix, vstack

sys.setrecursionlimit(100000000)

class Svm:

    def load_model(self, model_name):
        # load trained model
        self.model = load(model_name + ".joblib")


    def save_model(self, model_name):
        dump(self.model, model_name+".joblib")
        print("Safed model to " + model_name +".joblib! Parameters:\n\n" + str(self.model))


    def vcc_or_unclassified(self, feature_vector, threshold=1):
        confidence = self.model.decision_function(feature_vector)
        if (self.model.predict(feature_vector) == 1) and (confidence[0] > threshold):
            #print("This commit is prone to be vulnerable!")
            return True
        else:
            #print("This commit is not prone to be vulnerable!")
            return False

    def predict_confidence(self, feature_vector):
        prediction = self.model.predict(feature_vector) # 0 or 1
        confidence = self.model.decision_function(feature_vector) # confidence for the prediction being correct (distance to the boundary)
        return prediction[0], confidence[0]

    def train_model(self, vcc_feature_vectors, unclassified_feature_vectors, c=100, kernel="linear"):

        labels = []
        weights = []
        feature_vectors = vcc_feature_vectors[0]
        for feature_vector in vcc_feature_vectors[1:]+unclassified_feature_vectors:
            feature_vectors = vstack((feature_vectors, feature_vector))

        for i in range(len(vcc_feature_vectors)):
            labels.append(1)
            weights.append(100)
        for i in range(len(unclassified_feature_vectors)):
            labels.append(0)
            weights.append(1)

        # fit model
        self.model = svm.LinearSVC(C=c, max_iter=1000000000, class_weight="balanced") # class_weight={0:100, 1:1}) #dual=False)
        self.model.fit(feature_vectors, labels) #, weights)

