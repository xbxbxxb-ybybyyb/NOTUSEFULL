from sklearn.model_selection._split import _BaseKFold,indexable,check_array
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor ,LGBMRanker   
import lightgbm as lgb
from sklearn.model_selection import GridSearchCV
import pandas as pd
import numpy as np

class GroupTimeSeriesSplit(_BaseKFold):
    def __init__(self,n_splits=3):
        super(GroupTimeSeriesSplit,self).__init__(n_splits,
            shuffle=False,random_state = None)
    def split(self,X,y=None,groups=None):
        X,y,groups = indexable(X,y,groups)
        n_splits = self.n_splits
        n_folds = n_splits + 1

        if groups is None:
            raise ValueError("The  'groups' parameter should not be  None.")
        groups = check_array(groups,ensure_2d=False,dtype=None)
        
        unique_groups = np.unique(groups,return_inverse=True)[0]
        n_groups = len(unique_groups)
        if n_groups%n_folds !=0:
            raise ValueError("Cannot have number of splits n_splits=%d not divisible"
                "by the number of groups:%d."
                %(self.n_splits,n_groups))
        groups = np.array(groups)
        n_groups_per_fold = n_groups//n_folds
        for n_split in range(n_splits):
            train_groups = unique_groups[0:n_groups_per_fold*(n_split+1)]
            test_groups = unique_groups[n_groups_per_fold*(n_split+1):n_groups_per_fold*(n_split+2)]
            yield(np.where(np.logical_and(groups>=train_groups[0],groups<=train_groups[-1]))[0],
                np.where(np.logical_and(groups>=test_groups[0],groups<=test_groups[-1]))[0])
start_date = '20190520'
end_date = '20200515'
path_sample = '/data/group/800020/AlphaDataCenter/Sample/NormSample/'#
close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl').loc[start_date:end_date]
dates = [i.strftime('%Y%m%d') for i in close.index]
sample_list = []
for day in dates:
    df = pd.read_pickle(path_sample+ day + '.pkl')
    sample_list.append(df)
training_sample = pd.concat(sample_list)
factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Sample/factor_list.pkl')
training_sample = training_sample[training_sample['date'].isin(dates[:-2])]
X = training_sample[factor_list]
y = training_sample['0930_1129_re_5d']
groups = training_sample['date']
xgb = LGBMRegressor(random_state=42,tree_method='gpu_hist', gpu_id=0,n_jobs=100)
parameters = [{'learning_rate':[0.01,0.025,0.05,0.075,0.1],
               'max_depth':[3,5,10,15],
               'subsample':[0.8,0.85,0.9,0.95]}]
gptscv = GroupTimeSeriesSplit(n_splits=4)
clf = GridSearchCV(estimator=xgb,param_grid = parameters,
                  cv = gptscv.split(X,y,groups),n_jobs=8)
clf.fit(X,y)