import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from utils import *
import pickle

# sklearn - 0.23.1
# xgb - 0.90.0
import xgboost  as xgb
#from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_squared_error
from evaluation import get_validation_predicts_stat

from params import paramDict
import warnings
warnings.filterwarnings("ignore")

# Path
TrainDataPath = "/data/user/018187/TrainValidData/Data2/TrainData.npy"
TrainLabelPath = "/data/user/018187/TrainValidData/Data2/TrainLabel.npy"
# 
ValidDataPath = "/data/user/018187/TrainValidData/Data2/ValidData.npy"
ValidLabelPath = "/data/user/018187/TrainValidData/Data2/ValidLabel.npy"

# TrainSet: 
TrainData = np.load(TrainDataPath, allow_pickle=True)
TrainLabel = np.load(TrainLabelPath, allow_pickle=True)
# ValidSet
ValidData = np.load(ValidDataPath, allow_pickle=True)
ValidLabel = np.load(ValidLabelPath, allow_pickle=True)

## Load Saved_model
#if os.path.isfile('/data/user/000053/quanttest/saved/xgb_tag_0.pkl'):
#    with open('/data/user/000053/quanttest/saved/xgb_tag_0.pkl', 'rb') as fin:
#        multi_xgb = pickle.load(fin)



# make a single model for each tag (0~5)
for tag_index in range(6):
    # Data prepared
    nnTrainDataPath = "/data/user/000053/quanttest/saved/nntrainfactors_tag_{}.npy".format(tag_index)
    nnValidDataPath = "/data/user/000053/quanttest/saved/nntestfactors_tag_{}.npy".format(tag_index)  # 32 factors after mlp
    
    nnTrainData = np.load(nnTrainDataPath, allow_pickle=True)
    TrainData = np.concatenate((TrainData, nnTrainData), axis=1)  # 58 + 32 = 90
    nnValidData = np.load(nnValidDataPath, allow_pickle=True)
    ValidData = np.concatenate((ValidData, nnValidData), axis=1)
    x_train = TrainData
    x_valid = ValidData 
    y_train = TrainLabel[:,tag_index]
    y_valid = ValidLabel[:,tag_index]

    multi_xgb = xgb.XGBRegressor(**paramDict)

    print("Start training ====================================\n", showTime())

    # 封装多目标（多输出）回归,边训边测
    multi_xgb.fit(x_train, y_train, eval_set=[(x_valid, y_valid)], eval_metric="rmse", early_stopping_rounds=100)
    print("End training ====================================\n", showTime())

    # Save xgb
    with open('/data/user/000053/quanttest/saved/seperate/nnfactors_xgb_tag_{}.pkl'.format(tag_index), 'wb') as handle:
        pickle.dump(multi_xgb, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # HIGHLIGHT THE {tag_index}-th MODEL!
    print("This is the model for tag_{} #############################".format(tag_index))
    
    # Evaluate on Valid Set
    print('Evaluate Valid Set ================================', showTime())
    start = time.time()
    mse = mean_squared_error(y_valid, multi_xgb.predict(x_valid))
    acc, mse_str, rmse_str, mae_str, corr_str, predicts_str = get_validation_predicts_stat(y_valid, multi_xgb.predict(x_valid))
    end = time.time()
    
    # Detail evaluation info
    print('(Lon and Lat) Valid MSE: %.5f' % mse, 'consume %.2f sec' % (end-start))
    print(rmse_str, '\n', mae_str, '\n', acc, '\n', corr_str, '\n')
    print("Predicts range:  \n", predicts_str, '\n')
