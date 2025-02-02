import importlib
import file_utils
from arguments import read_params
from vccrosshair import VCCrosshair
from lapredict import LAPredict
from deepjit import DeepJIT
from cc2vec import CC2Vec
from simcom import SimCom

Svm = importlib.import_module("tools.vcc-mapper.Classifier.Replication.Svm")
Commit = importlib.import_module("tools.vcc-mapper.Classifier.Replication.Commit")

if __name__ == "__main__":
    args = read_params()

    data_checkpoint = file_utils.DataCheckpoint()
    
    if args.model == "vccrosshair":
        # run VCCrosshair
        vccrosshair = VCCrosshair()
        vccrosshair.preprocess(dataset_name=args.dataset)
        vccrosshair.train(dataset_name=args.dataset)
        vccrosshair.test(dataset_name=args.dataset, split=args.test_split)
    
    if args.model in ["lr-jit", "dbn-jit", "lapredict"]:
        # run LAPredict, LR-JIT & DBN-JIT
        lapredict = LAPredict() # includes LR-JIT and DBN-JIT
        lapredict.preprocess(dataset_name=args.dataset, test_split=args.test_split)
        lapredict.run(dataset_name=args.dataset, test_split=args.test_split)
    
    if args.model == "deepjit":
        # run DeepJIT
        deepjit = DeepJIT()
        deepjit.preprocess(dataset_name=args.dataset, test_split=args.test_split)
        deepjit.train()
        deepjit.predict(test_split=args.test_split)

    if args.model == "cc2vec":
        # run CC2Vec
        cc2vec = CC2Vec()
        cc2vec.preprocess(dataset_name=args.dataset, test_split=args.test_split)
        cc2vec.train_representations()
        cc2vec.generate_representations()
        cc2vec.train_classifier()
        cc2vec.predict()

    if args.model == "simcom":
        # run SimCom
        simcom = SimCom()
        simcom.preprocess(dataset_name=args.dataset)
        simcom.run_simple()
        simcom.train_complex()
        simcom.run_complex()
        simcom.run_combined()

    exit()
