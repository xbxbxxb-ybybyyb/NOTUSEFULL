import os
import torch
import torch.nn as nn
import numpy as np
from tqdm import tqdm

from model import regressor, aemlp, aemlp4Factors
from ensemble import xgboost
from dataset import getData
from parser import args
from utils import *

from sklearn.metrics import mean_squared_error
from evaluation import get_validation_predicts_stat, get_validation_win_return

import warnings
warnings.filterwarnings("ignore")

# eval during training stage
def valid(model, tag_index, test_loader, mod):
    model.eval()
    preds, labels = [], []
    
    start = time.time()
    for x, label, label_class in test_loader:
        if args.useGPU:
            x = x.to(args.device)  # batch_size, input_size
        
        if mod == "aemlp":  # Main + AE
            pred, outAction, outAe, x_decoder = model(x)
        elif mod == "cnn":
            pred, outAction = model(x)
        elif mod == "mlp":
            pred = model(x)


        pred_list = pred.squeeze().cpu().data.tolist()
        preds.extend(pred_list)
        labels.extend(label.squeeze().cpu().tolist())
    
    end = time.time()
    myPrint('Eval on valid set on tag_{0}, Consume {1} seconds'.format(tag_index, end-start), "{0}/logTrain_tag_{1}".format(args.model, tag_index))
    
    # Evaluate with such metrics  
    preds, labels = np.array(preds), np.array(labels)  # list 转为 ndarray
    start = time.time()
    mse = mean_squared_error(labels, preds)
    acc, mse_str, rmse_str, mae_str, corr_str, predicts_str = get_validation_predicts_stat(labels, preds)
    end = time.time()
    
    # Detail evaluation info
    myPrint('Valid MSE: {:.5f}, consume {:.2f} sec'.format(mse, end-start), "{0}/logTrain_tag_{1}".format(args.model, tag_index))
    myPrint(rmse_str+'\n'+mae_str+'\n'+acc+corr_str+'\n', "{0}/logTrain_tag_{1}".format(args.model, tag_index))
    myPrint("{} \n".format(predicts_str), "{0}/logTrain_tag_{1}".format(args.model, tag_index))


def getFactors(tag_index = 0):
    # train_sshuffle=False
    train_loader, test_loader = getData(corpus_dir = args.corpus_dir, tag_index=tag_index, batch_size = args.batch_size, train_shuffle=False)
    
    # load saved model (wrt. tag_index)
    model = aemlp4Factors(input_size=args.input_size, hidden_size=args.hidden_size, output_size=1, dropout=args.dropout).to(args.device)
    checkpoint = torch.load(os.path.join(args.save_dir, "manual_best/aemlp_2class-4loss_tag_{0}.pkl".format(tag_index)))
    model.load_state_dict(checkpoint)
    model.eval()
    
    print("Start utilizing TrainSet ================================= ")
    x_inp_list = []
    for x, label, label_class in tqdm(train_loader):
        if args.useGPU:
            x = x.to(args.device)  # batch_size, input_size
            
        x_inp, outRegressor, outAction, outAe, x_decoder = model(x)  # x_inp: shape-(bs,32)
        x_tmp = x_inp.squeeze().cpu().data.tolist()
        x_inp_list.extend(x_tmp)
    
    print("Start utilizing TestSet ================================= ")
    x_test_list = []
    for x, label, label_class in tqdm(test_loader):
        if args.useGPU:
            x = x.to(args.device)  # batch_size, input_size

        x_inp, outRegressor, outAction, outAe, x_decoder = model(x)  # x_inp: shape-(bs, 32)
        x_tmp = x_inp.squeeze().cpu().data.tolist()
        x_test_list.extend(x_tmp)
                
    xtrain_factors = np.array(x_inp_list)  # shape-(#num_train, 32)
    xtest_factors = np.array(x_test_list)
    
    print("Start Saving Factors to `/quanttest/saved/` ================================= ")
    # Save factors for Train&Test Dataset
    save_trainpath = "/data/user/000053/quanttest/saved/nntrainfactors_tag_{}.npy".format(tag_index)
    save_testpath = "/data/user/000053/quanttest/saved/nntestfactors_tag_{}.npy".format(tag_index)
    np.save(save_trainpath, xtrain_factors)
    np.save(save_testpath, xtest_factors)    
    
    print("Successfully Saving Factors to `/quanttest/saved/` ================================= ")
        
def test(tag_index):
    
    train_loader, test_loader = getData(corpus_dir = args.corpus_dir, tag_index=tag_index, batch_size = args.batch_size)
    # load saved model (wrt. tag_index)
    model = aemlp(input_size=args.input_size, hidden_size=args.hidden_size, output_size=1, dropout=args.dropout).to(args.device)
    checkpoint = torch.load(os.path.join(args.save_dir, "manual_best/aemlp_2class-4loss_tag_{}.pkl".format(tag_index)))
    model.load_state_dict(checkpoint)
    
    model.eval()
    preds, labels = [], []
    
    if args.mode == "ensemble":
        myPrint('Ensemble Xgboost and AE-MLP!!! Test on valid set on tag_{}'.format(tag_index), "logTest_tag_{}".format(tag_index))
    else:
        myPrint('Single Model!!! Test on valid set on tag_{}'.format(tag_index), "logTest_tag_{}".format(tag_index))
    
    start = time.time()
    for x, label, label_class in tqdm(test_loader):
        if args.useGPU:
            x = x.to(args.device)  # batch_size, input_size

        pred, outAction, outAe, x_decoder = model(x)
        pred_list = pred.squeeze().cpu().data.tolist()
        preds.extend(pred_list)
        labels.extend(label.squeeze().cpu().tolist())
    
    end = time.time()
    myPrint('Evaluate Valid Set ================================ Consume {:.3f} seconds'.format(end-start), "logTest_tag_{}".format(tag_index))
    
    # Evaluate with such metrics  
    preds, labels = np.array(preds), np.array(labels)  # list 转为 ndarray  
    if args.mode == "ensemble":
        xgb_preds = xgboost(tag_index=tag_index, modelname="xgb")  # shape同preds: (num_instances,)
        # """  # 加权平均
        w_1 = 0.5  # model_nn weight during ensemble
        w_2 = 1 - w_1
        preds = w_1 * preds + w_2 * xgb_preds 
        """  
        preds = np.maximum(preds, xgb_preds) # 取两者的max值
        """
    
    # 1. default metrics
    myPrint('Evaluate Valid Set ================================ {}'.format(showTime()), "logTest_tag_{}".format(tag_index))
    start = time.time()
    mse = mean_squared_error(labels, preds)
    acc, mse_str, rmse_str, mae_str, corr_str, predicts_str = get_validation_predicts_stat(labels, preds)
    end = time.time()
    # Detail evaluation info
    myPrint('Valid MSE: {:.5f}, consume {:.2f} sec'.format(mse, end-start), "logTest_tag_{}".format(tag_index))
    myPrint(rmse_str+'\n'+mae_str+'\n'+acc+'\n'+corr_str+'\n', "logTest_tag_{}".format(tag_index))
    myPrint("Predicts range:  \n {} \n".format(predicts_str), "logTest_tag_{}".format(tag_index))
    
    # 2. win-rate + return-rate
    buy = True if tag_index % 2 == 0 else False
    myPrint('Evaluate win-rate & return-rate on Valid Set {0}================================, {1}'.format(tag_index, showTime), "logTest_tag_{}".format(tag_index))
    start = time.time()
    stock_num_str, win_str, return_rate_str, mean_return_rate_str = get_validation_win_return(labels, preds, buy=buy)
    end = time.time()
    # Detail evaluation info, return_rate的计量单位是千分比
    myPrint('End evaluation, consume {0: .2f} seconds ================================'.format(end-start), "logTest_tag_{}".format(tag_index))
    myPrint(stock_num_str + '\n' + win_str + '\n' + return_rate_str + '\n' + mean_return_rate_str+ '\n', "logTest_tag_{}".format(tag_index))
        
           
if __name__ == '__main__':
    
    for tag_index in range(1, 6):
        # getFactors(tag_index)  
        test(tag_index)
    
