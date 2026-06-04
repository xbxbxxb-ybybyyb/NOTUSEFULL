import shap
import os
import sys
import time
sys.path.append("/data/user/016869/online_scripts/star_project/star_model")
# from backtest_scripts import *
# from backtest_utils import *
from factor_select import *
from factor_select import *
# from local_eval_stats import *
from joblib import Parallel, delayed
from online_check.utils import *
from src.utils.plot_backtest_results import *


from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider

s = FactorData()
fd = FactorProvider(userID="016884")

symbol = "688599.SH"
t_sta = "20200701"

exp_name = symbol + "_trade_v1.2"
exp_path = "exp_result/" + exp_name + "/"
if not os.path.exists(exp_path):
    os.makedirs(exp_path)

if not os.path.exists(exp_path + "saved_models/"):
    os.makedirs(exp_path + "saved_models/")

label_name = "labelEQtriplebarriertaggerv2pricetypeEQmidpricedsizeEQ120barrierEQ1"

config = {
    # 数据段配置
    "data_config": {
        "symbol": symbol,
        # "train_start_time": "20200701",
        # "train_end_time": "20220901",
        # "valid_start_time": "20220902",
        # "valid_end_time": "20230228",
        # "test_start_time": "20230301",
        # "test_end_time": "20230705",

        "train_start_time" : "20200701",
        "train_end_time"   : "20200730",
        "valid_start_time" : "20200701",
        "valid_end_time"   : "20200730",
        "test_start_time"  : "20200701",
        "test_end_time"    : "20200730",

        "main_stocks": symbol,
        "w_size": 1,
        "n_job": 4,
        "transform": True,
        "clip_type": "3sigma",
        "scaler_type": "z-score",
        "quantile": [0.02, 0.98],
        "factor_name_list": [],  # 按条数筛选后写入
        "tagger_name_list": ["labelEQtriplebarriertaggerv2pricetypeEQmidpricedsizeEQ120barrierEQ1"],
        "raw_name_list": [],
        "model_dir": exp_path + "saved_models/",
        "thres": [0.02, 0.02],
        "from_file": ""},
    # 模型段配置
    "xgb_config": {
        'objective': 'reg:squarederror',
        'booster': 'gbtree',
        'gamma': 0.5,
        'learning_rate': 0.01,
        'lambda': 2,
        'subsample': 0.7,
        'colsample_bytree': 0.7,
        'max_depth': 12,
        'n_estimators': 1500,
        'seed': 1},
    "metrics": {"reg_eval_abs_limits": [1.0, 3.0],
                "reg_eval_th": 0.5},
    "model": {"name": "mlp"},
    "optimizer": {"name": "adam", "lr": 0.001, },
    "model_dir": exp_path + "saved_models/",
    "criterion": {"name": "mse"},
    "Exp_path": exp_path,
    "factor_json_path": "",
    "exclude_json_path": "/data/user/019771/XC/star_project/star_model/src/configs/factor_exclude.json",
    "Model_save_mode": ["pkl", "onnx"],
    "n_jobs_model": 28
}


if __name__=="__main__":
    from tqdm import tqdm
    import ray
    ray.init(local_mode=False)
    t1 = time.time()
    chosen_config, chosen_config_path, dp = factor_select(config["data_config"], exp_path, n_jobs=4)
    for k,v in tqdm(enumerate(dp.train_dataset.normalized_data_list)):
        print(k, v.shape)
    ray.shutdown()
    print(time.time()-t1)