# 本脚本主要用于因子筛选
import json
import onnx
import torch
import warnings
warnings.filterwarnings('ignore')
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from xquant.factordata import FactorData
from src.data.RawData import RawData
from src.data.TaggerData import TaggerData
from analyzer.TickFactorBacktest import *
from src.data.data_pipeline import DataPipeline
from src.data.calculator import TagCalculator
from src.model.star_model import StarModel
from src.utils.utils import *
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
import time
from xquant.xqutils.perf_profile import profile

user_id = '016884'
# 获取个公共库中的因子名称
fd = FactorProvider(user_id)


def get_time(f):
    def inner(*arg,**kwarg):
        s_time = time.time()
        res = f(*arg,**kwarg)
        e_time = time.time()
        print('耗时：{}秒'.format(e_time - s_time))
        return res
    return inner


# @profile
def factor_select_by_cnt(symbol, t_sta, t_end, daily_avg_cnt=4200, return_factor_info = False):
    """筛选平均每日因子个数满足条件的因子
    params:
       symbol: str, 标的
       t_sta:  str, 验证期起始日期
       t_end:  str, 验证期终止日期
    return:
       factor_name_list: list, 满足条件的因子名集合
    """
    factor_name_list = list(fd.load_info_from_dfs('factor', source_type='personal'))
    factor_df = fd.load_personal_data_from_dfs(
        symbol=[symbol, ],
        factor_list=factor_name_list,
        start_time=t_sta,
        end_time=t_end,
        factor_type="factor"
    )
    factor_df.index = pd.to_datetime(factor_df.timestamp)
    if return_factor_info:
        factor_info_source = factor_df.describe()
        factor_info = factor_info_source.loc["count"]
    else:
        factor_info = factor_df.count()
        factors = [i for i in factor_info.index if i.startswith('Factor')] + ['ReferenceMidPrice']
        factor_info = factor_info[factor_info.index.isin(factors)]
    # factor_info.sort_values()
    trading_date_list = FactorData().tradingday(t_sta, t_end)
    factor_name_list = factor_info[factor_info > len(trading_date_list) * daily_avg_cnt].index.tolist()
    if not return_factor_info:
        return factor_name_list
    else:
        return factor_name_list, factor_info_source

# @profile
def factor_select_by_IC(data_config, label_name, n_jobs, thres=[0.2, 0.2]):
    """通过IC & RankIC 筛选因子
    params:
       data_config: dict, 数据流水线配置
       label_name:  str, label名称
       n_jobs:      str, 并发核数
       thres: list, 两个元素，第一个为IC阈值，第二个为RankIC阈值
    return:
       chosen_factor_config_dict: list, 满足条件的因子名集合
    """
    if not os.path.exists(data_config["model_dir"]):
        os.makedirs(data_config["model_dir"])
    dp = DataPipeline(data_config)
    dp.prepare_raw_dataset()
    analyzer = FactorBacktest(n_jobs)
    factor_label_list = analyzer.prepare_factor_label(dp, label=label_name)
    print("开始评价因子")
    t1 = time.time()
    all_factor_stats_df = analyzer.test_all_factor(factor_label_list, label=label_name)
    factor_info = all_factor_stats_df.groupby(
        all_factor_stats_df.test_factor).apply(np.mean)[["normal_ic", "rank_ic"]].fillna(0)
    print("评价因子耗时：", time.time()-t1)
    chosen_factor = factor_info[(abs(factor_info.normal_ic) >= thres[0]) | (abs(factor_info.rank_ic) >= thres[1])]
    return chosen_factor, dp

# @profile
def factor_select(config, output_path, n_jobs=20):
    """ 筛选因子Pipeline
    params:
       data_config: dict, 数据流水线配置
       output_path: 保存因子配置文件前缀
    return:
       chosen_factor_config_dict: list, 满足条件的因子名集合
    """
    t_sta = config["train_start_time"]
    t_end = config["valid_end_time"]
    symbol = config["symbol"]
    thres = config["thres"]
    label_name = config["tagger_name_list"][0]
    chosen_config_path = output_path + "_{}_{}.json".format(symbol, str(thres[0]).replace(".", ""))
    print("output_path", chosen_config_path)

    factor_name_list = factor_select_by_cnt(symbol, t_sta, t_end, daily_avg_cnt=4200)
    print("Filter Factors by cnt, Left {}".format(len(factor_name_list)))
    config["factor_name_list"] = factor_name_list

    # IC & RankIC filter
    factor_evl, dp = factor_select_by_IC(config, label_name, n_jobs, thres)
    print("Filter Factors by IC&RankIC, thres {}, Left {}".format(str(thres), len(factor_evl)))
    chosen_factor = ["ReferenceMidPrice"] + [v for v in factor_evl.index.tolist() if v.startswith("Factor")]
    print("Total Factor num: {}".format(len(chosen_factor)))

    # Save
    chosen_factor_config_dict = {"factor_name_list": chosen_factor}
    with open(chosen_config_path, "w") as f:
        json.dump(chosen_factor_config_dict, f, indent=4)
    factor_evl.to_csv(output_path + "_{}_{}.csv".format(symbol, str(thres[0]).replace(".", "")))
    print("Factor config saveed sucessfully to {}".format(chosen_config_path))

    return chosen_factor_config_dict, chosen_config_path, dp