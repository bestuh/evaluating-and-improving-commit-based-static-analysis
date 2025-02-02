from Svm import Svm
from Commit import Commit
import numpy as np
from scipy.sparse import load_npz
import glob

def main():

    '''
    # store feature vectors
    directory = "vccs/Training/httpd"
    with open("../Datasets/Training/httpd_vuls.txt", "r+") as vuls: #../Datasets/Testing/kernel_new.txt",
        commits = vuls.readlines()
        commits = list(set(commits))
        for i, commit in enumerate(commits[1:]):
            print(str(i+1)+"/"+str(len(commits)))
            commit = commit.split("  ")[0][-40:] # commit.rstrip() 
            print(commit)
            # skip duplicates
            if directory+commit+".npz" in glob.glob(directory+"/*")+glob.glob("vccs/*/*/*") :
                print("Duplicate, skipping " + vcc)
                continue
            try:
                commit = Commit("/home/jan.wagner/Repos/httpd", commit)
                commit.store_feature_vector_in(directory)
            except ValueError as e:
                print(e)
            except:
                print("Failed for commit: ", commit)
    exit()
    '''


    '''
    vcc_training = []
    for feature_vector in (glob.glob("vccs/Training/*/*") + glob.glob("vccs/Validation/*/*")):
        vcc_training.append(load_npz(feature_vector))

    unclassified_training = []
    for feature_vector in glob.glob("unclassified/Training/*/*"):
        unclassified_training.append(load_npz(feature_vector))
    '''
    
    vcc_testing = []
    for feature_vector in glob.glob("vccs/Testing/linux/*"):
        vcc_testing.append(load_npz(feature_vector))

    unclassified_testing = []
    for feature_vector in glob.glob("unclassified/Testing/linux/*"):
        unclassified_testing.append(load_npz(feature_vector))

    svm = Svm()
    svm.load_model("trained_model_003_unbalanced") # best

    
    tp = 0
    fp = 0
    tn = 0
    fn = 0
    threshold = 0.15
    for vec in vcc_testing:
        result = svm.vcc_or_unclassified(vec, threshold=threshold)
        if result == True:
            tp += 1
        else:
            fn += 1

    for vec in unclassified_testing:
        result = svm.vcc_or_unclassified(vec, threshold=threshold)
        if result == True:
            fp += 1
        else:
            tn += 1

    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    accuracy = (tp + tn) / (tp + tn + fp + fn)
    f = 2 * ((precision * recall)/(precision + recall))
    print("True Positives: ", str(tp))
    print("True Negatives: ", str(tn))
    print("False Positives: ", str(fp))
    print("False Negatives: ", str(fn))
    print("precision =", str(precision))
    print("recall =", str(recall))
    print("accuracy =", str(accuracy))
    print("f1 =", str(f))


    '''
    svm = Svm()
    svm.load_model("trained_model_005_balanced") # best

    best_t = 0
    best_f = 0
    for t in np.arange(0, 2, 0.01):
        print(t)
        #svm.train_model(vcc_training, unclassified_training)

        tp = 0
        fp = 0
        tn = 0
        fn = 0
        for vec in vcc_testing:
            result = svm.vcc_or_unclassified(vec, threshold=t)
            if result == True:
                tp += 1
            else:
                fn += 1

        for vec in unclassified_testing:
         result = svm.vcc_or_unclassified(vec, threshold=t)
         if result == True:
             fp += 1
         else:
             tn += 1

        try:
            precision = tp / (tp + fp)
            recall = tp / (tp + fn)
            accuracy = (tp + tn) / (tp + tn + fp + fn)
            f = 2 * ((precision * recall)/(precision + recall))
            
            print("True Positives: ", str(tp))
            print("True Negatives: ", str(tn))
            print("False Positives: ", str(fp))
            print("False Negatives: ", str(fn))
            print("precision =", str(precision))
            print("recall =", str(recall))
            print("accuracy =", str(accuracy))
            print("f1 =", str(f))

            if recall == 0.24:
                print("RECALL!" + str(t))

            if f > best_f:
                best_f = f
                best_c = t
        except:
            print("Divided by 0")
        # svm.save_model("trained_model_083")

    print("Best t value = ", str(best_c))
    print("with f = ", str(best_f))
    '''

    '''
    best_c = 0
    best_f = 0
    for c in np.arange(0.01, 1, 0.01):
        svm = Svm()
        #svm.load_model("trained_model_1")
        print(c)
        svm.train_model(vcc_training, unclassified_training, c)

        tp = 0
        fp = 0
        tn = 0
        fn = 0
        for vec in vcc_testing:
            result = svm.vcc_or_unclassified(vec)
            if result == True:
                tp += 1
            else:
                fn += 1

        for vec in unclassified_testing:
         result = svm.vcc_or_unclassified(vec)
         if result == True:
             fp += 1
         else:
             tn += 1

        precision = tp / (tp + fp)
        recall = tp / (tp + fn)
        accuracy = (tp + tn) / (tp + tn + fp + fn)
        f = 2 * ((precision * recall)/(precision + recall))
        
        print(str(f))
        if f > best_f:
            best_f = f
            best_c = c
        # svm.save_model("trained_model_083")

    print("Best C value = ", str(best_c))
    print("with f = ", str(best_f))
    '''



if __name__ == "__main__":
    main()

