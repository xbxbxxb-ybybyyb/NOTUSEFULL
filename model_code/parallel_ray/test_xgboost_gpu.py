try:
    from tensorflow import keras
except:
    import keras
import xgboost as xgb
import time
#from xquant.model import log_metrics, log_params, parse_params, start_run
from sklearn import datasets
from sklearn.metrics import accuracy_score, log_loss
import gpustat
import platform

# print(platform.processor())
gpustat.print_gpustat()
(X_train, y_train), (X_test, y_test) = keras.datasets.mnist.load_data()
X_train = X_train.reshape(-1, 784)
X_test = X_test.reshape(-1,784)
dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)


# 某些目标函数没法传tree_mehod
# params = {
#         'n_estimators':100,
#         "objective": "multi:softprob",
#         'nthread': 10,
#         "num_class": 10,
#         "learning_rate": 0.3,
#         "eval_metric": "mlogloss",121
#         "colsample_bytree": 1.0,
#         "subsample": 1.0,
#         "seed": 40,
#         "tree_mothod":'gpu_hist'
#     }

params= {"booster": "gbtree",'n_estimators': 100, 'seed': 1993, 'nthread': 10, 'gamma': 5.0, 'min_child_weight': 0.5,
                               'reg_alpha': 50, 'reg_lambda': 10, 'max_depth': 8, 'learning_rate': 0.05,
                               'subsample': 0.9,
                               'colsample_bytree': 0.9, 'tree_method': 'gpu_hist', 'gpu_id': 0}
t1 = time.time()
model = xgb.train(params, dtrain, 30, evals=[(dtrain, "train")])
print("test_xgboost time:", time.time()-t1)
# evaluate model

