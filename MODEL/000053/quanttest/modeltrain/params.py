import numpy as np

"""
+ n_estimators
+ verbosity
~ seed: 2022 -> 42
- early_stopping_rounds -> move to xgb.fit(early_stopping_rounds=50)
------------------------
? num_boost_round - didn't find in docs
- 'num_boost_round': 1024,
------------------------
UPDATE:
~ nthread -> n_jobs
~ seed -> random_state
"""

paramDict = {'base_score': 0,
 'booster': 'gbtree',
 'colsample_bylevel': 0.8,
 'colsample_bytree': 0.8,
 'eval_metric': 'rmse',
 'gamma': 1.0,
 'learning_rate': 0.05,
 'n_estimators': 1024,
 'max_bin': 512,
 'max_depth': 9,
 'min_child_weight': 5,
 'n_jobs': 6,
 'random_state': 42,
 'subsample': 0.8,
 'verbosity': 0,
 'tree_method': 'hist'}


paramDict_yangbo = {'base_score': 0,
 'booster': 'gbtree',
 'colsample_bylevel': 0.8,
 'colsample_bytree': 0.8,
 'early_stopping_rounds': 50,
 'eval_metric': 'rmse',
 'gamma': 1.0,
 'learning_rate': 0.05,
 'max_bin': 512,
 'max_depth': 9,
 'min_child_weight': 5,
 'nthread': 16,
 'num_boost_round': 1024,
 'seed': 2022,
 'subsample': 0.8,
 'verbosity': 0,
 'tree_method': 'hist'}

def checkcorrmat():
    ValidDataPath = "/data/user/018187/TrainValidData/Data2/ValidData.npy"
    nnValidDataPath = "/data/user/000053/quanttest/saved/nntestfactors.npy"  # 32 factors after mlp
    
    ValidData = np.load(ValidDataPath, allow_pickle=True)
    nnValidData = np.load(nnValidDataPath, allow_pickle=True)
    ValidData = np.concatenate((ValidData, nnValidData), axis=1)  # (all, 90)
    
    print("Building correlation matrix =================== ")
    corrmat = np.corrcoef(ValidData, rowvar=False)  # 90 * 90
    np.save("/data/user/000053/quanttest/saved/nnfactorscorrmat.npy", corrmat)
    
    # 新的非线性因子与所有90因子（包含本身），有多少个相关性>0.5
    newFactors = abs(corrmat[58:])  # 32 factors
    check = np.sum((newFactors > 0.5).astype(int), axis=1)
    print(check)

if __name__ == "__main__":
    corrmat = np.load("/data/user/000053/quanttest/saved/nnfactorscorrmat.npy", allow_pickle=True)[58:]
    print("Abs-Correlation > 0.2 of New nn-factors:")
    print("Corr between original 58 factors \n", np.sum(abs(corrmat[:,:58] > 0.2).astype(int), axis=1))
    print("Corr between new 32 factors \n", np.sum(abs(corrmat[:,58:] > 0.2).astype(int), axis=1))
    
    