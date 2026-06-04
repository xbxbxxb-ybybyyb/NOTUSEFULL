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
import pandas as pd
pd.set_option("display.max.rows", None)
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

import os
import json
import polars as pl

#################################################
SYMBOL_LIST = pd.read_csv("kc50.csv", header=None)[0].tolist()
SYMBOL_LIST = pd.read_csv("zz500_select74.csv", header=None)[0].tolist()


flying_factor = ["PriceSpread", "OneBigOrder", "CumOrdersNetVolOverV0", "BreakingP0NumOrders", "LevelOneChange"]
flying_factor = pd.read_csv("extra_factors.csv", header=None)[0].tolist()

model_config["data_config"]["flying_factor"] = flying_factor
model_config["symbol_list"] = SYMBOL_LIST
model_config["train_start_time"] = "20210101"
model_config["train_end_time"] = "20231015"
model_config["valid_start_time"] = "20231016"
model_config["valid_end_time"] = "20231214"
model_config["test_start_time"] = "20231215"
model_config["test_end_time"] = "20240422"

def bigrun(model_config):
    expa = exp_artifacts.ExpArtifacts(exp_name=exp_name)
    fp = FactorProvider('016884')
    exp_path = expa.exp_path
    expa.activate_version_to_save(model_config, version_alias=version_alias)
    exp_version_path = expa.path_of_exp_version()

    if True:
        model_config = json.load(open(os.path.join(exp_version_path, "params_jsonstr.json"), "r"))
        select_factors = model_config["factor_name_list"]
        flying_factor = model_config["data_config"]["flying_factor"]

    model_config["tagger_name_list"] = [label_name]  # "LabelFirstPeak_th10_60s"
    ######################################


    #     print(flying_factor)

    def winloss_func(source_signal_df, long_pred_th, short_pred_th, start_date="2023-12-06", end_date="2024-02-06", use_self_prob = False, local_mode = False):
        from artifacts.model_save_and_evaluate import model_signal_evaluation_winloss_stop_table_daily
        res_dict = model_signal_evaluation_winloss_stop_table_daily(source_signal_df,
                                                                    long_pred_th=long_pred_th,
                                                                    short_pred_th=short_pred_th,
                                                                    win_limits=[0.001, 0.0015, 0.002],
                                                                    loss_limits=[0.002],
                                                                    t_sta="09:33:00",
                                                                    use_self_prob=use_self_prob,
                                                                    local_mode = local_mode
                                                                    )
        res_df = res_dict[(0.002, 0.002)]
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

    def save_backtest_result(result_df, sheet_name, output_path = "/home/appadmin/signal.xlsx"):
        from openpyxl import load_workbook
        result_df = result_df.reset_index()
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl', mode = "a") as writer:
                df_strategy = result_df
                df_strategy.to_excel(writer, sheet_name = sheet_name, index=False)
                writer.save()
        except:
            with pd.ExcelWriter(output_path, engine='openpyxl', mode = "w") as writer:
                df_strategy = result_df
                df_strategy.to_excel(writer, sheet_name = sheet_name, index=False)
                writer.save()

    excel_path = os.path.join(exp_version_path, file_name)
    result_list = []
    for symbol_name in SYMBOL_LIST:
    #     if symbol_name !="688012.SH":
    #         continue
        try:
            print("====================="+symbol_name+":"+f"[{long_pred_th}, {short_pred_th}]"+"=====================")
            source_signal_df = expa.model_signal_load(version_alias, label_name, symbol_name)
            res_df = winloss_func(source_signal_df, long_pred_th, short_pred_th,
                                    start_date = "2023-12-15",end_date = "2024-04-30")
            res_df["总止盈率"] = (res_df["涨信号止盈个数"]+res_df["跌信号止盈个数"])/(res_df["涨信号个数"]+res_df["跌信号个数"])
            res_df["总止损率"] = (res_df["涨信号止损个数"]+res_df["跌信号止损个数"])/(res_df["涨信号个数"]+res_df["跌信号个数"])
            res_df["总平率"] = (res_df["涨信号平个数"]+res_df["跌信号平个数"])/(res_df["涨信号个数"]+res_df["跌信号个数"])
            res_df["总信号个数"] = (res_df["涨信号个数"]+res_df["跌信号个数"])
        #     res_df["信号质量加权"] = (res_df["涨信号止盈个数"]+res_df["跌信号止盈个数"])*1-(res_df["涨信号止损个数"]+res_df["跌信号止盈个数"])*1-0.5*(res_df["涨信号平个数"]+res_df["跌信号平个数"])
            res_df["信号质量加权"] = (res_df["总止盈率"]*1- res_df["总止损率"]*2.5-res_df["总平率"]*0.5)
        #     display(res_df)
        #     res_dict[(0.0015, 0.002)].to_csv(os.path.join(exp_version_path,
        #                                "pred_th_win_loss_{}_{}_{}.csv".format(1,5, model_config["test_start_time"], model_config["test_end_time"])))
        #     display(res_dict[(0.0015, 0.002)][res_dict[(0.0015, 0.002)].index<"2024-02-06"].mean())
            a = res_df["涨信号止盈个数"].sum()+res_df["跌信号止盈个数"].sum()
            b = res_df["涨信号止损个数"].sum()+res_df["跌信号止损个数"].sum()
            c = res_df["涨信号平个数"].sum()+res_df["跌信号平个数"].sum()
            aa = res_df["总信号个数"].sum()
            save_backtest_result(res_df, symbol_name, output_path = excel_path)
            w = {symbol_name:{"信号质量加权": (a-2.5*b-0.5*c)/aa}}
            print(w)
            result_list.append(w)
        except Exception as e:
            print(e)
            pass

    result_dict = {}
    excel_path = os.path.join(exp_version_path, file_name)
    for symbol in SYMBOL_LIST:
        try:
            res_df = pd.read_excel(excel_path, sheet_name=symbol)
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

            print(f"======================{symbol}========================")
            print(f"涨信号【总体】：信号个数: {up_num_tol}， 止盈率：{up_win_tol}, 平率： {up_eq_tol}， 止损率： {up_loss_tol}")
            print(f"跌信号【总体】：信号个数: {dw_num_tol}，止盈率：{dw_win_tol}, 平率： {dw_eq_tol}， 止损率： {dw_loss_tol}")
            print(f"涨信号日均：信号个数: {up_num_day}，止盈率：{up_win_day}，平率：{up_eq_day}, 止损率：{up_loss_day}")
            print(f"跌信号日均：信号个数: {dw_num_day}，止盈率：{dw_win_day}，平率：{dw_eq_day}, 止损率：{dw_loss_day}")

            eva_dict = {
                "涨跌总体": {
                    "总信号数": (up_num_tol + dw_num_tol) / len(res_df),
                    "止盈率": (res_df["涨信号止盈个数"].sum() + res_df["跌信号止盈个数"].sum()) / (up_num_tol + dw_num_tol),
                    "平率": (res_df["涨信号平个数"].sum() + res_df["跌信号平个数"].sum()) / (up_num_tol + dw_num_tol),
                    "止损率": (res_df["涨信号止损个数"].sum() + res_df["跌信号止损个数"].sum()) / (up_num_tol + dw_num_tol)
                },
                "涨信号总体": {"信号个数": up_num_tol, "止盈率": up_win_tol, "平率": up_eq_tol, "止损率": up_loss_tol},
                "跌信号总体": {"信号个数": dw_num_tol, "止盈率": dw_win_tol, "平率": dw_eq_tol, "止损率": dw_loss_tol}
            }
            eva_dict["涨跌总体"]["质量加权"] = eva_dict["涨跌总体"]["止盈率"] * 1 - eva_dict["涨跌总体"]["止损率"] * 2.5 - eva_dict["涨跌总体"][
                "平率"] * 0.5
            result_dict[symbol] = eva_dict
        except Exception as e:
            print(e)

    result_list = []
    for symbol in result_dict:
        df = pd.Series(result_dict[symbol]["涨跌总体"]).to_frame().T
        df.insert(0, "symbol", symbol)
        result_list.append(df)

    result_df = pd.concat(result_list).sort_values(by="质量加权", ascending=False).reset_index(drop=True)
    print(result_df)

if __name__=="__main__":
    exp_list = [
        ("LabelFirstPeak_th12_60s", "exp_l3_zz500_flying4", 'LabelFirstPeak_th12_60s'),
        # ("LabelLongOneMin", "exp_l3_zz500_flying4", 'LabelLongOneMin'),
        # ("LabelShortOneMin", "exp_l3_zz500_flying4", 'LabelShortOneMin'),
        # ("LabelLongTwoMin", "exp_l3_zz500_flying4", 'LabelLongTwoMin'),
        # ("LabelShortTwoMin", "exp_l3_zz500_flying4", 'LabelShortTwoMin')
    ]

    for label_name, exp_name, version_alias in exp_list:
        file_name = "signal_zz500_ls1.8_win2.0.xlsx"
        long_pred_th = 1.8
        short_pred_th = -1.8
        start_date = "2024-04-21"
        end_date = "2024-05-16"
        bigrun(model_config)


