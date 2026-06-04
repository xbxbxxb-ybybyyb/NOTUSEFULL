import os
import pickle
import numpy as np
from parser import args

# Valid Path
ValidDataPath = "/data/user/018187/TrainValidData/Data2/ValidData.npy"
nnValidDataPath = "/data/user/000053/quanttest/saved/nntestfactors.npy"  # 32 factors after mlp
ValidLabelPath = "/data/user/018187/TrainValidData/Data2/ValidLabel.npy"

def xgboost(tag_index, modelname="nnfactors_xgb"):
    
    ValidData = np.load(ValidDataPath, allow_pickle=True)
    
    if modelname == "nnfactors_xgb":
        nnValidData = np.load(nnValidDataPath, allow_pickle=True)
        testX = np.concatenate((ValidData, nnValidData), axis=1)  # combined with nn-factors
    else:
        testX = ValidData

    # Load Saved_model
    if os.path.isfile('/data/user/000053/quanttest/saved/{0}_tag_{1}.pkl'.format(modelname, tag_index)):
        with open('/data/user/000053/quanttest/saved/{0}_tag_{1}.pkl'.format(modelname, tag_index), 'rb') as fin:
            multi_xgb = pickle.load(fin)
            
    xgb_preds = multi_xgb.predict(testX)  # np.ndarray
    return xgb_preds