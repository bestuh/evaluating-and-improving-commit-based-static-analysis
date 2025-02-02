import sys
from sklearn.model_selection import cross_val_score
from sklearn import svm, preprocessing
from sklearn.ensemble import BaggingClassifier
import sqlite3
from joblib import dump, load
import numpy as np
from scipy.sparse import csc_matrix, vstack, hstack


sys.setrecursionlimit(100000000)

class Svm:
    def __init__(self):
        self.confidences = {}

    def load_model(self, model_name):
        # load trained model
        self.model = load("Models/"+model_name + ".joblib")
        self.preprocessing = load("Models/"+model_name + "_preprocessing.joblib")

    def save_model(self, model_name):
        dump(self.model, "Models/"+model_name+".joblib")
        dump(self.preprocessing, "Models/"+model_name+"_preprocessing.joblib")
        print("Safed model to " + model_name +".joblib! Parameters:\n\n" + str(self.model))

    def vcc_or_unclassified(self, feature_vector, threshold):
        if feature_vector[1] not in self.confidences.keys():
            scaled_feature_vector = self.preprocess(feature_vector[0])
            confidence = self.model.decision_function(scaled_feature_vector)
            #significance_vector = scaled_feature_vector.multiply(self.model.coef_[0])
            self.confidences[feature_vector[1]] = confidence
        else:
            confidence = self.confidences[feature_vector[1]]

        if confidence[0] > threshold:
            #print("Commit", str(feature_vector[1]), "is prone to be vulnerable!")
            '''
            print("Confidence:", str(confidence[0]))
            print("The significant feature was:" , str(significance_vector.argmax()), "with score", str(significance_vector.max()) + "\n")
            '''
            return True
        else:
            #print("Commit", str(feature_vector[1]), "is not prone to be vulnerable!")
            '''
            print("Confidence:", str(confidence[0]))
            print("The significant feature was: " + str(significance_vector.argmin()), "with score", str(significance_vector.min()) + "\n")
            '''
            return False

    def evaluate_set(self, vcc_feature_vectors, unclassified_feature_vectors):
        '''
        feature_vectors = self.preprocess(vcc_feature_vectors[0][0])
        for feature_vector in vcc_feature_vectors[1:]+unclassified_feature_vectors:
            feature_vectors = vstack((feature_vectors, self.preprocess(feature_vector[0])))
        dump(feature_vectors, "Vectors/testing_set.joblib")
        '''
        feature_vectors = load("Vectors/testing_set.joblib")
        
        confidences = self.model.decision_function(feature_vectors)
        for i, confidence in enumerate(confidences):
            self.confidences[(vcc_feature_vectors+unclassified_feature_vectors)[i][1]] = confidence

        pre= []
        rec= []
        for t in np.arange(-5, 5, 0.001):
            tp = 0
            tn = 0
            fn = 0
            fp = 0
            for commit in vcc_feature_vectors:
                if self.confidences[commit[1]] > t:
                    tp += 1
                else: fn += 1

            for commit in unclassified_feature_vectors:
                if self.confidences[commit[1]] > t:
                    fp += 1
                else: tn += 1

            if tp == 0:
                precision = 0
                recall = 0
                pre.append(0)
                rec.append(0)
            else:
                precision = tp/(tp+fp)
                recall = tp/(tp+fn)
                pre.append(precision)
                rec.append(recall)
            print("True Positives: ", str(tp))
            print("True Negatives: ", str(tn))
            print("False Positives: ", str(fp))
            print("False Negatives: ", str(fn))
            print("Precision: ", str(precision))
            print("Recall: ", str(recall))

        open("x_own", "w+").write(str(rec))
        open("y_own", "w+").write(str(pre))


    def train_model(self, vcc_feature_vectors_and_weigts, unclassified_feature_vectors, fs=303, c=1, weight=1):

        labels = []
        weights = []
        '''
        vcc_feature_vectors = [x[0] for x in vcc_feature_vectors_and_weigts]
        fit_vectors = [x.tocsc()[0, :303] for x in vcc_feature_vectors+unclassified_feature_vectors]
        # preprocess fit
        self.preprocess_fit(fit_vectors)
        #dump(self.preprocessing, "Models/preprocessing.joblib")
        '''
        #self.preprocessing = load("Models/preprocessing.joblib")

        '''
        feature_vectors = self.preprocess(vcc_feature_vectors[0])
        for feature_vector in vcc_feature_vectors[1:]+unclassified_feature_vectors:
            feature_vectors = vstack((feature_vectors, self.preprocess(feature_vector)))
        #dump(feature_vectors, "feature_vectors.joblib")
        '''
        feature_vectors = load("feature_vectors.joblib")

        for i, vector in enumerate(vcc_feature_vectors_and_weigts):
            labels.append(1)
            weights.append(vcc_feature_vectors_and_weigts[i][1]*weight)
        for i in range(len(unclassified_feature_vectors)):
            labels.append(0)
            weights.append(1)

        print("fitting...")
        self.model = svm.LinearSVC(C=c, max_iter=100000000)

        # feature selection using k best
        '''
        print("feature selection...")
        self.kbest = SelectKBest(chi2, k=int(fs))
        feature_vectors_best = self.kbest.fit_transform(feature_vectors_scaled, labels)
        self.model.fit(feature_vectors_best, labels, weights)
        print("Done")
        # feature selection using select from model
        self.feature_select = SelectFromModel(self.model, threshold=float(fs))
        self.feature_select.fit(feature_vectors_scaled, labels)
        feature_selected_vectors = self.feature_select.transform(feature_vectors_scaled)
        print(feature_selected_vectors.shape)
        '''

        '''
        self.model.fit(feature_vectors, labels, weights)
        print("Score:", str(self.model.score(feature_vectors, labels)))
        print("Done")
        self.confidences = {}
        '''
        k = 5
        scores = cross_val_score(self.model, feature_vectors, labels, cv=k)
        print(scores)
        print("Average score:", str(sum(scores)/k))
        exit()

    def preprocess_fit(self, vectors):
        fit_vecs = vectors[0]
        for vec in vectors:
            fit_vecs = vstack((fit_vecs, vec))
        self.preprocessing = preprocessing.KBinsDiscretizer(n_bins=5)
        self.preprocessing.fit(fit_vecs.toarray())

    def preprocess(self, vector):
        return hstack(( self.preprocessing.transform(vector.tocsc()[0, :303].toarray()), vector.tocsc()[0, 303:].toarray() )).tocsr()
