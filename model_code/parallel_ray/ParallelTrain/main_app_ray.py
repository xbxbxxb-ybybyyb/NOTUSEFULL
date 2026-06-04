import os
os.system("pip install --upgrade pip")
# os.system("pip install -U --trusted-host 168.7.17.225 -i http://168.7.17.225:8081/repository/pypi/simple/ xgboost==1.5.1")
import ray
import pandas as pd
from parallel_train.entry import train
from parallel_train.api import SplitTaskParam, RayParams
from DataAPI.DataToolkit import *


def get_train_test_map(start_date, end_date, update_model_period):
    trading_day = get_trading_day(start_date, end_date)
    trading_day_fri = get_friday_trading_days(start_date, end_date)
    trading_day = get_trading_day(trading_day_fri[0], trading_day[-1])
    i_1 = 0
    train_test_map = {}
    temp_train_date = trading_day[0]
    for i in range(trading_day.__len__()-1):
        if i == 0 or (trading_day[i] in trading_day_fri and i - i_1 >= update_model_period):
            i_1 = i
            temp_train_date = trading_day[i]
        train_test_map.update({trading_day[i+1]: temp_train_date})
    return train_test_map


test_start_date = 20200111
test_end_date = 20200217
save_root_path = "/tmp/user/012620/own/Apollo/StrategySelectStockDay"
update_model_period = 5
strategy_types = ['vwap']
fs = pd.read_pickle("/data/user/013150/ai_data/factor_list.pkl")
factor_dict = {}
for time_ in strategy_types:
    # test_factor = list(pd.read_excel(factor_dir + factor_file_name, sheet_name=time_, header=None).values.flatten())
    factor_dict[time_] = fs

train_test_map = get_train_test_map(test_start_date, test_end_date, update_model_period)
train_date_list = sorted(list(set([v for k, v in (train_test_map.items())])))

data_params = {"train_date": SplitTaskParam(train_date_list*60),
               "strategy_type_factor": SplitTaskParam([(strategy_type, factor_list) for strategy_type, factor_list in factor_dict.items()]),
               "train_test_map":train_test_map,
               "label_name": 'vwap_re',
               'gap': 5,
               'train_window': 240,
               "save_root_path": save_root_path
               }
model_params = {"params": {'n_estimators': 1000, 'seed': 1993, 'nthread': 100, 'gamma': 5.0, 'min_child_weight': 0.5,
                           'reg_alpha': 50, 'reg_lambda': 10, 'max_depth': 8, 'learning_rate': 0.05, 'subsample': 0.9,
                           'colsample_bytree': 0.9, 'tree_method': 'gpu_hist'},
                "maximize": False,
                "eval_metric": ["mae"]
                }

#可参考parallel_train/readme.md查看详细使用说明。
#通过RayParams指定计算进程池的单个进程资源
# ray_params = RayParams(cpus_per_actor=4, gpus_per_actor=2, num_actors=2)
# train_additional_results = train(backend_actor="XGBWrapActor", data_params=data_params, model_params=model_params, ray_params = ray_params)
# print(train_additional_results)

for i in range(200):
    print(i,"*"*50)
    os.system("python3 parallel_train/trainer/XGBWrapActor.py")