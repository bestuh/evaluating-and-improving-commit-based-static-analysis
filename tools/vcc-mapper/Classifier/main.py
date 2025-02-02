from Svm import Svm
import subprocess
from Commit import Commit
from joblib import load, dump
from BagOfWords.BagOfWords import BagOfWords
import numpy as np
from scipy.sparse import load_npz
import glob
import re
import time
from multiprocessing import Pool, Manager

def store_commit(commit):
    repository = "firefox"
    if commit[1] == "confident":
        directory = "Training/vccs/"+repository.lower()+"/confident"
    elif commit[1] == "not confident":
        directory = "Training/vccs/"+repository.lower()+"/not_confident"
    else:
        directory = "Training/vccs/"+repository.lower()+"/ground_truth"
    directory = "Training/vccs/"+repository.lower()
    try:
        commit = Commit("/home/rappy/Programs/Repos/gecko-dev", commit[0].rstrip()) #+repository
        commit.extract_features()
        commit.save_features_to_json(directory)
    except ValueError as e:
        print(e)


def main():

    a = time.time()

    '''
    # index bow features TODO: verschieben
    add_voc = [v for v, i in sorted(bag_of_words.add_vect.vocabulary_.items(), key=lambda item: item[1])]
    del_voc = [v for v, i in sorted(bag_of_words.del_vect.vocabulary_.items(), key=lambda item: item[1])]
    msg_voc = [v for v, i in sorted(bag_of_words.count_vect.vocabulary_.items(), key=lambda item: item[1])]
    print(len(msg_voc))
    exit()

    for v in add_voc:
        print("Addition of: " + v)
    for v in del_voc:
        print("Deletion of: " + v)
    for v in msg_voc:
        print("Use of: " + v + " in commit message")
    exit()
    '''


    '''
    # store feature vectors
    # parallel
    config = open("Training/vccs/firefox/config.txt", "r+").readlines()
    commits = [[x.split("  ")[0].rstrip()] for x in config] #, x.split("  ")[3].rstrip()
    p = Pool()
    p.map(store_commit, commits)
    p.close()
    p.join()
    print("Zeit: " + str(time.time() - a))
    exit()
    '''

    # create feature vectors
    '''
    bag_of_words = BagOfWords()
    bag_of_words.load_bag_of_words()
    raw_data_paths = glob.glob("Training/unclassified/*/*.json") + glob.glob("Training/vccs/*/*/*.json") + glob.glob("Validation/vccs/*/*.json") + glob.glob("Testing/vccs/*/*.json") + glob.glob("Validation/bugs/*/*.json") +  glob.glob("Testing/bugs/*/*.json") + glob.glob("Validation/unclassified/*/*.json") + glob.glob("Testing/unclassified/*/*.json")
    count = 1
    for path in raw_data_paths:
        print(str(count)+"/"+str(len(raw_data_paths)))
        # create feature vector
        commit = Commit()
        commit.load_features_from_json(path)
        commit.create_feature_vector(bag_of_words)
        # store feature vector
        commit.store_feature_vector_in(path[:-45])
        count += 1
    print("Zeit: " + str(time.time() - a))
    exit()
    '''

    # Load data set
    vcc_training = []
    for feature_vector in glob.glob("Training/vccs/*/ground_truth/*.npz"):
        vcc_training.append([load_npz(feature_vector), 5])
    for feature_vector in glob.glob("Training/vccs/*/confident/*.npz"):
        vcc_training.append([load_npz(feature_vector), 5])
    for feature_vector in glob.glob("Training/vccs/*/not_confident/*.npz"):
        vcc_training.append([load_npz(feature_vector), 1])
    print(len(vcc_training))
    
    unclassified_training = []
    for feature_vector in glob.glob("Training/unclassified/*/*.npz"):
        unclassified_training.append([load_npz(feature_vector), feature_vector[-44:-4]])
    #dump(unclassified_training, "Vectors/unclassified_training.joblib")
    #unclassified_training = load("Vectors/unclassified_training.joblib")[:1]

    vcc_validation = []
    '''
    for feature_vector in (glob.glob("Validation/vccs/*/*.npz")):
        vcc_validation.append([load_npz(feature_vector), feature_vector[-44:-4]]) #.multiply(e)
    dump(vcc_validation, "Vectors/vcc_validation.joblib")
    '''
    vcc_validation = load("Vectors/vcc_validation.joblib")

    unclassified_validation = []
    '''
    for feature_vector in (glob.glob("Validation/unclassified/*/*.npz") + glob.glob("Validation/bugs/*/*.npz")):
        unclassified_validation.append([load_npz(feature_vector), feature_vector[-44:-4]])
    print(len(unclassified_validation))
    dump(unclassified_validation, "Vectors/unclassified_validation.joblib")
    '''
    unclassified_validation = load("Vectors/unclassified_validation.joblib")

    vcc_testing = []
    '''
    for feature_vector in (glob.glob("Testing/vccs/*/*.npz")):
        vcc_testing.append([load_npz(feature_vector), feature_vector[-44:-4]]) #.multiply(e)
    print(len(vcc_testing))
    dump(vcc_testing, "Vectors/vcc_testing.joblib")
    '''
    vcc_testing = load("Vectors/vcc_testing.joblib")

    unclassified_testing = []
    '''
    for feature_vector in (glob.glob("Testing/unclassified/*/*.npz") + glob.glob("Testing/bugs/*/*.npz")):
        unclassified_testing.append([load_npz(feature_vector), feature_vector[-44:-4]]) #.multiply(e)
    print(len(unclassified_testing))
    dump(unclassified_testing, "Vectors/unclassified_testing.joblib")
    '''
    unclassified_testing = load("Vectors/unclassified_testing.joblib")

    svm = Svm()
    c = 0.09 #1 # 0.1
    w = 0.2 #1.5 #0.2 
    svm.train_model(vcc_training, unclassified_training, c=c, weight=w)
    svm.save_model("c-"+str(c)+"w"+str(w))

    #svm.load_model("c-0.5w0.5")
    #svm.evaluate_set(vcc_validation+vcc_testing, unclassified_validation+unclassified_testing)
    #exit()
    ret = evaluate(svm, vcc_training, unclassified_training, threshold=0)
    print(ret)
    exit()
    x = []
    y = []
    for t in np.arange(-5, 5, 0.001):
        ret = evaluate(svm, vcc_validation+vcc_testing, unclassified_validation+unclassified_testing, threshold=t)
        x.append(ret[1])
        y.append(ret[0])
    open("x_own", "w+").write(str(x))
    open("y_own", "w+").write(str(y))
    exit()
    for t in np.arange(-3, 3, 0.0001):
        ret = evaluate(svm, vcc_training, unclassified_training, threshold=t)
        print(ret)

def evaluate(svm, vcc_vectors, unclassified_vectors, threshold=-99999999999999):
    tp = 0
    fp = 0
    tn = 0
    fn = 0
    for vec in vcc_vectors:
        result = svm.vcc_or_unclassified(vec, threshold=threshold)
        if result == True:
            tp += 1
        else:
            fn += 1

    for vec in unclassified_vectors:
        result = svm.vcc_or_unclassified(vec, threshold=threshold)
        if result == True:
            fp += 1
        else:
            tn += 1

    print("True Positives: ", str(tp))
    print("True Negatives: ", str(tn))
    print("False Positives: ", str(fp))
    print("False Negatives: ", str(fn))

    precision = 0
    recall = 0
    accuracy = 0
    f = 0 
    f2 = 0
    try:
        if tp + fp == 0: return [0, 0, 0, 0, 0]
        precision = tp / (tp + fp)
        recall = tp / (tp + fn)
        accuracy = (tp + tn) / (tp + tn + fp + fn)
        f = 2 * ((precision * recall)/(precision + recall))
        beta = 0.5
        f2 = (1 + beta**2) * ((precision * recall)/((beta**0.5 * precision) + recall))
        jan = tp/fp
        print("F2: ", str(f2))
        print("Jan: ", str(jan))
        print("Precision: ", str(precision))
        print("Recall: ", str(recall))
    except:
        pass
        #print("Division by 0.")

    return [precision, recall, accuracy, f, f2]

def find_best_hyperparameters(svm, vcc_training, unclassified_training, vcc_validation, unclassified_validation, range_c, range_w):
    best_c = 0
    best_w = 0
    best_f = 0
    for c in np.arange(range_c[0], range_c[1], range_c[2]):
        for w in np.arange(range_w[0], range_w[1], range_w[2]):
            print("C:", str(c))
            print("W:", str(w))

            svm.train_model(vcc_training, unclassified_training, c=c, weight=w)
            f = evaluate(svm, vcc_validation, unclassified_validation)[4]

            if f > best_f:
                best_f = f
                best_c = c
                best_w = w

    return best_c, best_w

if __name__ == "__main__":
    main()

