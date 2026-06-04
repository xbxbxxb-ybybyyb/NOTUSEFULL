import os
import pickle
from tqdm import tqdm
import numpy as np
import torch
from torch.utils.data import DataLoader
# import torch.nn as nn

from model import aemlp4Factors, aemlp
#from ensemble import xgboost
from dataset import myDataset
from parser import args
from utils import *
from sklearn.metrics import mean_squared_error
from evaluation import get_validation_predicts_stat, get_validation_win_return

import warnings
warnings.filterwarnings("ignore")


def getData(tag_index = 0):
    testX = np.load("/data/user/018187/TrainValidData/Data2/ValidData.npy", allow_pickle=True)
    testY = np.load("/data/user/018187/TrainValidData/Data2/ValidLabel.npy", allow_pickle=True)[:, tag_index:tag_index+1]
    
    num_workers = 16
    test_loader = DataLoader(dataset=myDataset(testX, testY), batch_size=32768, shuffle=False, pin_memory=True, num_workers=num_workers)
    
    return test_loader
    
def getFactors(tag_index = 0):
    test_loader = getData(tag_index=tag_index)
    # load saved model (wrt. tag_index)
    device = torch.device("cpu")
    model = aemlp4Factors(input_size=58, hidden_size=64, output_size=1, dropout=0.2).to(device)

    checkpoint_path = "/data/user/000053/quanttest/saved_nn/manual_best/aemlp_2class-4loss_tag_{}.pkl".format(tag_index)
    checkpoint = torch.load(checkpoint_path, map_location = 'cpu')  # map to cpu 为了兼容生产版    
    # filter num_batches_tracked
    state_dict = model.state_dict() 
    for key, value in checkpoint.items():
        if 'num_batches_tracked' in key:
            continue        
        state_dict[key] = value
        
    model.load_state_dict(state_dict)
    model.eval()

    print("Start utilizing TestSet ================================= ")
    x_test_list = []
    for x, label, label_class in tqdm(test_loader):           
        x_inp, outRegressor, outAction, outAe, x_decoder = model(x)  # x_inp: shape-(bs, 32)
        x_tmp = x_inp.squeeze().data.tolist()
        x_test_list.extend(x_tmp)
                
    xtest_factors = np.array(x_test_list)
    
    """
    print("Start Saving Factors to `/quanttest/saved/` ================================= ")
    # Save factors for Train&Test Dataset
    # save_trainpath = "/data/user/000053/quanttest/saved/nntrainfactors.npy"
    # np.save(save_trainpath, xtrain_factors)
    save_testpath = "/data/user/000053/quanttest/saved/nntestfactors.npy"
    np.save(save_testpath, xtest_factors)    
    print("Successfully Saving Factors to `/quanttest/saved/` ================================= ")
    """
    
    return xtest_factors
    
def ensembleTest(tag_index = 0):
    
    test_loader = getData(tag_index=tag_index)
    # load saved model (wrt. tag_index)
    model = aemlp(input_size=args.input_size, hidden_size=args.hidden_size, output_size=1, dropout=args.dropout)

    checkpoint_path = "/data/user/000053/quanttest/saved_nn/manual_best/aemlp_2class-4loss_tag_{}.pkl".format(tag_index)
    checkpoint = torch.load(checkpoint_path, map_location = 'cpu')  # map to cpu 为了兼容生产版   
    # filter num_batches_tracked
    state_dict = model.state_dict() 
    for key, value in checkpoint.items():
        if 'num_batches_tracked' in key:
            continue
        
        state_dict[key] = value      
    model.load_state_dict(state_dict)
    model.eval()

    preds, labels = [], []
    
    for x, label, label_class in tqdm(test_loader):

        pred, outAction, outAe, x_decoder = model(x)
        pred_list = pred.squeeze().data.tolist()
        preds.extend(pred_list)
        labels.extend(label.squeeze().tolist())
    
    # AE-MLP prediction
    preds, labels = np.array(preds), np.array(labels)  # list 转为 ndarray  
    
    # Xgboost prediction
    if os.path.isfile('/data/user/000053/quanttest/saved/bigxgb_tag_{}.pkl'.format(tag_index)):
        with open('/data/user/000053/quanttest/saved/bigxgb_tag_{}.pkl'.format(tag_index), 'rb') as fin:
            multi_xgb = pickle.load(fin)
    
    testX = np.load("/data/user/018187/TrainValidData/Data2/ValidData.npy", allow_pickle=True)        
    xgb_preds = multi_xgb.predict(testX)

    # Ensemble:加权平均
    w_1 = 0.5  # model_nn weight during ensemble
    w_2 = 1 - w_1
    preds = w_1 * preds + w_2 * xgb_preds 
    
    return preds, labels

  
if __name__ == "__main__":
    
    # 方法1. ensemble
    for tag_index in range(6):
        
        # ensemble predict
        ypred_valid, y_valid = ensembleTest(tag_index=tag_index)
        
        # Code Check
        myPrint("Evaluating ...", "backtest")
        mse = mean_squared_error(y_valid, ypred_valid)
        myPrint("RMSE: {}".format(np.sqrt(mse)), "backtest")
        
        acc, mse_str, rmse_str, mae_str, corr_str, predicts_str = get_validation_predicts_stat(y_valid, ypred_valid)
        myPrint(rmse_str+'\n'+mae_str+'\n\n'+acc+corr_str, "backtest")
        myPrint("Predicts range:  \n"+predicts_str+'\n', "backtest")
    
    """
    # 方法2. nnfactors_xgboost
    
    # hyper-parameter
    modelname = "separate_nnfactors_xgb"
#    modelname = "nnfactors_xgb"
#    modelname = "bigxgb"
    
    ValidDataPath = "/data/user/018187/TrainValidData/Data2/ValidData.npy"
    ValidLabelPath = "/data/user/018187/TrainValidData/Data2/ValidLabel.npy"
    ValidLabel = np.load(ValidLabelPath, allow_pickle=True)
    ValidData = np.load(ValidDataPath, allow_pickle=True)
    # 这个 tag_index 只是为了指定 "模型名"
    
    if modelname == "bigxgb":
         x_valid = ValidData
    elif modelname == "nnfactors_xgb":
        x_valid = np.concatenate((ValidData, getFactors(tag_index=0)), axis=1)  # combined with nn-factors, Shape:(N, 58+32)   
    
    for tag_index in range(6):
        
        # separate models
        if modelname == "separate_nnfactors_xgb":
            pass
        
        # predict
        print("Loading Model ...")
        if os.path.isfile('/data/user/000053/quanttest/saved/{0}_tag_{1}.pkl'.format(modelname, tag_index)):
            with open('/data/user/000053/quanttest/saved/{0}_tag_{1}.pkl'.format(modelname, tag_index), 'rb') as fin:
                nn_xgb = pickle.load(fin)
        
        ypred_valid = nn_xgb.predict(x_valid)  
        
        # Code Check
        print("Evaluating ...")
        y_valid = ValidLabel[:,tag_index]
        mse = mean_squared_error(y_valid, ypred_valid)
        print("MSE: ", mse)
        print("RMSE: ", np.sqrt(mse))
        #
        acc, mse_str, rmse_str, mae_str, corr_str, predicts_str = get_validation_predicts_stat(y_valid, ypred_valid)
        print(rmse_str, '\n', mae_str, '\n\n', acc, corr_str)
        print("Predicts range:  \n", predicts_str, '\n')
    """
    
    