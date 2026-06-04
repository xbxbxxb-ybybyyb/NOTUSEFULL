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
import artifacts
import importlib
importlib.reload(artifacts)


from artifacts import exp_artifacts, save_to_mongo, model_save_and_evaluate,utils, factor_save_and_evaluate
from artifacts import parse_format, backtest_save_and_evaluate, model_plot, online_model, model_metrics
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from artifacts import backtest_plot
import plotly.graph_objects as go
from artifacts import flying_functions
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
from artifacts.flying_functions import *
from xquant.marketdata import MarketData
ma = MarketData()

import os
import json
import polars as pl

#################################################
SYMBOL_LIST = pd.read_csv("kc50.csv", header=None)[0].tolist()

flying_factor = ["PriceSpread", "OneBigOrder", "CumOrdersNetVolOverV0", "BreakingP0NumOrders", "LevelOneChange"]
flying_factor = pd.read_csv("extra_factors.csv", header=None)[0].tolist()

model_config["data_config"]["flying_factor"] = flying_factor
model_config["symbol_list"] = SYMBOL_LIST
model_config["train_start_time"] = "20210101"
model_config["train_end_time"] = "20231015"
model_config["valid_start_time"] = "20231016"
model_config["valid_end_time"] = "20231214"
model_config["test_start_time"] = "20231215"
model_config["test_end_time"] = "20240327"
model_config["tagger_name_list"] = ["LabelFirstPeak_th12_60s"] #"LabelFirstPeak_th10_60s"
# exp_name = "exp_l3_kc50_th12_60s_extra59"
exp_name = "exp_l3_kc50_th12_60s"
version_alias = "xgboost_base"
label_name = model_config["tagger_name_list"][0]



######################################
fp = FactorProvider('016884')
expa = exp_artifacts.ExpArtifacts(exp_name = exp_name)
exp_path = expa.exp_path
expa.activate_version_to_save(model_config, version_alias = "xgboost_base")
exp_version_path = expa.path_of_exp_version()
if True:
    model_config = json.load(open(os.path.join(exp_version_path, "params_jsonstr.json"), "r"))
    select_factors= model_config["factor_name_list"]
    flying_factor = model_config["data_config"]["flying_factor"]
#     print(flying_factor)


for symbol in ["688012.SH", "688041.SH"]:
    long_pred_th, short_pred_th = 1.5, -1.5
    signal_df_all = expa.model_signal_load(version_alias=version_alias, label_name=label_name, symbol=symbol)
    dates = sorted(set(signal_df_all["DATE"].tolist()))
    print(dates)
    ma_df_all = ma.get_data_by_time_frame("STOCK", symbol, dates[0].replace("-", "")+" 093000000", dates[-1].replace("-", "")+" 150000000")

    save_path = "/home/appadmin/{}".format(symbol)
    os.makedirs(save_path, exist_ok=True)

    for date in tqdm(dates):
        signal_df = signal_df_all[signal_df_all["DATE"]==date]
        signal_df["DateTime"] = signal_df["PERIOD_BEGIN"]
        signal_df = signal_df.set_index("DateTime")
        signal_df_day = online_model.generate_probs_v3(signal_df["PREDICTED"], long_pred_th, short_pred_th, amp=6, period=120, target_value=signal_df["TARGET_VALUE"].values, target_type="mid")
        signal_df_day.to_parquet("{}/{}.parquet".format(save_path, date))

        print("=====================" + symbol + ":" + f"[{long_pred_th}, {short_pred_th}]" + "=====================")

        date = pd.to_datetime(date).strftime("%Y-%m-%d")
        eva_dict = flying_functions.winloss_func_dict(signal_df.copy(), long_pred_th, short_pred_th,
                              start_date=date, end_date=date)


        ma_df_day = ma_df_all[ma_df_all["MDDate"]==date.replace("-", "")]
        fig1, fig2 = backtest_save_and_evaluate.backtest_plot_signal_trade(signal_df_day, trade_records_df_day = pd.DataFrame(), ma_df_day = ma_df_day, plot_save_dir = save_path, plot_orderbook = False)


        res_df = pd.DataFrame(eva_dict).T.iloc[:2, :]
        res_df.insert(0, "方向", ["涨", "跌"])

        # 创建一个Figure对象并将表格添加进去
        fig1.add_trace(go.Table(
            header=dict(values=list(res_df.columns),
                        fill_color='paleturquoise',
                        align='left'),
            cells=dict(values=[res_df[col].tolist() for col in res_df.columns],
                       fill_color='lavender',
                       align='left')))
        with open(os.path.join(save_path, "{}.html".format(date)), "w") as f:
            f.write(fig1.to_html(full_html=False))
