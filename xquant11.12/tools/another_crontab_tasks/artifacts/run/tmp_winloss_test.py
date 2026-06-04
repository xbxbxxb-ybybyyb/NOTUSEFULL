import sys
sys.path.insert(0, "..")
import os
import onnx
import json
import warnings
import time
warnings.filterwarnings('ignore')
import numpy as np
import pickle
from onnxmltools.convert import convert_xgboost
from skl2onnx.common.data_types import FloatTensorType, DoubleTensorType
import pandas as pd
from artifacts.model_metrics import compute_metrics, backtest_oneday
from artifacts import online_model, model_metrics, parse_format
from artifacts.utils import start_ray_cluster
import datetime as dt
import onnxruntime as rt
from xquant.factordata import FactorData
import ray
from xgboost import XGBRegressor, XGBClassifier
from joblib import Parallel, delayed
from xquant.xqutils.perf_profile import profile


model_config = {
        # 数据段配置
        "symbol_list": [],
        "train_start_time": "20210101",
        "train_end_time": "20230930",
        "valid_start_time": "20231001",
        "valid_end_time": "20231130",
        "test_start_time": "20231201",
        "test_end_time": "20240229",
        "factor_name_list": [],  # 按条数筛选后写入
        "tagger_name_list": ["LabelFirstPeak_th10_60s"],

        "data_config": {
            "data_type":"tick_l2p",
            "w_size": 1,
            "n_job": 2,
            "transform": True,
            "clip_type": "3sigma",
            "scaler_type": "z-score",
            "quantile": [0.02, 0.98],
            "tagger_limit": 60,
            "raw_name_list": [],
            "thres": [-0.020, 0.020],
            "other_factor_list": "",
            # 因子列表， 为空的话为全量
            "factor_json_path": ""
        },
        # 模型段配置
        "xgb_config": {
            'objective': 'reg:squarederror',
            'booster': 'gbtree',
            'tree_method': 'hist',
            'gamma': 0.5,
            'learning_rate': 0.02,
            'lambda': 2,
            'subsample': 0.7,
            'colsample_bytree': 0.7,
            'max_depth': 13,
            'n_estimators': 1300,
            'seed': 4,
        },
        "metrics": {"reg_eval_abs_limits": [1.0, 3.0],
                    "reg_eval_th": 0.5},
        "model_save_mode": ["pkl", "onnx"],
    }

import sys
sys.path.insert(0, "/tmp/pycharm_project_710/exp_assembles/")
sys.path.append("/data/user/013150/exp_result/plot_tmp/HeatMap_release")
import artifacts
import importlib
from artifacts import exp_artifacts, save_to_mongo, model_save_and_evaluate,utils, factor_save_and_evaluate
from artifacts import parse_format, backtest_save_and_evaluate, model_plot, online_model, model_metrics
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from artifacts import backtest_plot
from artifacts import flying_functions
importlib.reload(artifacts)
importlib.reload(exp_artifacts)
importlib.reload(save_to_mongo)
importlib.reload(model_save_and_evaluate)
importlib.reload(factor_save_and_evaluate)
importlib.reload(parse_format)
importlib.reload(backtest_save_and_evaluate)
importlib.reload(model_plot)
importlib.reload(online_model)
importlib.reload(model_metrics)
importlib.reload(backtest_plot)
importlib.reload(utils)
importlib.reload(flying_functions)
print(artifacts)
import Stock_HeatMap_v1
importlib.reload(Stock_HeatMap_v1)
from Stock_HeatMap_v1 import Stock_HeatMap
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import plotly.figure_factory as ff
import plotly.io as pio
from plotly.graph_objs import *
from plotly.subplots import make_subplots
import os
import json
import polars as pl
import copy
import shutil
import ray


#################################################
flying_factor = ["PriceSpread", "OneBigOrder", "CumOrdersNetVolOverV0", "BreakingP0NumOrders"]
# flying_factor = pd.read_csv("extra_factors.csv", header=None)[0].tolist()

model_config["data_config"]["flying_factor"] = flying_factor
model_config["train_start_time"] = "20220101"
model_config["train_end_time"] = "20240320"
model_config["valid_start_time"] = "20240321"
model_config["valid_end_time"] = "20240425"
model_config["test_start_time"] = "20240426"
model_config["test_end_time"] = "20240520"

cached_norm_dataset = "/dfs/group/800657/exp_results/zz500_dataset"
flying_base_dir = "/dfs/group/800657/library/l3_event/event_data"
label_name, exp_name,version_alias = ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4_train_without", 'LabelFirstPeak_th12_60s_factor98')
label_name, exp_name,version_alias = ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98')
label_name, exp_name,version_alias = ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_amp')
label_name, exp_name,version_alias = ("LabelLongTwoMin", "exp_l3_zzkc_flying4", 'LabelLongTwoMin_factor98_amp')
label_name, exp_name,version_alias = ("LabelShortTwoMin", "exp_l3_zzkc_flying4", 'LabelShortTwoMin_factor98_amp')
label_name, exp_name,version_alias = ("LabelLongOneMin", "exp_l3_zzkc_flying4", 'LabelLongOneMin_factor98_amp')
label_name, exp_name,version_alias = ("LabelShortOneMin", "exp_l3_zzkc_flying4", 'LabelShortOneMin_factor98_amp')

model_config["tagger_name_list"][0] = label_name

######################################
fp = FactorProvider('016884')
expa = exp_artifacts.ExpArtifacts(exp_name = exp_name)
exp_path = expa.exp_path
expa.activate_version_to_save(model_config, version_alias = version_alias)
exp_version_path = expa.path_of_exp_version()
if True:
    model_config = json.load(open(os.path.join(exp_version_path, "params_jsonstr.json"), "r"))
    select_factors= model_config["factor_name_list"]
    flying_factor = model_config["data_config"]["flying_factor"]
    # pd.read_csv("kc50.csv", header=None)[0].tolist()
    SYMBOL_LIST = model_config["symbol_list"]
    print("SYMBOL_LIST:", len(SYMBOL_LIST))
    print("select_factors:", len(select_factors))
else:
#     model_config["factor_name_list"] = pd.read_csv(os.path.join(exp_version_path, "saved_models/factors.csv"), header=None)[0].tolist()
    flying_factor = ["PriceSpread", "OneBigOrder", "CumOrdersNetVolOverV0", "BreakingP0NumOrders"]
    model_config["data_config"]["flying_factor"] = flying_factor
    symbols = pd.read_csv(os.path.join(cached_norm_dataset, "kc_amt_swing.csv"), header=None)[0].tolist()
    symbols1 = pd.read_csv(os.path.join(cached_norm_dataset, "zz500_select74.csv"), header=None)[0].tolist()
    SYMBOL_LIST = list(sorted(set(symbols + symbols1)))
    model_config["symbol_list"] = SYMBOL_LIST
    print("SYMBOL_LIST:", len(SYMBOL_LIST))
    print("select_factors:", len(select_factors))

#     print(flying_factor)



def get_l2p_data(symbol, start_date, end_date):
    if symbol.endswith("SH"):
        mkt_type = "sh_stock_tick_l2p_persec"
    elif symbol.endswith("SZ"):
        mkt_type = "sz_stock_tick_l2p_persec"
    else:
        raise Exception()
    try:
        start_date = start_date.replace("-", "")
        end_date = end_date.replace("-", "")
        l2p_df = fp.get_market_data(symbol,start_date,end_date,tableName=mkt_type)
    except:
        print("get_l2p_data ERROR:", symbol, start_date, end_date)
    if len(l2p_df)==0:
        return pl.DataFrame()
    l2p_df = pl.from_pandas(l2p_df[["M_MDDate", "M_MDTime", "M_BuyPrice","M_SellPrice", "M_BuyOrderQty","M_SellOrderQty", "M_OpenPx" ]])
    l2p_df = l2p_df.with_columns(
        pl.concat_str(
        pl.col("M_MDDate").cast(str).str.slice(0,11), pl.col("M_MDTime")).alias("DateTime")
    )
    l2p_df = l2p_df.with_columns(
        pl.col("DateTime").str.strptime(dtype=pl.Datetime, format="%Y-%m-%d %H:%M:%S", strict=False).dt.cast_time_unit("ns"),
        pl.col("M_SellPrice").list[0].alias("Ask1P"),
        pl.col("M_BuyPrice").list[0].alias("Bid1P")
    )
    return l2p_df



def winloss_func(source_signal_df, long_pred_th, short_pred_th, start_date="2023-12-06", end_date="2024-02-06", use_self_prob = False, local_mode = False, t_sta="09:33:00"):
    # from artifacts.model_save_and_evaluate import model_signal_evaluation_winloss_stop_table_daily
    res_dict = model_signal_evaluation_winloss_stop_table_daily(source_signal_df,
                                                                long_pred_th=long_pred_th,
                                                                short_pred_th=short_pred_th,
                                                                win_limits=[0.0015],
                                                                loss_limits=[0.002],
                                                                t_sta=t_sta,
                                                                use_self_prob=use_self_prob,
                                                                local_mode = local_mode
                                                                )
    res_df = res_dict[(0.001, 0.002)]
    start_date = pd.to_datetime(start_date).strftime("%Y-%m-%d")
    end_date = pd.to_datetime(end_date).strftime("%Y-%m-%d")
    res_df = res_df[(res_df.index >= start_date) & (res_df.index <= end_date)]

    up_win_tol = round(res_df["涨信号止盈个数"].sum() / res_df["涨信号个数"].sum(), 3) if res_df["涨信号个数"].sum() else 0
    up_eq_tol = round(res_df["涨信号平个数"].sum() / res_df["涨信号个数"].sum(), 3) if res_df["涨信号个数"].sum() else 0
    up_loss_tol = round(res_df["涨信号止损个数"].sum() / res_df["涨信号个数"].sum(), 3) if res_df["涨信号个数"].sum() else 0
    up_num_tol = round(res_df["涨信号个数"].sum(), 3)
    up_win_day = round(res_df.mean()["涨信号止盈率"], 3)
    up_loss_day = round(res_df.mean()["涨信号止损率"], 3)
    up_eq_day = round(res_df.mean()["涨信号平率"], 3)
    up_num_day = round(res_df.mean()["涨信号个数"], 3)

    dw_win_tol = round(res_df["跌信号止盈个数"].sum() / res_df["跌信号个数"].sum(), 3) if res_df["跌信号个数"].sum() else 0
    dw_eq_tol = round(res_df["跌信号平个数"].sum() / res_df["跌信号个数"].sum(), 3) if res_df["跌信号个数"].sum() else 0
    dw_loss_tol = round(res_df["跌信号止损个数"].sum() / res_df["跌信号个数"].sum(), 3) if res_df["跌信号个数"].sum() else 0
    dw_num_tol = round(res_df["跌信号个数"].sum(), 3)
    dw_win_day = round(res_df.mean()["跌信号止盈率"], 3)
    dw_loss_day = round(res_df.mean()["跌信号止损率"], 3)
    dw_eq_day = round(res_df.mean()["跌信号平率"], 3)
    dw_num_day = round(res_df.mean()["跌信号个数"], 3)

    print(f"涨信号【总体】：信号个数: {up_num_tol}， 止盈率：{up_win_tol}, 平率： {up_eq_tol}， 止损率： {up_loss_tol}")
    print(f"跌信号【总体】：信号个数: {dw_num_tol}，止盈率：{dw_win_tol}, 平率： {dw_eq_tol}， 止损率： {dw_loss_tol}")
    print(f"涨信号日均：信号个数: {up_num_day}，止盈率：{up_win_day}，平率：{up_eq_day}, 止损率：{up_loss_day}")
    print(f"跌信号日均：信号个数: {dw_num_day}，止盈率：{dw_win_day}，平率：{dw_eq_day}, 止损率：{dw_loss_day}")
    eva_dict = {"涨信号总体": {"信号个数": up_num_tol, "止盈率": up_win_tol, "平率": up_eq_tol, "止损率": up_loss_tol},
                "跌信号总体": {"信号个数": dw_num_tol, "止盈率": dw_win_tol, "平率": dw_eq_tol, "止损率": dw_loss_tol},
                "涨信号日均": {"信号个数": up_num_day, "止盈率": up_win_day, "平率": up_eq_day, "止损率": up_loss_day},
                "跌信号日均": {"信号个数": dw_num_day, "止盈率": dw_win_day, "平率": dw_eq_day, "止损率": dw_loss_day}}
    #     eva_dict = {"涨总信号个数": up_num_tol, "涨总止盈率":up_win_tol, "涨总平率": up_eq_tol, "涨总止损率": up_loss_tol,
    #         "涨信号个数": dw_num_tol,"涨总止盈率":dw_win_tol,"涨总平率": dw_eq_tol, "涨总止损率": dw_loss_tol,
    #         "涨总信号个数": up_num_day,"涨总止盈率":up_win_day,"涨日均平率":up_eq_day, "涨日均止损率":up_loss_day,
    #         "跌日信号个数": dw_num_day,"跌日均止盈率":dw_win_day,"跌日均平率":dw_eq_day, "跌日均止损率":dw_loss_day}
    return res_df


@profile
def model_signal_evaluation_winloss_stop_table_daily(signal_df, long_pred_th = 1.2, short_pred_th = -1.2, win_limits = [0.0015,0.002], loss_limits = [0.002], t_sta="09:33:00", use_self_prob = False, local_mode = False):
    """
    统计单天信号，在指定止盈止损线情况下的，止盈止损率
    :param signal_df: 标准的信号原始DataFram
    :param long_pred_th: 有效信号的上涨阈值
    :param short_pred_th: 有效信号的下跌阈值
    :param win_limits:
    :param loss_limits:
    :param t_sta: 计算有效信号的开始时间,
    :param use_self_prob: 是否使用signal_df中自带的PROBABILITY字段
    :return:
    """
    if not "PREDICT" in signal_df.columns:
        signal_df["PREDICT"] = signal_df["PREDICTED"]
    if not "PREDICTED" in signal_df.columns:
        signal_df["PREDICTED"] = signal_df["PREDICT"]
    assert type(win_limits)==list and type(loss_limits)==list, "win_limits和loss_limits必须为list类型"
    if not use_self_prob:
        signal_df["PROBABILITY"] = signal_df["PREDICT"].apply(lambda x:online_model.reg2cls_v3(x, minMap = -6, maxMap = 6, long_pred_th = long_pred_th, short_pred_th = short_pred_th))

    import polars as pl
    signal_df = pl.from_pandas(signal_df)
    t_sta = int(t_sta.replace(":", ""))
    try:
        df1 = signal_df.with_columns(
            PERIOD_BEGIN=pl.col("PERIOD_BEGIN").str.strptime(dtype=pl.Datetime, format="%Y-%m-%d %H:%M:%S"),
            PERIOD_END=pl.col("PERIOD_END").str.strptime(dtype=pl.Datetime, format="%Y-%m-%d %H:%M:%S"),
            )
    except:
        df1 = signal_df
    df1 = df1.with_columns(Date=pl.col("PERIOD_BEGIN").dt.strftime("%Y-%m-%d"),
                           DateTime=pl.col("PERIOD_BEGIN"),
                           TimeStamp=pl.col("PERIOD_BEGIN").dt.replace_time_zone("Asia/Shanghai").dt.timestamp(
                               time_unit="ms"),
                           PERIOD_BEGIN=pl.col("PERIOD_BEGIN").dt.strftime("%H%M%S").cast(pl.Int32),
                           PERIOD_END=pl.col("PERIOD_END").dt.strftime("%H%M%S").cast(pl.Int32),
                           cls=pl.col("PROBABILITY").list.arg_max()
                           ). \
        with_columns(up=pl.when(pl.col("cls") > 2).then(pl.col("TARGET_VALUE")).otherwise(np.nan),
                     dw=pl.when(pl.col("cls") < 2).then(pl.col("TARGET_VALUE")).otherwise(np.nan),
                     ). \
        filter(pl.col("PERIOD_BEGIN") >= t_sta)
    df1 = df1.sort(by="DateTime")
    symbol = signal_df["SYMBOL"][0]
    start_date ,end_date = df1["Date"].min(), df1["Date"].max()
    l2p_df = get_l2p_data(symbol, start_date, end_date).select(["DateTime","Ask1P", "Bid1P", "M_OpenPx"])
    df1 = df1.join(l2p_df, on = "DateTime")
    df = df1.to_pandas().reset_index(drop=True)
    print(df)


    res_dict = {}
    dates = sorted(list(set(df['Date'])))
    if not local_mode:
        start_ray_cluster(num_cpus = 10, restart = False)
        remote_func = ray.remote(find_stop)
        for win_ratio in win_limits:
            for loss_ratio in loss_limits:
                tasks = [remote_func.remote(
                    df[df['Date'] == i],
                    win_ratio,
                    loss_ratio
                ) for i in dates]
                res_tmp = ray.get(tasks)
                res = pd.concat(res_tmp)
                res = res.sort_index()
                res['止盈线'] = win_ratio
                res['止损线'] = loss_ratio
            res_dict[(win_ratio, loss_ratio)] = res
        # ray.shutdown()
    else:
        for win_ratio in win_limits:
            for loss_ratio in loss_limits:
                res_tmp = [find_stop(
                    df[df['Date'] == i],
                    win_ratio,
                    loss_ratio
                ) for i in dates]
                res = pd.concat(res_tmp)
                res = res.sort_index()
                res['止盈线'] = win_ratio
                res['止损线'] = loss_ratio
            res_dict[(win_ratio, loss_ratio)] = res

    return res_dict


def judge_long(lis, profit, loss):
    for i in lis:
        if i >= profit:
            return 2
        if i <= loss:
            return 0
    return 1
def judge_short(lis, profit, loss):
    for i in lis:
        if i <= profit:
            return 2
        if i >= loss:
            return 0
    return 1

def find_stop(signal_df, profit_ratio, loss_ratio):
    """
    计算有效信号的止盈率，止损率
    :param signal_df: 标准的DataFrame列，此外还必须有PROBABILITY，五分类列
    :param profit_ratio:
    :param loss_ratio:
    :return:
    """
    df = signal_df.reset_index()
    res_lis = []
    res_up_down = pd.DataFrame()
    info_dic = {"up_up":0,
                "up_0" :0,
                "up_dw":0,
                "dw_up":0,
                "dw_0" :0,
                "dw_dw":0
               }
    valid_df = df[df["cls"]!=2]
    for idx,row in valid_df.iterrows():
        if row["cls"] != 2:
            t1 = row["PERIOD_BEGIN"]
            t2 = row["PERIOD_END"]
            #print(t1,t2)
            try:
                idx2 = df.loc[df["PERIOD_BEGIN"] >= t2].index[0]
            except:
                idx2 = df.index[-1]
            #print(idx, idx2)
            tmp = df.iloc[idx:idx2]
            #print(t1,t2, row["TARGET_VALUE"] )

            if row["cls"] > 2:  # 看涨
                start_price_col = "Ask1P"
                end_price_col = "Bid1P"
                profit = row[start_price_col] * (1 + profit_ratio)
                loss =   row[start_price_col] * (1 - loss_ratio)
                res = judge_long(list(tmp[end_price_col]), profit, loss)
                #print(res)
                if res == 2:
                    info_dic["up_up"] += 1
                if res == 1:
                    info_dic["up_0"] += 1
                if res == 0:
                    info_dic["up_dw"] += 1
                #print("看涨", t1,t2, row["TARGET_VALUE"],res )
            else:               # 看跌
                start_price_col = "Bid1P"
                end_price_col = "Ask1P"
                profit = row[start_price_col] * (1 - profit_ratio)
                loss =   row[start_price_col] * (1 + loss_ratio)
                res = judge_short(list(tmp[end_price_col]), profit, loss)
                if res == 2:
                    info_dic["dw_dw"] += 1
                if res == 1:
                    info_dic["dw_0"] += 1
                if res == 0:
                    info_dic["dw_up"] += 1
                #print("看跌", t1,t2, row["TARGET_VALUE"],res )
        else:
            res = np.nan
        res_lis.append(res)
    #print(info_dic)
    up_total = info_dic["up_up"] + info_dic["up_0"] + info_dic["up_dw"]
#     try:
#         print("涨： 共{}个\t 止盈率：{}\t 平率：{}\t 止损率：{}".format(up_total,  round(info_dic["up_up"]/up_total,4),
#                                                                     round(info_dic["up_0"] /up_total,4),
#                                                                     round(info_dic["up_dw"]/up_total,4) ))
#     except:
#         pass
    dw_total = info_dic["dw_up"] + info_dic["dw_0"] + info_dic["dw_dw"]
#     try:
#         print("跌： 共{}个\t 止盈率：{}\t 平率：{}\t 止损率：{}".format(dw_total,  round(info_dic["dw_dw"]/dw_total,4),
#                                                                     round(info_dic["dw_0"] /dw_total,4),
#                                                                     round(info_dic["dw_up"]/dw_total,4) ))
#     except:
#         pass
    up_zero = False
    dw_zero = False
    try:
        if not up_total:
            up_total = 1
            up_zero= True
        if not dw_total:
            dw_total = 1
            dw_zero = True
        res_up_down = pd.DataFrame(
            {'涨信号个数': up_total, '涨信号止盈个数': info_dic["up_up"], '涨信号平个数': info_dic["up_0"], '涨信号止损个数': info_dic["up_dw"],
             '涨信号止盈率': round(info_dic["up_up"] / up_total, 4) if up_total else 0, '涨信号平率': round(info_dic["up_0"] / up_total, 4) if up_total else 0,
             '涨信号止损率': round(info_dic["up_dw"] / up_total, 4) if up_total else 0,
             '跌信号个数': dw_total, '跌信号止盈个数': info_dic["dw_dw"], '跌信号平个数': info_dic["dw_0"], '跌信号止损个数': info_dic["dw_up"],
             '跌信号止盈率': round(info_dic["dw_dw"] / dw_total, 4) if dw_total else 0, '跌信号平率': round(info_dic["dw_0"] / dw_total, 4) if dw_total else 0,
             '跌信号止损率': round(info_dic["dw_up"] / dw_total, 4) if dw_total else 0},
            index=[df.iloc[0]['Date']])
        res_up_down['止盈率'] = profit_ratio
        res_up_down['止损率'] = loss_ratio
        if up_zero:
            res_up_down["涨信号个数"] = 0
        if dw_zero:
            res_up_down["跌信号个数"] = 0
    except Exception as e:
        print(e)
    #     print('Done!')
    return res_up_down

if __name__=="__main__":
    print(winloss_func)
    result_list = []
    long_pred_th = 2.0
    short_pred_th = -1.0
    start_date = "20240426"  # model_config["test_start_time"]
    end_date = "20240520"  # model_config["test_end_time"]
    symbols = model_config["symbol_list"]
    symbols = ["688256.SH"]  # ["688012.SH","688041.SH","688047.SH","688256.SH","688271.SH","688498.SH","688506.SH", "688017.SH"]

    for symbol_name in symbols:
        try:
            print(
                "=====================" + symbol_name + ":" + f"[{long_pred_th}, {short_pred_th}]" + "=====================")
            source_signal_df = expa.model_signal_load(version_alias, label_name, symbol_name)
            # source_signal_df = source_signal_df[source_signal_df["DATE"]=="2024-05-16"]
            source_signal_df["SYMBOL"] = symbol_name
            # 只统计采样点的准确率
            source_signal_df["PREDICTED"] = source_signal_df["PREDICTED"] * source_signal_df["flying_flag"]
            source_signal_df["PREDICT"] = source_signal_df["PREDICT"] * source_signal_df["flying_flag"]
            res_df = winloss_func(source_signal_df, long_pred_th, short_pred_th,
                                  start_date=start_date, end_date=end_date, local_mode = True)
            res_df["总止盈率"] = (res_df["涨信号止盈个数"] + res_df["跌信号止盈个数"]) / (res_df["涨信号个数"] + res_df["跌信号个数"])
            res_df["总止损率"] = (res_df["涨信号止损个数"] + res_df["跌信号止损个数"]) / (res_df["涨信号个数"] + res_df["跌信号个数"])
            res_df["总平率"] = (res_df["涨信号平个数"] + res_df["跌信号平个数"]) / (res_df["涨信号个数"] + res_df["跌信号个数"])
            res_df["总信号个数"] = (res_df["涨信号个数"] + res_df["跌信号个数"])
            #     res_df["信号质量加权"] = (res_df["涨信号止盈个数"]+res_df["跌信号止盈个数"])*1-(res_df["涨信号止损个数"]+res_df["跌信号止盈个数"])*1-0.5*(res_df["涨信号平个数"]+res_df["跌信号平个数"])
            res_df["信号质量加权"] = (res_df["总止盈率"] * 1 - res_df["总止损率"] * 2.5 - res_df["总平率"] * 0.5)
            #     display(res_df)
            #     res_dict[(0.0015, 0.002)].to_csv(os.path.join(exp_version_path,
            #                                "pred_th_win_loss_{}_{}_{}.csv".format(1,5, model_config["test_start_time"], model_config["test_end_time"])))
            #     display(res_dict[(0.0015, 0.002)][res_dict[(0.0015, 0.002)].index<"2024-02-06"].mean())
            a = res_df["涨信号止盈个数"].sum() + res_df["跌信号止盈个数"].sum()
            b = res_df["涨信号止损个数"].sum() + res_df["跌信号止损个数"].sum()
            c = res_df["涨信号平个数"].sum() + res_df["跌信号平个数"].sum()
            aa = res_df["总信号个数"].sum()
            w = {symbol_name: {"信号质量加权": (a - 2.5 * b - 0.5 * c) / aa}}
            print(w)
            print(res_df)
            result_list.append(w)
        except Exception as e:
            import traceback
            print(traceback.print_exc())
            print(e)
            pass
    ray.shutdown()
