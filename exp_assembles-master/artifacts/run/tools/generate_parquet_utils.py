from artifacts import exp_artifacts
from artifacts.utils import save_and_append_parquet
from artifacts.flying_functions import *
from artifacts import online_model, model_save_and_evaluate
from artifacts.utils import save_winloss_data
from artifacts.parse_param import parse_target_type
import os
import json
import time
import shutil
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from xquant.factordata import FactorData
from xquant.marketdata import MarketData
from tqdm import tqdm
import pandas as pd
import numpy as np
import ray
import collections
import re

import polars as pl
from artifacts.model_metrics import winloss_stop_table_daily, find_stop_new
from artifacts.utils import save_and_append_parquet,get_cache_data_and_lack_param


model_config = {
    "data_config": {
        "data_type": "tick_l2p",
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
}

winloss_field_pattern = ["模型名称","日期", "标的", "总信号个数", "总止盈率", "总止损率", "总平率", "止盈线", "止损线", "预测阈值", "信号质量加权",
                         "涨信号个数", "涨信号止盈个数", "涨信号平个数", "涨信号止损个数", "涨信号止盈率",
                         "涨信号平率", "涨信号止损率", "跌信号个数", "跌信号止盈个数", "跌信号平个数",
                         "跌信号止损个数", "跌信号止盈率", "跌信号平率", "跌信号止损率",
                         ]

################################################################
def main_generate_parquet_l3(label_name, symbol, exp_version_path, start_date, end_date, data_type,
                             model_config, factor_type = 'factor', model_file_type = "pickle"):
    # global model_config
    try:
        fp = FactorProvider("016869")
        fa = FactorData()
        model = None
        # data_type = "enhanced_tick_norm"
        start_date = pd.to_datetime(start_date).strftime("%Y%m%d")
        end_date = pd.to_datetime(end_date).strftime("%Y%m%d")
        start_date = fa.tradingday(start_date, -3)[0]
        dates = fa.tradingday(start_date, end_date)
        signal_path = os.path.join(exp_version_path, "signal_files")
        os.makedirs(signal_path, exist_ok=True)

        save_parquet_path = os.path.join(os.path.join(exp_version_path, f"signal_files/{label_name}-{symbol}.parquet"))
        if not os.path.exists(os.path.join(exp_version_path, "saved_models/{}_factor_config.json".format(symbol))):
            print(f"该模型{exp_version_path}无法预测该标的{symbol}！")
            return
        for date in dates:
            factor_name_list = model_config["factor_name_list"]
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
                model_config["data_config"]["tagger_limit"],
                factor_type=factor_type,
                factor_only=True
            )
            flying_factor_df = load_flying_factors(symbol, dates = [date],  flying_base_dir = "/dfs/group/800657/library/l3_event/event_data")
            if len(flying_factor_df)==0:
                print(f"{symbol} {date}flying因子数据为空！")
                continue
            flying_factor_df = flying_factor_df.to_pandas()
            try:
                flying_factor_df = flying_factor_df.set_index("DateTime")
            except:
                print("flying_factor_df ERROR: ")
                print(flying_factor_df)

            merge_df = pd.merge(feature_label_df, flying_factor_df, left_index=True, right_index=True, how = "inner")

            new_feature_label_df = merge_df[factor_name_list + [label_name] + flying_factor]
            if new_feature_label_df.empty:
                print(f"{symbol} {date}因子标签数据为空！")
                continue
            T_test, X_test, Y_test = get_prepared(new_feature_label_df, label_name,
                                                  model_config["data_config"]["w_size"], parallel_mode=False)
            Y_test = Y_test.flatten()
            # print("T_test, X_test, Y_train: ", len(T_test), X_test.shape, Y_test.shape)
            # ########################预测信号###########################
            today = pd.DataFrame(X_test, columns=factor_name_list + flying_factor)
            factor_config = pd.read_json(
                os.path.join(exp_version_path, "saved_models/{}_factor_config.json".format(symbol)))
            for j in range(len(factor_name_list)):
                factor_mean = factor_config[factor_name_list[j]].loc['mean']
                factor_std = factor_config[factor_name_list[j]].loc['std']
                clip_lower = factor_mean - 3 * factor_std
                clip_upper = factor_mean + 3 * factor_std
                cliped_df = today[factor_name_list[j]].clip(
                    lower=clip_lower, upper=clip_upper)
                today[factor_name_list[j]] = (cliped_df.values - factor_mean) / factor_std
            X_test_norm = today.values
            print(symbol, date,  "feature_label_df: ", feature_label_df.shape, ", new_feature_label_df: ", new_feature_label_df.shape, "X_test_norm.shape:", X_test_norm.shape)


            # ########################生成信号数据###########################
            if factor_type != "real_factor":
                factor_df_online = fp.load_public_data_from_dfs(symbol=[symbol], factor_list=["LabelReferenceMidPx"],
                                                                start_time=date, end_time=date,
                                                                factor_type="label", data_type=data_type)
                factor_df_online = factor_df_online[factor_df_online["timestamp"].isin(T_test)]
                target_values = factor_df_online["LabelReferenceMidPx"].values
            else:
                factor_df_online = fp.load_public_data_from_dfs(symbol=[symbol], factor_list=["ReferenceMidPrice"],
                                                                start_time=date, end_time=date,
                                                                factor_type="real_factor", data_type=data_type)
                factor_df_online = factor_df_online[factor_df_online["timestamp"].isin(T_test)]
                target_values = factor_df_online["ReferenceMidPrice"].values
            if len(target_values) == 0:
                raise Exception(f"{symbol} {date}未加载到ReferenceMidPrice数据！")
            if model == None:
                model_path = os.path.join(exp_version_path, "saved_models/model.onnx")
                if os.path.exists(model_path):
                    model_file_type = "onnx"
                else:
                    model_path = os.path.join(exp_version_path, "saved_models/tmp_model.pickle.dat")
                    model_file_type = "pickle"
                model, Y_test_pred = model_save_and_evaluate.load_model_and_predict(model_path, model_file_type,
                                                                                X_test_norm=X_test_norm)
            else:
                model, Y_test_pred = model_save_and_evaluate.load_model_and_predict(model_path, model_file_type,
                                                                                    X_test_norm = X_test_norm, cache_model = model)

            signal_df = model_save_and_evaluate.generate_signal_without_class(symbol, T_test, Y_test_pred, Y_test,
                                                                              target_values,
                                                                              period=120, target_type="mid")
            signal_df["flying_flag"] = merge_df["open_flying"]#.astype(int)


            # 显示标签和预测值相关性
            res = pd.DataFrame(Y_test_pred, columns=["pred"])
            res["label"] = Y_test
            res = res[res["label"] > -100]
            print(date, res.corr())

            #########################生成parquet文件########################
            save_and_append_parquet(symbol, signal_df, save_parquet_path, overwrite_col = "DATE")
    except:
        import traceback
        print("main_generate_parquet error: {} {}".format(exp_version_path, symbol), traceback.print_exc())


def main_generate_parquet_l2p(label_name, symbol, exp_version_path, start_date, end_date, data_type,
                              model_config, factor_type = 'factor', model_file_type = "pickle"):
    # global model_config
    try:
        fp = FactorProvider("016869")
        fa = FactorData()
        model = None
        # data_type = "enhanced_tick_norm"
        start_date = pd.to_datetime(start_date).strftime("%Y%m%d")
        end_date = pd.to_datetime(end_date).strftime("%Y%m%d")
        start_date = fa.tradingday(start_date, -3)[0]
        dates = fa.tradingday(start_date, end_date)
        signal_path = os.path.join(exp_version_path, "signal_files")
        os.makedirs(signal_path, exist_ok=True)

        save_parquet_path = os.path.join(os.path.join(exp_version_path, f"signal_files/{label_name}-{symbol}.parquet"))
        if not os.path.exists(os.path.join(exp_version_path, "saved_models/{}_factor_config.json".format(symbol))):
            print(f"该模型{exp_version_path}无法预测该标的{symbol}！")
            return
        for date in dates:
            factor_name_list = model_config["factor_name_list"]
            flying_factor = []#model_config["data_config"]["flying_factor"]
            # ########################生成采样数据###########################
            feature_label_df = load_factor_label(
                fp,
                data_type,
                date,
                date,
                symbol,
                factor_name_list,
                [label_name],
                model_config["data_config"]["tagger_limit"],
                factor_type=factor_type,
                factor_only=True
            )
            new_feature_label_df = feature_label_df[factor_name_list + flying_factor + [label_name]]
            if new_feature_label_df.empty:
                print(f"{symbol} {date}因子标签数据为空！")
                continue
            T_test, X_test, Y_test = get_prepared(new_feature_label_df, label_name,
                                                  model_config["data_config"]["w_size"], parallel_mode=False)
            Y_test = Y_test.flatten()
            # ########################预测信号###########################
            today = pd.DataFrame(X_test, columns=factor_name_list + flying_factor)
            factor_config = pd.read_json(
                os.path.join(exp_version_path, "saved_models/{}_factor_config.json".format(symbol)))
            for j in range(len(factor_name_list)):
                factor_mean = factor_config[factor_name_list[j]].loc['mean']
                factor_std = factor_config[factor_name_list[j]].loc['std']
                clip_lower = factor_mean - 3 * factor_std
                clip_upper = factor_mean + 3 * factor_std
                cliped_df = today[factor_name_list[j]].clip(
                    lower=clip_lower, upper=clip_upper)
                today[factor_name_list[j]] = (cliped_df.values - factor_mean) / factor_std
            X_test_norm = today.values
            print(symbol, date, "feature_label_df: ", feature_label_df.shape, ", new_feature_label_df: ",
                  new_feature_label_df.shape, "X_test_norm.shape:", X_test_norm.shape)


            # ########################生成信号数据###########################
            if factor_type != "real_factor":
                factor_df_online = fp.load_public_data_from_dfs(symbol=[symbol], factor_list=["LabelReferenceMidPx"],
                                                                start_time=date, end_time=date,
                                                                factor_type="label", data_type=data_type)
                factor_df_online = factor_df_online[factor_df_online["timestamp"].isin(T_test)]
                target_values = factor_df_online["LabelReferenceMidPx"].values
            else:
                factor_df_online = fp.load_public_data_from_dfs(symbol=[symbol], factor_list=["ReferenceMidPrice"],
                                                                start_time=date, end_time=date,
                                                                factor_type="real_factor", data_type=data_type)
                factor_df_online = factor_df_online[factor_df_online["timestamp"].isin(T_test)]
                target_values = factor_df_online["ReferenceMidPrice"].values
            if len(target_values) == 0:
                raise Exception(f"{symbol} {date}未加载到ReferenceMidPrice数据！")
            if model == None:
                model_path = os.path.join(exp_version_path, "saved_models/model.onnx")
                if os.path.exists(model_path):
                    model_file_type = "onnx"
                else:
                    model_path = os.path.join(exp_version_path, "saved_models/tmp_model.pickle.dat")
                    model_file_type = "pickle"
                model, Y_test_pred = model_save_and_evaluate.load_model_and_predict(model_path, model_file_type,
                                                                                X_test_norm=X_test_norm)
            else:
                model, Y_test_pred = model_save_and_evaluate.load_model_and_predict(model_path, model_file_type,
                                                                                    X_test_norm = X_test_norm, cache_model = model)

            signal_df = model_save_and_evaluate.generate_signal_without_class(symbol, T_test, Y_test_pred, Y_test,
                                                                              target_values,
                                                                              period=120, target_type="mid")
            # 显示标签和预测值相关性
            res = pd.DataFrame(Y_test_pred, columns=["pred"])
            res["label"] = Y_test
            res = res[res["label"] > -100]
            print(date, res.corr())

            #########################生成parquet文件########################
            save_and_append_parquet(symbol, signal_df, save_parquet_path, overwrite_col = "DATE")
    except:
        import traceback
        print("main_generate_parquet error: {} {}".format(exp_version_path, symbol), traceback.print_exc())


def start_generate_signal(exp_list, symbol_list, start_date, end_date, model_config = model_config,
                               data_type="tick_l2p", model_file_type = "pkl", l3_flag = False,
                               factor_type = 'factor'):
    if not l3_flag:
        remote_func = ray.remote(main_generate_parquet_l2p)
        flying_factor = []
    else:
        remote_func = ray.remote(max_calls=5)(main_generate_parquet_l3)
        flying_factor = ["PriceSpread", "OneBigOrder", "CumOrdersNetVolOverV0", "BreakingP0NumOrders"]

    start_date = pd.to_datetime(start_date).strftime("%Y%m%d")
    end_date = pd.to_datetime(end_date).strftime("%Y%m%d")
    for label_name, exp_name, version_alias in exp_list:
        expa = exp_artifacts.ExpArtifacts(exp_name=exp_name)
        exp_version_path = expa.path_of_exp_version(version_alias=version_alias)
        target_type = parse_target_type(label_name)  # "longshort" #评价指标的类型，mid是中间价收益率，longshort是端到端涨跌收益率
        ######################(1)生成实验数据###########################
        params_jsonstr_path = os.path.join(exp_version_path, "params_jsonstr.json")
        if os.path.exists(params_jsonstr_path):
            model_config = json.load(open(params_jsonstr_path, "r"))
            select_factors = model_config["factor_name_list"]
            flying_factor = model_config["data_config"]["flying_factor"]
            model_config["data_config"]["flying_factor"] = flying_factor
            # pd.read_csv("kc50.csv", header=None)[0].tolist()
            SYMBOL_LIST = model_config["symbol_list"]
            print("SYMBOL_LIST:", len(SYMBOL_LIST))
            print("select_factors:", len(select_factors))
        else:
            print("WARNING: no params_jsonstr!")
            model_config["factor_name_list"] = \
                pd.read_csv(os.path.join(exp_version_path, "saved_models/factors.csv"), header=None)[0].tolist()
            model_config["data_config"]["flying_factor"] = flying_factor
            SYMBOL_LIST = []

        ############################(2)生成Parquet文件##############################
        tt1 = time.time()
        tasks = [
            remote_func.remote(label_name, symbol, exp_version_path, start_date, end_date, data_type, model_config,
                               factor_type=factor_type, model_file_type=model_file_type)
            for symbol in symbol_list]
        ray.get(tasks)
        print(f"{version_alias}-{start_date}-{end_date}-{len(symbol_list)}支标的 flag_generate_parquet 耗时:{time.time() - tt1} s")



@ray.remote(max_calls=10)
def inner_func(symbol_name, source_signal_df, long_pred_th, short_pred_th, start_date, end_date,
               target_type, win_limits, loss_limits, file_path):
    res_df = winloss_func(symbol_name, source_signal_df, long_pred_th, short_pred_th,
                          start_date=start_date, end_date=end_date, local_mode=True, t_sta="09:33:00",
                          target_type=target_type, win_limits=win_limits, loss_limits = loss_limits)
    res_df["日期"] = res_df.index.values
    agg_df, eval_dict = winloss_func_agg(res_df, verbose=1)
    if "标的" not in agg_df.columns:
        agg_df["标的"] = symbol_name
    return agg_df, res_df

@ray.remote(max_calls=10)
def inner_func0(model_name, symbol_name, pred00_df, percent, date_list,
               win_limit, loss_limit):
    df_calc_list = []
    for date in date_list:
        df_pred00_p = pred00_df.filter(pl.col("DATE") == date)
        if df_pred00_p.shape[0] == 0:
            continue
        df_pred00_p = df_pred00_p.with_columns((pl.col("PREDICT").abs()).alias("PREDICT_abs"))
        df_pred00_p = df_pred00_p.sort(by='PREDICT_abs')
        # 获取百分位数
        percent_1 = percent / 100
        th = round(df_pred00_p['PREDICT_abs'].quantile(1 - percent_1), 1)
        df_p = find_stop_new(df_pred00_p, float(win_limit), float(loss_limit), th,
                             model_name=model_name, symbol_name=symbol_name,
                             date=date)
        df_calc_list.append(df_p)
    if df_calc_list:
        df_calc = pd.concat(df_calc_list)
        return df_calc
    else:
        return pd.DataFrame()

def start_generate_percent_signal(exp_list, symbol_list, start_date, end_date, l3_flag=False):
    if not l3_flag:
        excel_path_list = ["signal_winloss"]
    else:
        excel_path_list = ["signal_winloss", "signal_sample_winloss"]

    start_date = pd.to_datetime(start_date).strftime("%Y%m%d")
    end_date = pd.to_datetime(end_date).strftime("%Y%m%d")
    for label_name, exp_name, version_alias in exp_list:
        expa = exp_artifacts.ExpArtifacts(exp_name=exp_name)
        exp_version_path = expa.path_of_exp_version(version_alias = version_alias)
        target_type = parse_target_type(label_name)  # "longshort" #评价指标的类型，mid是中间价收益率，longshort是端到端涨跌收益率

        sdate = pd.to_datetime(start_date).strftime("%Y-%m-%d")
        edate = pd.to_datetime(end_date).strftime("%Y-%m-%d")
        win_limits = [0.001, 0.0015]
        loss_limits = [0.002]
        try:
            t0 = time.time()
            tasks = []
            for symbol_name in symbol_list:
                for path in excel_path_list:
                    print("=====================" + symbol_name + "=====================")
                    try:
                        source_signal_df = expa.model_signal_load(version_alias, label_name, symbol_name)
                        source_signal_df = source_signal_df[
                            (source_signal_df["DATE"] >= sdate) & (source_signal_df["DATE"] <= edate)]
                        signal_dates = list(set(source_signal_df["DATE"].tolist()))
                    except Exception as e:
                        print("ERROR: model_signal_load failed! ", e)
                        continue
                    if source_signal_df.empty:
                        continue

                    if "sample" in path:
                        # 只统计采样点的准确率
                        source_signal_df["PREDICTED"] = source_signal_df["PREDICTED"] * source_signal_df["flying_flag"]
                        source_signal_df["PREDICT"] = source_signal_df["PREDICT"] * source_signal_df["flying_flag"]

                    # -----------------------------------------------------
                    pred00_path = os.path.join(exp_version_path, "signal_files_pred00")
                    os.makedirs(pred00_path, exist_ok=True)
                    for win_limit in win_limits[1:]:
                        for loss_limit in loss_limits:
                            pred00_file = f"{exp_name}_{symbol_name}" + "_" \
                                          + f"win{float(win_limit * 1000)}" \
                                          + "_" + f"loss{float(loss_limit * 1000)}" + "_pred00.parquet"
                            pred00_file_path = os.path.join(pred00_path, pred00_file)
                            _, no_cache_dates = get_cache_data_and_lack_param(file_path=pred00_file_path,
                                                                                      increase_col="DATE",
                                                                                      calc_params=signal_dates)
                            if no_cache_dates:
                                print(f"{version_alias}-{symbol_name}-{len(no_cache_dates)}天开始计算0阈值信号文件")
                                # 把未缓存00阈值数据的日期，计算并缓存
                                nocache_signal_df = source_signal_df[source_signal_df["DATE"].isin(no_cache_dates)]
                                no_cache_dates.sort()
                                remote_func = ray.remote(calc_save_winloss_func_pred00)
                                task = remote_func.remote(symbol_name, nocache_signal_df, pred00_file_path,
                                                            local_mode=True, target_type=target_type,
                                                            t_sta="09:33:00",
                                                            win_limits=[win_limit],
                                                            loss_limits=[loss_limit])
                                tasks.append(task)
                            # TODO 测试性能时用，有没有缓存都会重新计算，然后存储
                            # remote_func = ray.remote(calc_save_winloss_func_pred00)
                            # task = remote_func.remote(symbol_name, nocache_signal_df, pred00_file_path,
                            #                           local_mode=True, target_type=target_type,
                            #                           t_sta="09:33:00",
                            #                           win_limits=[win_limit],
                            #                           loss_limits=[loss_limit])
                            # tasks.append(task)
            ray.get(tasks)
            print(f"{version_alias} {len(symbol_list)}个标的，{start_date}-{end_date}计算0阈值信号文件耗时：{time.time()-t0} s")
        except Exception as e:
            import traceback
            print(traceback.print_exc())
            print(e)


def start_evaluate_signal(exp_list, symbol_list, start_date, end_date, model_config = model_config,
                          l3_flag = False, winloss_save_path=None):
    if not l3_flag:
        excel_path_list = ["signal_winloss"]
        flying_factor = []
    else:
        excel_path_list = ["signal_winloss", "signal_sample_winloss"]
        flying_factor = ["PriceSpread", "OneBigOrder", "CumOrdersNetVolOverV0", "BreakingP0NumOrders"]

    start_date = pd.to_datetime(start_date).strftime("%Y%m%d")
    end_date = pd.to_datetime(end_date).strftime("%Y%m%d")
    for label_name, exp_name, version_alias in exp_list:
        tt0 = time.time()
        expa = exp_artifacts.ExpArtifacts(exp_name=exp_name)
        exp_version_path = expa.path_of_exp_version(version_alias = version_alias)
        target_type = parse_target_type(label_name)  # "longshort" #评价指标的类型，mid是中间价收益率，longshort是端到端涨跌收益率
        ######################(1)生成实验数据###########################
        params_jsonstr_path = os.path.join(exp_version_path, "params_jsonstr.json")
        if os.path.exists(params_jsonstr_path):
            model_config = json.load(open(params_jsonstr_path, "r"))
            select_factors = model_config["factor_name_list"]
            flying_factor = model_config["data_config"]["flying_factor"]
            model_config["data_config"]["flying_factor"] = flying_factor
            # pd.read_csv("kc50.csv", header=None)[0].tolist()
            SYMBOL_LIST = model_config["symbol_list"]
            print("SYMBOL_LIST:", len(SYMBOL_LIST))
            print("select_factors:", len(select_factors))
        else:
            print("WARNING: no params_jsonstr!")
            model_config["factor_name_list"] = \
                pd.read_csv(os.path.join(exp_version_path, "saved_models/factors.csv"), header=None)[0].tolist()
            model_config["data_config"]["flying_factor"] = flying_factor
            SYMBOL_LIST = []
        ############################(3)计算止盈止损率指标##############################
        if target_type == "mid":
            if "log" in version_alias:
                th_list = [0.9, 1.0, 1.1, 1.2, 1.4, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4]
            else:
                th_list = [1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0]
        else:
            th_list = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4]
        sdate = pd.to_datetime(start_date).strftime("%Y-%m-%d")
        edate = pd.to_datetime(end_date).strftime("%Y-%m-%d")
        win_limits = [0.001, 0.0015]
        loss_limits = [0.002]
        percent_list = [1, 2]
        if winloss_save_path == None:
            winloss_save_path_v = os.path.dirname(exp_version_path)
        else:
            winloss_save_path_v = winloss_save_path
        t0 = time.time()
        # TODO 计算阈值百分比的止盈止损
        try:
            tasks = collections.defaultdict(list)
            for symbol_name in symbol_list:
                for path in excel_path_list:
                    pred00_path = os.path.join(exp_version_path, "signal_files_pred00")
                    for win_limit in win_limits[1:]:
                        for loss_limit in loss_limits:
                            pred00_file = f"{exp_name}_{symbol_name}" + "_" \
                                          + f"win{float(win_limit * 1000)}" \
                                          + "_" + f"loss{float(loss_limit * 1000)}" + "_pred00.parquet"
                            pred00_file_path = os.path.join(pred00_path, pred00_file)
                            if os.path.exists(pred00_file_path):
                                df_pred00 = pd.read_parquet(pred00_file_path)
                                df_pred00 = df_pred00[(df_pred00["DATE"]>=sdate) & (df_pred00["DATE"]<=edate)]
                                if df_pred00.empty:
                                    print(f"{pred00_file_path}在{sdate}-{edate}无数据。")
                                    continue
                                calc_dates = sorted(list(set(df_pred00["DATE"].tolist())))
                                df_pred00_pl = pl.from_pandas(df_pred00)
                                for percent in percent_list:
                                    percent_winloss_file = f"{target_type}_{path}_win{float(win_limit * 1000)}_loss{float(loss_limit * 1000)}_pred_percent{int(percent)}.parquet"
                                    if winloss_save_path == None:
                                        percent_winloss_file_path = os.path.join(exp_version_path, percent_winloss_file)
                                    else:
                                        os.makedirs(os.path.join(winloss_save_path, version_alias), exist_ok=True)
                                        percent_winloss_file_path = os.path.join(winloss_save_path, version_alias,
                                                                                 percent_winloss_file)
                                    task = inner_func0.remote(version_alias, symbol_name, df_pred00_pl, percent,
                                                              calc_dates, win_limit, loss_limit)
                                    tasks[percent_winloss_file_path].append(task)
                            else:
                                print(f"Warning: {pred00_file_path}不存在。")
                                continue
            print(f"{version_alias}-{start_date}-{end_date}-{len(symbol_list)}支标的，阈值百分比：{percent_list} 止盈止损【计算】耗时：{time.time() - t0} s")
            t1 = time.time()
            for task_id in tasks.keys():
                if not tasks[task_id]:
                    continue
                results = ray.get(tasks[task_id])
                results_df = pd.concat(results)
                file_name = task_id.split("/")[-1]
                res_out_path = os.path.join(winloss_save_path_v, version_alias, file_name)
                save_winloss_data(results_df, save_parquet_path=res_out_path, sub_cols=["日期", "标的"])
            print(f"{version_alias}-{start_date}-{end_date}-{len(symbol_list)}支标的，阈值百分比：{percent_list} 止盈止损【存储】耗时：{time.time() - t1} s")
        except Exception as e:
            import traceback
            print(traceback.print_exc())
            print(e)
            pass
        print(f"{version_alias}-{start_date}-{end_date}-{len(symbol_list)}支标的，阈值百分比：{percent_list} 止盈止损【计算并存储】耗时：{time.time() - t0} s")
        t2 = time.time()
        # TODO 计算固定阈值的止盈止损
        for th in th_list:
            tt2 = time.time()
            try:
                tasks_dict = collections.defaultdict(list)
                for symbol_name in symbol_list:
                    for path in excel_path_list:
                        print(f"=====================symbol_name:{symbol_name},th:{th}=====================")
                        try:
                            source_signal_df = expa.model_signal_load(version_alias, label_name, symbol_name)
                            sdate = pd.to_datetime(start_date).strftime("%Y-%m-%d")
                            edate = pd.to_datetime(end_date).strftime("%Y-%m-%d")
                            source_signal_df = source_signal_df[
                                (source_signal_df["DATE"] >= sdate) & (source_signal_df["DATE"] <= edate)]
                        except Exception as e:
                            print("ERROR: model_signal_load failed! ", e)
                            continue
                        if source_signal_df.empty:
                            continue
                        if "sample" in path:
                            # 只统计采样点的准确率
                            source_signal_df["PREDICTED"] = source_signal_df["PREDICTED"] * source_signal_df[
                                "flying_flag"]
                            source_signal_df["PREDICT"] = source_signal_df["PREDICT"] * source_signal_df[
                                "flying_flag"]
                        for win_limit in win_limits[1:]:
                            for loss_limit in loss_limits:
                                long_pred_th = th
                                short_pred_th = -th
                                file_name = f"{target_type}_{path}_win{win_limit * 1000}_loss{loss_limit * 1000}_pred{th}.parquet"
                                if winloss_save_path == None:
                                    excel_path = os.path.join(exp_version_path, file_name)
                                else:
                                    os.makedirs(os.path.join(winloss_save_path, version_alias), exist_ok=True)
                                    excel_path = os.path.join(winloss_save_path, version_alias, file_name)
                                print(
                                    "=====================" + symbol_name + ":" + f"[{long_pred_th}, {short_pred_th}]" + "=====================")
                                # long short标签数量多，评价很慢
                                if target_type == "longshort":
                                    if "SHORT" in label_name.upper():
                                        long_pred_th = 20 * long_pred_th
                                    if "LONG" in label_name.upper():
                                        short_pred_th = 20 * short_pred_th
                                task = inner_func.remote(symbol_name, source_signal_df, long_pred_th,
                                                         short_pred_th, start_date, end_date,
                                                         target_type=target_type, win_limits=[win_limit],
                                                         loss_limits=[loss_limit], file_path=excel_path)
                                tasks_dict[excel_path].append(task)
                print(f"{version_alias}-{start_date}-{end_date}-{len(symbol_list)}支标的，固定阈值：{th} 止盈止损【计算】耗时：{time.time() - tt2} s")
                tt3 = time.time()
                for task_id in tasks_dict.keys():
                    if not tasks_dict[task_id]:
                        continue
                    results = ray.get(tasks_dict[task_id])
                    agg_res_list = [res[0] for res in results]
                    res_list = [res[-1] for res in results]
                    result_agg_df = pd.concat(agg_res_list)
                    result_res_df = pd.concat(res_list)
                    file_name = task_id.split("/")[-1]
                    agg_file_name = "agg_" + file_name
                    agg_out_path = os.path.join(winloss_save_path_v, version_alias, agg_file_name)
                    res_out_path = os.path.join(winloss_save_path_v, version_alias, file_name)
                    save_winloss_data(result_agg_df, save_parquet_path=agg_out_path, sub_cols=["开始日期", "结束日期", "标的"])
                    save_winloss_data(result_res_df, save_parquet_path=res_out_path, sub_cols=["日期", "标的"])
                print(f"{version_alias}-{start_date}-{end_date}-{len(symbol_list)}支标的，固定阈值：{th} 止盈止损【存储】耗时：{time.time() - tt3} s")
            except Exception as e:
                import traceback
                print(traceback.print_exc())
                print(e)
                pass
            print(f"{version_alias}-{start_date}-{end_date}-{len(symbol_list)}支标的 固定阈值【计算并存储】耗时：{time.time() - tt2} s")
        print(f"{version_alias}-{start_date}-{end_date}-{len(symbol_list)}支标的 固定阈值计算止盈止损并存储，总耗时：{time.time() - t2} s")
        # # 把所有的mid_winloss_detail数据合并为一个parquet文件
        t3 = time.time()
        file_pattern = f"mid_signal_winloss_win(\d+(\.\d+)?)_loss(\d+(\.\d+)?)_pred(\d+(\.\d+)?)" + ".parquet"
        model_path = os.path.join(winloss_save_path_v, version_alias)
        cache_file_name = os.path.join(model_path, "winloss_detail_all_new.parquet")
        res_df_list = []
        for f in os.listdir(model_path):
            match = re.match(file_pattern, f)
            if match:
                winloss_file = os.path.join(model_path, f)
                win, loss, pred = float(match.group(1)), float(match.group(3)), float(match.group(5))
                df_p = pd.read_parquet(winloss_file)
                df_p["模型名称"] = version_alias
                df_p["预测阈值"] = pred
                df_p["止盈线"] = df_p["止盈线"] * 1000
                df_p["止损线"] = df_p["止损线"] * 1000
                df_p = df_p.reindex(columns=winloss_field_pattern)
                res_df_list.append(df_p)
        res_df = pd.concat(res_df_list) if len(res_df_list) else pd.DataFrame()
        if len(res_df) > 0:
            res_df.to_parquet(cache_file_name)
        print("汇总固定阈值止盈止损数据到parquet，耗时：{} s".format(time.time() - t3))

        print(f"{version_alias}-{start_date}-{end_date}-{len(symbol_list)}支标的止盈止损计算存储总耗时：{time.time()-tt0} s")




def calc_save_winloss_func_pred00(symbol_name, source_signal_df, file_path, use_self_prob=False,
                                  local_mode=True, target_type="mid", t_sta="09:33:00",
                                  win_limits=[0.0015, 0.002], loss_limits=[0.002]):
    res_dict = winloss_stop_table_daily(source_signal_df,
                                        long_pred_th=0,
                                        short_pred_th=0,
                                        target_type=target_type,
                                        win_limits=win_limits,
                                        loss_limits=loss_limits,
                                        t_sta=t_sta,
                                        use_self_prob=use_self_prob,
                                        local_mode=local_mode
                                        )
    # res_df = res_dict[(0.0015, 0.002)]
    res_df = res_dict[(win_limits[0], loss_limits[0])]
    save_and_append_parquet(symbol_name, res_df, file_path, overwrite_col="DATE")






