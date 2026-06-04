import numpy as np
from utils import *
import pickle
import os

# import xgboost  as xgb
from sklearn.metrics import mean_squared_error
from evaluation import get_validation_predicts_stat, get_validation_win_return

import warnings
warnings.filterwarnings("ignore")

# Train Path
TrainDataPath = "/data/user/018187/TrainValidData/Data2/TrainData.npy"
TrainLabelPath = "/data/user/018187/TrainValidData/Data2/TrainLabel.npy"
# Valid Path
ValidDataPath = "/data/user/018187/TrainValidData/Data2/ValidData.npy"
nnValidDataPath = "/data/user/000053/quanttest/saved/nntestfactors.npy"  # 32 factors after mlp
nnValidDataPath25 = "/data/user/000053/quanttest/saved/nntestfactors_25.npy"
ValidLabelPath = "/data/user/018187/TrainValidData/Data2/ValidLabel.npy"

buy = True  # tag_index % 2 == 0, by defaults

# TrainSet: 
#TrainData = np.load(TrainDataPath, allow_pickle=True)
#TrainLabel = np.load(TrainLabelPath, allow_pickle=True)
# x_train = TrainData


def test(modelname):
    # make a single model for each tag (0~5)
    myPrint("Loading Dataset =============================== ", "{0}/test_tag_0".format(modelname))
    ValidData = np.load(ValidDataPath, allow_pickle=True)
    ValidLabel = np.load(ValidLabelPath, allow_pickle=True)
    
    if modelname == "xgb":
        x_valid = ValidData
    # 使用 1组统一的非线性因子
    elif modelname == "nnfactors_xgb":
        nnValidData = np.load(nnValidDataPath, allow_pickle=True)
        ValidData = np.concatenate((ValidData, nnValidData), axis=1)  # combined with nn-factors
        x_valid = ValidData  # input: factors vectors
    elif modelname == "nnfactors_25_xgb":
        nnValidData = np.load(nnValidDataPath25, allow_pickle=True)
        ValidData = np.concatenate((ValidData, nnValidData), axis=1)  # combined with nn-factors
        x_valid = ValidData  # input: factors vectors       

    for tag_index in range(6):  # 6
        myPrint("------------------------------------------------ Tag_{} ! ---------------------------------------------".format(tag_index), "{0}/test_tag_0".format(modelname))
        
        
        """
        # 使用 6组独立的非线性因子
        if modelname == "separate_nnfactors_xgb":
            tempPath = "/data/user/000053/quanttest/saved/nntestfactors_tag_{}.npy".format(tag_index)
            nnValidData = np.load(tempPath, allow_pickle=True)
            x_valid = np.concatenate((ValidData, nnValidData), axis=1)  # combined with nn-factors
        """
                
        y_valid = ValidLabel[:,tag_index]
               
        # 1. bigxgb_tag_{}.pkl  -- 记得改xvalid
        # 2. nnfactors_xgb_tag_{}.pkl
        if os.path.isfile('/data/user/000053/quanttest/saved/{0}_tag_{1}.pkl'.format(modelname, tag_index)):
            with open('/data/user/000053/quanttest/saved/{0}_tag_{1}.pkl'.format(modelname, tag_index), 'rb') as fin:
                multi_xgb = pickle.load(fin)
        # 
        elif modelname == "separate_nnfactors_xgb":
            if os.path.isfile('/data/user/000053/quanttest/saved/seperate/nnfactors_xgb_tag_{}.pkl'.format(tag_index)):
                with open('/data/user/000053/quanttest/saved/seperate/nnfactors_xgb_tag_{}.pkl'.format(tag_index), 'rb') as fin:
                    multi_xgb = pickle.load(fin)
        
        # HIGHLIGHT THE {tag_index}-th MODEL!
        myPrint("This is the | {0} | model for tag_{1} #############################".format(modelname, tag_index), "{0}/test_tag_0".format(modelname))
        
        # Evaluate on Valid Set with `Default Evaluation Metrics`
        myPrint('Evaluate Valid Set ================================ {}'.format(showTime()), "{0}/test_tag_0".format(modelname))
        start = time.time()
        ypred_valid = multi_xgb.predict(x_valid)
        myPrint("End Prediction, Start Evaluation =============================== ", "{0}/test_tag_0".format(modelname))
        
        mse = mean_squared_error(y_valid, ypred_valid)
        acc, mse_str, rmse_str, mae_str, corr_str, predicts_str = get_validation_predicts_stat(y_valid, ypred_valid)
        end = time.time()
        # Detail evaluation info
        myPrint('(Lon and Lat) Valid MSE: %.5f' % mse + 'consume %.2f sec' % (end-start), "{0}/test_tag_0".format(modelname))
        myPrint(rmse_str + '\n' + mae_str + '\n\n' + acc + corr_str, "{0}/test_tag_0".format(modelname))
        myPrint("Predicts range:  \n" + predicts_str + '\n', "{0}/test_tag_0".format(modelname))

        # Evaluation_func Parameter
        buy = True  # buy
        if tag_index % 2 != 0:  # sell
            buy = False
        # Evaluate `win-rate & return-rate` on Valid Set
        myPrint('Evaluate win&return rate on Valid Set {}================================'.format(tag_index), "{0}/test_tag_0".format(modelname))
        start = time.time()
        
        stock_num_str, win_str, return_rate_str, mean_return_rate_str = get_validation_win_return(y_valid, ypred_valid, buy=buy)
        end = time.time()
        # Detail evaluation info, return_rate的计量单位是千分比
        myPrint('End evaluation, consume {0: .2f} seconds ================================'.format(end-start), "{0}/test_tag_0".format(modelname))
        myPrint(stock_num_str + '\n\n' + win_str + '\n' + return_rate_str + '\n' + mean_return_rate_str, "{0}/test_tag_0".format(modelname))


if __name__ == "__main__":
    modelnames = ["xgb", "bigxgb", "nnfactors_xgb", "separate_nnfactors_xgb"]

    # test(modelnames[0])

    for modelname in modelnames:
        test(modelname)
