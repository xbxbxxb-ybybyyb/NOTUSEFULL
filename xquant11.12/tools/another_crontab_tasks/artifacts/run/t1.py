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
import sys
sys.path.append("/data/user/013150/exp_result/plot_tmp/HeatMap_release")
import Stock_HeatMap_v1
import importlib
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


#################################################
flying_factor = ["PriceSpread", "OneBigOrder", "CumOrdersNetVolOverV0", "BreakingP0NumOrders", "LevelOneChange"]
flying_factor = pd.read_csv("extra_factors.csv", header=None)[0].tolist()

model_config["data_config"]["flying_factor"] = flying_factor
model_config["train_start_time"] = "20210101"
model_config["train_end_time"] = "20231015"
model_config["valid_start_time"] = "20231016"
model_config["valid_end_time"] = "20231214"
model_config["test_start_time"] = "20231215"
model_config["test_end_time"] = "20240422"

label_name, exp_name,version_alias = ("LabelFirstPeak_th10_120s", "unite_kc", 'unite_kc')
model_config["tagger_name_list"][0] = label_name

######################################
fp = FactorProvider('016884')
expa = exp_artifacts.ExpArtifacts(exp_name = exp_name)
exp_path = expa.exp_path
expa.activate_version_to_save(model_config, version_alias = version_alias)
exp_version_path = expa.path_of_exp_version()
if False:
    model_config = json.load(open(os.path.join(exp_version_path, "params_jsonstr.json"), "r"))
    select_factors= model_config["factor_name_list"]
    flying_factor = model_config["data_config"]["flying_factor"]
    # pd.read_csv("kc50.csv", header=None)[0].tolist()
    SYMBOL_LIST = model_config["symbol_list"]
    print("SYMBOL_LIST:", len(SYMBOL_LIST))
    print("select_factors:", len(select_factors))

#     print(flying_factor)


from artifacts import online_model, model_save_and_evaluate
import os
import json
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from xquant.factordata import FactorData
from tqdm import tqdm

fp = FactorProvider("016869")
factor_type = 'factor'
data_type = "enhanced_tick"#"tick_l2p"
symbol_list = ["688256.SH"]

start_date, end_date = "20240512", "20240516"
# start_date, end_date = "20240321", "20240416"

fa = FactorData()
from xquant.marketdata import MarketData

ma = MarketData()
dates = fa.tradingday(start_date, end_date)

winloss_result_list = []
for symbol in symbol_list[:1]:
    ma_df_all = ma.get_data_by_time_frame("STOCK", symbol, dates[0].replace("-", "") + " 093000000",
                                          dates[-1].replace("-", "") + " 150000000")
    long_pred_th, short_pred_th = 1.5, -1.5
    save_parquet_path = os.path.join(os.path.join("/home/appadmin/", f"signal_files/{label_name}-{symbol}.parquet"))
    for date in dates:
        model_base_dir = "/data/user/016869/AutoMiningFrame/trade_data/COO/unite_kc/unite_kc"
        # model_base_dir = exp_version_path
        save_parquet_path = os.path.join(os.path.join(model_base_dir, f"signal_files/{label_name}-{symbol}.parquet"))
        factor_name_list = pd.read_csv(os.path.join(model_base_dir, "factors.csv"), header = None).iloc[:,0].values.tolist()
        # factor_name_list = model_config["factor_name_list"]
        flying_factor = model_config["data_config"]["flying_factor"]
        # ########################生成采样数据###########################
        feature_label_df = load_factor_label(
            fp,
            data_type,
            date,
            date,
            symbol,
            factor_name_list,
            [label_name],
            model_config["data_config"]["tagger_limit"])
        flying_factor_df = load_flying_factors(symbol, dates=[date], use_pandas=False,
                                               flying_base_dir="/dfs/group/800657/library/l3_event/event_data")
        if len(flying_factor_df) == 0:
            continue
        flying_factor_df = flying_factor_df.to_pandas()
        flying_factor_df = flying_factor_df.set_index("DateTime")

        merge_df = pd.merge(feature_label_df, flying_factor_df, left_index=True, right_index=True, how="inner")
        print(merge_df)
        new_feature_label_df = merge_df[factor_name_list + [label_name] + flying_factor]
        print("feature_label_df: ", feature_label_df.shape, ", new_feature_label_df: ", new_feature_label_df.shape)
        if new_feature_label_df.empty:
            continue
        T_test, X_test, Y_test = get_prepared(new_feature_label_df, label_name,
                                              model_config["data_config"]["w_size"], parallel_mode=False)
        X_test = X_test  # [:, 0]
        Y_test = Y_test.flatten()
        print("T_test, X_test, Y_train: ", len(T_test), X_test.shape, Y_test.shape)
        # ########################预测信号###########################
        today = pd.DataFrame(X_test, columns=factor_name_list + flying_factor)
        #         factor_config = pd.read_json("/dfs/group/800657/exp_results/kc_dataset/{}_factor_config.json".format(symbol))
        factor_config = pd.read_json(
            os.path.join(exp_version_path, "{}_factor_config.json".format(symbol)))
        for j in range(len(factor_name_list)):
            factor_mean = factor_config[factor_name_list[j]].loc['mean']
            factor_std = factor_config[factor_name_list[j]].loc['std']
            clip_lower = factor_mean - 3 * factor_std
            clip_upper = factor_mean + 3 * factor_std
            cliped_df = today[factor_name_list[j]].clip(
                lower=clip_lower, upper=clip_upper)
            today[factor_name_list[j]] = (cliped_df.values - factor_mean) / factor_std
        today.iloc[0].sum()

        X_test_norm = today.values
        print("X_test_norm.shape:", X_test_norm.shape)

        if False:
            model_path = os.path.join(model_base_dir, "model.onnx")
            model_sess = online_model.load_onnx_model(model_path)
            model_input_name = model_sess.get_inputs()[0].name
            model_label_name = model_sess.get_outputs()[0].name
            rest = model_sess.run([model_label_name], {model_input_name: X_test_norm.astype(np.float32)})[0]
            Y_test_pred = np.array(yhat)
        else:
            if not xgb_regressor:
                xgb_regressor = pd.read_pickle(os.path.join(exp_version_path, "tmp_model.pickle.dat"))
            Y_test_pred = xgb_regressor.predict(X_test_norm)
        # ########################生成信号数据###########################
        factor_df_online = fp.load_public_data_from_dfs(symbol=[symbol], factor_list=["LabelReferenceMidPx"],
                                                        start_time=date, end_time=date,
                                                        factor_type="label", data_type=data_type)
        factor_df_online = factor_df_online[factor_df_online["timestamp"].isin(T_test)]
        target_values = factor_df_online["LabelReferenceMidPx"].values
        signal_df = model_save_and_evaluate.generate_signal_without_class(T_test, Y_test_pred, Y_test, target_values,
                                                                          period=120, target_type="mid")
        signal_df["flying_flag"] = merge_df["open_flying"].astype(int)
        signal_df["PREDICTED"] = signal_df["PREDICTED"] * signal_df["flying_flag"]
        signal_df["PREDICTED"] = signal_df["PREDICTED"] * signal_df["flying_flag"]
        signal_df.drop(columns=["flying_flag"], inplace=True)

        # 显示标签和预测值相关性
        res = pd.DataFrame(Y_test_pred, columns=["pred"])
        res["label"] = Y_test
        res = res[res["label"] > -100]
        print(date, res.corr())
        #         res.plot()

        #         #########################生成parquet文件########################
        # source_signal_df = pd.read_parquet(save_parquet_path)
        # source_signal_df = source_signal_df[~source_signal_df["DATE"].isin(set(signal_df["DATE"].tolist()))]
        # new_signal_df = pd.concat([source_signal_df, signal_df], axis=0)
        new_signal_df["STRATEGY_NAME"] = exp_name
        new_signal_df["SYMBOL"] = symbol
        print(new_signal_df)
        new_signal_df.to_parquet(save_parquet_path)


