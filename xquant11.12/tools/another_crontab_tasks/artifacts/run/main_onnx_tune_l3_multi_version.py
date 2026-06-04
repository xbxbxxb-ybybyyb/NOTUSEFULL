import os
import gc
import datetime
import sys
import shutil
import pickle
from tqdm import tqdm
import polars as pl
from xgboost import XGBRegressor, XGBClassifier
import numpy as np
import pandas as pd
import copy
import time
import json
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from sklearn.metrics import mean_squared_error as mse
import ray
from artifacts import exp_artifacts, model_save_and_evaluate, parse_format, backtest_save_and_evaluate, model_plot
from artifacts.run.parallel_xbrain_backtest import parallel_run
from artifacts.flying_functions import *
from artifacts.utils import save_backtest_result

pd.set_option('display.max_colwidth', 200)
pd.set_option('display.max_rows', 200)

"""
20240408：训练数据去除上市前30天，挑选训练集去除刚上市
"""


class L2PXGBoostRegPack:
    def __init__(self, exp_name, model_config, version_alias):
        self.data_type = "tick_l2p"
        self.expa = exp_artifacts.ExpArtifacts(exp_name=exp_name, exp_base="/dfs/group/800657/exp_results/")
        self.exp_path = self.expa.exp_path
        self.expa.activate_version_to_save(model_config, version_alias=version_alias)
        self.version_alias = version_alias
        self.model_config = model_config
        self.factor_name_list = model_config["factor_name_list"]
        self.tagger_name_list = model_config["tagger_name_list"]
        self.symbol_list = model_config["symbol_list"]
        self.exp_version_path = self.expa.path_of_exp_version()
        self.fp = FactorProvider('016884')

    def prepare_data(self, data_params):
        select_factors = select_factors_multi(self.expa, self.model_config, self.fp)
        self.select_factors = select_factors
        self.model_config["factor_name_list"] = select_factors
        model_config = self.model_config
        exp_path = self.exp_path
        fp = self.fp
        use_pandas = False
        factor_descibe_dict = {}
        label_list = model_config["tagger_name_list"]
        for symbol in model_config["symbol_list"]:
            source_data_path = os.path.join(cached_norm_dataset, "{}_data.parquet".format(symbol))
            if not os.path.exists(source_data_path):
                factor_df_all = fp.load_public_data_from_dfs(symbol=[symbol], factor_list=select_factors,
                                                             start_time=model_config["train_start_time"],
                                                             end_time=model_config["test_end_time"],
                                                             factor_type='factor',
                                                             data_type=model_config["data_config"]["data_type"])
                factor_df_all = factor_df_all.set_index("timestamp")
                factor_df_all.reindex(columns=select_factors, copy=False)
                if not factor_df_all.empty:
                    #                 factor_descibe_dict[symbol] = factor_label_df.describe()
                    factor_config = {}
                    factor_df_all_train = factor_df_all[
                        (factor_df_all.index >= pd.to_datetime(model_config["train_start_time"])) &
                        (factor_df_all.index <= pd.to_datetime(model_config["train_end_time"]))]
                    for factor_name in select_factors:
                        mean = factor_df_all_train[factor_name].mean()
                        std = factor_df_all_train[factor_name].std()
                        factor_config[factor_name] = {"mean": mean, "std": std}
                    with open(os.path.join(os.path.dirname(source_data_path), "{}_factor_config.json".format(symbol)),
                              "w") as f:
                        json.dump(factor_config, f, indent=4)
                    norm_results = []
                    ########耗时2min左右#######
                    for f_name in tqdm(select_factors):
                        sub_result = clip_norm(factor_df_all[[f_name]].values, factor_config[f_name]["mean"],
                                               factor_config[f_name]["std"])
                        norm_results.append(sub_result)
                    normal_factor_arr = np.concatenate(norm_results, axis=1)
                    X_all = normal_factor_arr
                    T_all = factor_df_all.index.values
                    factor_norm_df_all = pl.from_numpy(X_all, schema=select_factors).with_columns(
                        pl.Series(T_all).alias("DateTime"))
                    factor_norm_df_all.write_parquet(source_data_path)

            if os.path.exists(source_data_path) and not use_pandas:
                #######################标签数据需要删掉重新计算##########################
                try:
                    shutil.rmtree(os.path.join(exp_path, "dataset/{}_flying_label.parquet".format(symbol)))
                except:
                    pass
                if not os.path.exists(os.path.join(exp_path, "dataset/{}_flying_factor.parquet".format(symbol))):
                    #######################合并数据##########################
                    print("source_data_path: ", source_data_path)
                    factor_norm_df_all = pl.read_parquet(source_data_path)
                    label_df_all = fp.load_public_data_from_dfs(symbol=[symbol], factor_list=label_list,
                                                                start_time=model_config["train_start_time"],
                                                                end_time=model_config["test_end_time"],
                                                                factor_type='label',
                                                                data_type=model_config["data_config"]["data_type"])
                    if label_df_all.empty:
                        continue
                    ############## 去除上市首月的数据, 避免极端行情的影响
                    label_df_all = label_df_all.iloc[14400 * 22:]
                    label_df_all = label_df_all[["timestamp"] + label_list]
                    label_df_all = label_df_all[label_df_all[label_list[0]]<=model_config["data_config"]["tagger_limit"]]
                    label_df_all = pl.from_pandas(label_df_all).rename({"timestamp": "DateTime"})
                    flying_factor = model_config["data_config"]["flying_factor"]
                    edf_resample_df_all = load_flying_factors(symbol, model_config=model_config, use_pandas=False,
                                                              flying_factors=flying_factor,
                                                              flying_base_dir=flying_base_dir)

                    factor_label_df_all = factor_norm_df_all.join(label_df_all, on="DateTime")
                    if not os.path.exists(exp_path + "/dataset/"):
                        os.makedirs(exp_path + "/dataset/")
                    open_flying_df = factor_label_df_all.join(edf_resample_df_all, on="DateTime").filter(
                        pl.col("open_flying") != 0)
                    factor_columns = [col for col in open_flying_df.columns if col not in label_list]
                    label_columns = ["DateTime"] + label_list
                    open_flying_df[factor_columns].write_parquet(
                        os.path.join(exp_path, "dataset/{}_flying_factor.parquet".format(symbol)))
                    open_flying_df[label_columns].write_parquet(
                        os.path.join(exp_path, "dataset/{}_flying_label.parquet".format(symbol)))
                else:
                    ############### 利用缓存好的因子数据，和标签数据合并成新标签
                    label_df_all = fp.load_public_data_from_dfs(symbol=[symbol], factor_list=label_list,
                                                                start_time=model_config["train_start_time"],
                                                                end_time=model_config["test_end_time"],
                                                                factor_type='label',
                                                                data_type=model_config["data_config"]["data_type"])
                    assert len(label_list)==1, "label_list==1"
                    if label_df_all.empty:
                        continue
                    label_df_all = label_df_all[label_df_all[label_list[0]]<=model_config["data_config"]["tagger_limit"]]
                    label_df_all = label_df_all[["timestamp"] + label_list]
                    label_df_all = pl.from_pandas(label_df_all).rename({"timestamp": "DateTime"})

                    open_flying_factor_df = pl.read_parquet(
                        os.path.join(exp_path, "dataset/{}_flying_factor.parquet".format(symbol)))
                    open_flying_df = open_flying_factor_df.join(label_df_all, on="DateTime")
                    label_columns = ["DateTime"] + label_list
                    open_flying_df[label_columns].write_parquet(
                        os.path.join(exp_path, "dataset/{}_flying_label.parquet".format(symbol)))
                    print(symbol, " : open_flying_df shape: ", open_flying_df.shape)
                    #########################################################

    def train_loop(self, model_params):
        exp_path = self.exp_path
        exp_version_path = self.exp_version_path
        symbol_list = model_config["symbol_list"]
        flying_factor = model_config["data_config"]["flying_factor"]
        select_factors = select_factors_multi(self.expa, self.model_config, self.fp)

        T_train_list, X_train_list, Y_train_list, T_valid_list = [], [], [], []
        X_valid_list, Y_valid_list, T_test_list, X_test_list, Y_test_list = [], [], [], [], []

        for symbol in symbol_list:
            if not os.path.exists(os.path.join(exp_path, "dataset/{}_flying_label.parquet".format(symbol))):
                print("无该标的因子数据：", symbol)
                continue
            print("train_loop: ", symbol)
            open_flying_factor_df = pl.read_parquet(
                os.path.join(exp_path, "dataset/{}_flying_factor.parquet".format(symbol)))
            open_flying_label_df = pl.read_parquet(
                os.path.join(exp_path, "dataset/{}_flying_label.parquet".format(symbol)))
            open_flying_df = open_flying_factor_df.join(open_flying_label_df, on="DateTime")
            ########################划分训练测试集################################
            T_train, X_train, F_train, Y_train = generate_split_dataset(model_config, open_flying_df, model_config["data_config"]["tagger_limit"], type="train")
            T_valid, X_valid, F_valid, Y_valid = generate_split_dataset(model_config, open_flying_df, model_config["data_config"]["tagger_limit"], type="valid")

            # 将收益率转换为对数收益
            if model_config["data_config"]["tagger_log"]:
                Y_train = np.emath.logn(2, np.abs(Y_train) + 1.2) * np.sign(Y_train)#将收益率转换到偏移对数区间，使得乘数收益值为1以下有效，且乘数收益[1.0, 1.1, 1.2]映射为对数收益[1.13,1.20,1.26]
                Y_valid = np.emath.logn(2, np.abs(Y_valid) + 1.2) * np.sign(Y_valid)

            X_train = X_train.astype(np.float32)
            X_valid = X_valid.astype(np.float32)

            print("mask shape:", symbol, T_train.shape, Y_train.flatten())
            T_train_list.append(T_train[-5000000:])
            X_train_list.append(X_train[-5000000:])
            Y_train_list.append(Y_train[-5000000:])
            T_valid_list.append(T_valid)
            X_valid_list.append(X_valid)
            Y_valid_list.append(Y_valid)
            del F_train
            del F_valid

        T_train_all = np.concatenate(T_train_list)
        X_train_all = np.concatenate(X_train_list)
        Y_train_all = np.concatenate(Y_train_list)
        T_valid_all = np.concatenate(T_valid_list)
        X_valid_all = np.concatenate(X_valid_list)
        Y_valid_all = np.concatenate(Y_valid_list)
        del T_train_list
        del X_train_list
        del Y_train_list
        del T_valid_list
        del X_valid_list
        del Y_valid_list
        del T_test_list
        del X_test_list
        del Y_test_list
        gc.collect()

        self.model_config["xgb_config"]["n_estimators"] = 2000
        self.model_config["xgb_config"]['tree_method'] = 'gpu_hist'
        xgb_regressor = XGBRegressor(**self.model_config["xgb_config"], n_jobs=30)
        print("X_train_all: ", X_train_all.shape, "Y_train_all:", Y_train_all.shape, "X_valid_all:", X_valid_all.shape,
              "Y_valid_all:", Y_valid_all.shape)
        xgb_regressor.fit(X_train_all, Y_train_all,
                          eval_set=[(X_train_all, Y_train_all), (X_valid_all, Y_valid_all)],
                          # xgb_model = xgb_regressor_semiconductor,
                          early_stopping_rounds=8,
                          verbose=True)

        ########################## 模型文件存储 #########################
        self.expa.model_file_save(model_obj=xgb_regressor, mode=["pkl"], overwrite=True)
        for symbol in model_config["symbol_list"]:
            if os.path.exists(os.path.join(cached_norm_dataset, "{}_factor_config.json".format(symbol))):
                shutil.copyfile(os.path.join(cached_norm_dataset, "{}_factor_config.json".format(symbol)),
                                os.path.join(self.exp_version_path, "saved_models/{}_factor_config.json".format(symbol)))
        try:
            exp_factor_path = os.path.join(exp_version_path, f"saved_models/factors.csv")
            if not os.path.exists(exp_factor_path):
                os.makedirs(os.path.join(exp_version_path, f"saved_models"), exist_ok=True)
                with open(exp_factor_path, "w") as f:
                    for factor in select_factors:
                        f.writelines(factor + ",\n")
                # shutil.copyfile("/dfs/group/800657/exp_results/exp_l3_kc50_60s/xgboost_base/saved_models/factors.csv", factor_path)
        except Exception as e:
            print("ERRRO:", e)
        ##################################################
        importance_ = xgb_regressor.feature_importances_
        factor_importance = pd.DataFrame({'factor': select_factors + flying_factor, 'importance': importance_})
        factor_importance = factor_importance.sort_values(by='importance', ascending=False)
        print("factor_importance:", factor_importance)
        self.xgb_regressor = xgb_regressor

    def predict_signal(self, xgb_regressor):
        # 加载模型
        exp_path = self.exp_path
        exp_version_path = self.exp_version_path
        model_config = self.model_config
        select_factors = select_factors_multi(self.expa, self.model_config, self.fp)
        self.model_config["factor_name_list"] = select_factors
        fp = self.fp
        expa = self.expa
        fp = FactorProvider('016884')
        os.makedirs(os.path.join(exp_version_path, "signal_files/"), exist_ok=True)
        for symbol in model_config["symbol_list"]:
            print("predict_signal:", symbol)
            if not os.path.exists(os.path.join(exp_path, "dataset/{}_flying_label.parquet".format(symbol))):
                print("无该标的标签数据：", symbol)
                continue
            #########################读取因子数据########################
            # 方式2：读取原始因子、事件、标签数据，做合并，并对因子数据做标准化
            from artifacts.flying_functions import merge_norm_flying_factor
            open_flying_df, open_flying_label_df, flying_flag_df = merge_norm_flying_factor(
                symbol, model_config["test_start_time"],
                model_config["test_end_time"],
                model_config["factor_name_list"],
                model_config["tagger_name_list"][0],
                model_config["data_config"]["flying_factor"],
                factor_config_path=os.path.join(exp_version_path,"saved_models/{}_factor_config.json".format(symbol)),
                tagger_limit=model_config["data_config"]["tagger_limit"],
                data_type="tick_l2p",
                flying_base_dir="/dfs/group/800657/library/l3_event/event_data")
            if open_flying_label_df.empty:
                print("ERRRO: merge_norm_flying_factor 无该标的数据: ", symbol)
                continue
            T_test, X_test, Y_test = open_flying_df.index.values, open_flying_df.values, open_flying_label_df.values
            if model_config["data_config"]["tagger_log"]:
                Y_test = np.emath.logn(2, np.abs(Y_test) + 1.2) * np.sign(Y_test)#将收益率转换到偏移对数区间，使得乘数收益值为1以下有效，且乘数收益[1.0, 1.1, 1.2]映射为对数收益[1.13,1.20,1.26]

            factor_df = fp.load_public_data_from_dfs(symbol=[symbol], factor_list=["ReferenceMidPrice"],
                                                     start_time= model_config["test_start_time"],
                                                     end_time=model_config["test_end_time"], factor_type='factor',
                                                     data_type=model_config["data_config"]["data_type"])
            factor_df = factor_df.set_index("timestamp")
            target_values = factor_df["ReferenceMidPrice"].loc[T_test].values
            # 预测信号
            Y_test_pred = xgb_regressor.predict(X_test)
            # Y_test_pred = (2*Y_test_pred+Y_test_pred_lgbm)/3
            print("test rmse", np.sqrt(mse(Y_test_pred, Y_test)))

            ###########################合成并存储标准信号数据############################
            save_parquet_path = os.path.join(
                os.path.join(exp_version_path, f"signal_files/{label_name}-{symbol}.parquet"))
            signal_df = model_save_and_evaluate.generate_signal_without_class(symbol, T_test, Y_test_pred, Y_test,
                                                                              target_values, period=120,
                                                                              target_type="mid")
            signal_df["flying_flag"] = flying_flag_df
            print("new_signal_df shape: ", signal_df.shape)
            signal_df.to_parquet(save_parquet_path)

            # ###########################生成信号txt数据###################################
            # stock, p1, p2 = symbol, 1.5, -1.5
            # signal_df_load = expa.model_signal_load(version_alias=version_alias, label_name=label_name, symbol=stock)
            # signal_dir = expa.path_of_signal_process_save(evaluate_type="long_short_pred_th_classify",
            #                                               version_alias=version_alias,
            #                                               label_name=label_name,
            #                                               symbol=symbol,
            #                                               pred_th_up=p1, pred_th_dw=p2)
            # print("signal_dir:", signal_dir)
            # model_save_and_evaluate.model_signal_process_long_short_pred_th_classify(signal_df_load, pred_th_up=p1,
            #                                                                          pred_th_dw=p2,
            #                                                                          symbol=stock,
            #                                                                          signal_process_base_dir=signal_dir)

    def analysis_ic(self):
        exp_path = self.exp_path
        for symbol_name in self.model_config["symbol_list"]:
            if not os.path.exists(os.path.join(exp_path, "dataset/{}_flying_label.parquet".format(symbol_name))):
                print("无该标的数据：", symbol_name)
                continue
            signal_df_load = self.expa.model_signal_load(version_alias=self.version_alias, symbol=symbol_name,
                                                         label_name=self.model_config["tagger_name_list"][0])
            print(symbol_name)
            print(signal_df_load[["PREDICTED", "LABEL_VALUE"]].corr())

    def analysis_signal_winloss(self, start_date="2023-12-06", end_date="2024-02-06"):
        exp_version_path = self.exp_version_path
        expa = self.expa
        from artifacts.parse_param import parse_target_type
        target_type = parse_target_type(label_name)

        for path in ["signal_sample.xlsx", "signal_all.xlsx"]:
            excel_path = os.path.join(exp_version_path, target_type + "_" + path)
            for symbol_name in self.model_config["symbol_list"]:
                try:
                    source_signal_df = expa.model_signal_load(version_alias, label_name, symbol_name)
                    if "signal_sample.xlsx" in path:
                        # 只统计采样点的准确率
                        source_signal_df["PREDICTED"] = source_signal_df["PREDICTED"] * source_signal_df[
                            "flying_flag"]
                        source_signal_df["PREDICT"] = source_signal_df["PREDICT"] * source_signal_df["flying_flag"]

                    def inner_func(symbol_name, source_signal_df, long_pred_th, short_pred_th, start_date, end_date, target_type,
                                   win_limits):
                        res_df = winloss_func(symbol_name, source_signal_df, long_pred_th, short_pred_th,
                                              start_date=start_date, end_date=end_date, local_mode=True,
                                              target_type=target_type, win_limits=win_limits)
                        save_backtest_result(res_df, symbol_name, output_path=excel_path)
                        agg_df, eval_dict = winloss_func_agg(res_df, verbose=1)
                        return agg_df

                    remote_func = ray.remote(inner_func)
                    tasks = []
                    if target_type == "mid":
                        th_list = [1.0, 1.1, 1.2, 1.4, 1.5, 1.6, 1.8, 2.0, 2.2]
                    else:
                        th_list = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4]
                    for th in th_list:
                        for win_limit in [0.001, 0.0015]:
                            long_pred_th = th
                            short_pred_th = -th
                            print(
                                "=====================" + symbol_name + ":" + f"[{long_pred_th}, {short_pred_th}]" + "=====================")
                            tasks.append(remote_func.remote(symbol_name, source_signal_df, long_pred_th,
                                                            short_pred_th, start_date, end_date,
                                                            target_type=target_type, win_limits=[win_limit]))
                    results = ray.get(tasks)
                    result_agg_df = pd.concat(results)
                    save_backtest_result(result_agg_df, symbol_name,
                                         output_path=excel_path.replace("signal_all", "signal_all_agg").replace("signal_sample", "signal_sample_agg"))
                except Exception as e:
                    print(e)
                    pass
        ray.shutdown()

    def dyanamic_evaluate(self):
        self.analysis_ic()
        self.analysis_signal_winloss(start_date=self.model_config["test_start_time"], end_date=self.model_config["test_end_time"])

    def xbrain_backtest(self):
        ray.init(num_cpus=30, ignore_reinit_error=True, local_mode=False,
                 _system_config={"object_spilling_config": json.dumps(
                     {"type": "filesystem", "params": {"directory_path": "/data/user/013150/tmp/"}, })})
        for th1 in [1.2, 1.4]:
            for probs_up in [0.64, 0.66]:
                # th1 = 1.2
                # probs_up = 0.62
                signal_process_dir = self.expa.path_of_signal_process_save(
                    label_name=self.model_config["tagger_name_list"][0],
                    symbol=self.model_config["symbol_list"][0],
                    label_th1=th1,
                    label_th2=2,
                    probs_up=probs_up,
                    probs_dw=probs_up)
                plot_save_dir = signal_process_dir.replace("signal_files_processed", "StrategySignalT0")
                print("signal_process_dir:", signal_process_dir)
                print("plot_save_dir: ", plot_save_dir)
                parallel_run(signal_process_dir, plot_save_dir, self.model_config["symbol_list"][0], th1=th1,
                             prob1=probs_up)


def main(exp_name, model_config, version_alias, train_mode=True):
    # assert model_config!=None, "model_config不可为None！"
    instance = L2PXGBoostRegPack(exp_name=exp_name,
                                 model_config=model_config,
                                 version_alias=version_alias
                                 )
    if train_mode == True:
        instance.prepare_data(data_params={})
        instance.train_loop(model_params={})
        instance.xgb_regressor = pd.read_pickle(
            os.path.join(instance.exp_version_path, "saved_models/tmp_model.pickle.dat"))
        instance.predict_signal(instance.xgb_regressor)
        instance.dyanamic_evaluate()
    else:
        # 只评价信号，不训练
        # instance.dyanamic_evaluate()
        instance.xbrain_backtest()


if __name__ == "__main__":
    #######################################################################
    model_config_source = {
        # 数据段配置
        "symbol_list": [],
        "train_start_time": "20210701",
        "train_end_time": "20230930",
        "valid_start_time": "20231001",
        "valid_end_time": "20231215",
        "test_start_time": "20231216",
        "test_end_time": "20240229",
        "factor_name_list": [],  # 按条数筛选后写入
        "tagger_name_list": [],

        "data_config": {
            "data_type": "tick_l2p",
            "w_size": 1,
            "n_job": 2,
            "transform": True,
            "clip_type": "3sigma",
            "scaler_type": "z-score",
            "quantile": [0.02, 0.98],
            "tagger_limit": 60,
            "tagger_log": False, # 是否对收益率取对数
            "tagger_trim": 0, # 是否截取低阈值标签，0表示不截取
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
            'learning_rate': 0.03,
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
    model_config_source["train_start_time"] = "20220110"
    model_config_source["train_end_time"] = "20240320"
    model_config_source["valid_start_time"] = "20240321"
    model_config_source["valid_end_time"] = "20240425"
    model_config_source["test_start_time"] = "20240426"
    model_config_source["test_end_time"] = "20240520"
    # model_config["train_start_time"] = "20240101"
    # model_config["train_end_time"] = "20240131"
    # model_config["valid_start_time"] = "20240201"
    # model_config["valid_end_time"] = "20240210"
    # model_config["test_start_time"] = "20240211"
    # model_config["test_end_time"] = "20240228"
    stock_set = "kc_amt_swing"
    if stock_set == "kc50":
        SYMBOL_LIST = pd.read_csv("kc50.csv", header=None)[0].tolist()
        cached_norm_dataset = "/dfs/group/800657/exp_results/kc_dataset"
        # select_factors = pd.read_csv(os.path.join(cached_norm_dataset, "factors.csv"), header=None)[0].tolist()
        select_factors = pd.read_csv(os.path.join(cached_norm_dataset, "factors88.csv"), header=None)[0].tolist()
        flying_factor = pd.read_csv("extra_factors.csv", header=None)[0].tolist()
        flying_factor = ["PriceSpread", "OneBigOrder", "CumOrdersNetVolOverV0", "BreakingP0NumOrders"]
        # flying_factor = ["FacPriceSpread", "FacOneBigOrder", "FacCumOrdersNetVolOverV0", "FacBreakingP0NumOrders"]
    elif stock_set == "kc_amt_swing":
        # a = stock_info[(stock_info["close_mean"] >= 35) & (stock_info["close_mean"] <= 150)]
        # select_info = a[
        #     (a["amt_mean_rank"] < 130) | (a["swing_mean_rank"] < 130) & (a["amt_mean_rank"] < 150)].reset_index(
        #     drop=True)
        SYMBOL_LIST = pd.read_csv("kc_amt_swing.csv", header=None)[0].tolist()
        cached_norm_dataset = "/dfs/group/800657/exp_results/zz500_dataset"
        select_factors = pd.read_csv(os.path.join(cached_norm_dataset, "factors_drop.csv"), header=None)[0].tolist()
        # select_factors = pd.read_csv(os.path.join(cached_norm_dataset, "factors88.csv"), header=None)[0].tolist()
        # flying_factor = pd.read_csv("extra_factors.csv", header=None)[0].tolist()
        flying_factor = ["PriceSpread", "OneBigOrder", "CumOrdersNetVolOverV0", "BreakingP0NumOrders"]
        # flying_factor = ["FacPriceSpread", "FacOneBigOrder", "FacCumOrdersNetVolOverV0", "FacBreakingP0NumOrders"]
    elif stock_set == "zz500":
        symbols = pd.read_csv("kc_amt_swing.csv", header=None)[0].tolist()
        symbols1 = pd.read_csv("zz500_select74.csv", header=None)[0].tolist()
        SYMBOL_LIST = list(sorted(set(symbols + symbols1)))
        cached_norm_dataset = "/dfs/group/800657/exp_results/zz500_dataset"
        select_factors = pd.read_csv(os.path.join(cached_norm_dataset, "factors_drop.csv"), header=None)[0].tolist()
        flying_factor = pd.read_csv("extra_factors.csv", header=None)[0].tolist()
        flying_factor = ["PriceSpread", "OneBigOrder", "CumOrdersNetVolOverV0", "BreakingP0NumOrders"]
        # flying_factor = ["FacPriceSpread", "FacOneBigOrder", "FacCumOrdersNetVolOverV0", "FacBreakingP0NumOrders"]
        # last_idx = SYMBOL_LIST.index("603589.SH")
        # SYMBOL_LIST = SYMBOL_LIST[last_idx:]
    else:
        raise Exception("stock set:", stock_set)
    if (len(flying_factor) > 60):
        flying_base_dir = "/dfs/group/800657/library/l3_event/merge_event_data"
    else:
        flying_base_dir = "/dfs/group/800657/library/l3_event/event_data"
    #######################################################################
    model_config_source["data_config"]["flying_factor"] = flying_factor
    model_config_source["symbol_list"] = SYMBOL_LIST
    model_config_source["tagger_name_list"] = []  # "LabelFirstPeak_th10_60s"
    model_config_source["factor_name_list"] = select_factors
    ###################################################
    # /data/user/013150/online_scripts/shen/DolphindbFactors/labels/InfoTech/Factors
    for label_name, exp_name, version_alias in [
        # ("LabelFirstPeak_th10_60s", "exp_l3_kc50_th10_60s", 'xgboost_base'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_kc50_th12_60s", 'xgboost_base'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_kc50_th12_60s_extra59", 'xgboost_base'),
        # ("LabelFirstPeak_th10_60s", "exp_l3_kc50_th10_60s_flying4", 'xgboost_base'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_kc50_th12_60s_flying4", 'xgboost_base'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_kc50_th12_60s_flying4Fac", 'xgboost_base'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_kc50_th12_60s_flying0", 'xgboost_base'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_kc50_th12_60s_flying0_TopSymbol", 'xgboost_base'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_kc50_th12_60s_flying4_88", 'xgboost_base'),
        ("LabelFirstPeak_th12_60s", "exp_l3_zz500_th12_60s_extra59", 'xgboost_base'),
        # ("LabelFirstPeakLongShort_th10_60s", "exp_l3_kc50_ls_th10_60s", 'xgboost_base'),
        # ("LabelFirstPeakLong_th10_60s", "exp_l3_kc50_ls_l_th10_60s", 'xgboost_base'),
        # ("LabelFirstPeakShort_th10_60s", "exp_l3_kc50_ls_s_th10_60s", 'xgboost_base'),
        # ("LabelFirstPeakSmooth_5_th10_60s", "exp_l3_kc50_smooth5_th10_60s", 'xgboost_base'),
        # ("LabelFirstPeakSmooth_2_th10_60s", "exp_l3_kc50_smooth2_th10_60s", 'xgboost_base'),
        # ( "LabelLongTwoMin", "exp_l3_kc50_ls_120s", 'xgboost_base'),
        # ("LabelLongOneMin", "exp_l3_kc50_ls_60s", 'xgboost_base'),
        # ("LabelShortOneMin", "exp_l3_kc50_ls_s_60s", 'xgboost_base'),
        # ("LabelShortTwoMin", "exp_l3_kc50_ls_s_120s", 'xgboost_base'),
        # ("LabelLongOneMin", "exp_l3_zz500_th12_60s_extra59", 'xgboost_base'),
        # ("LabelShortOneMin", "exp_l3_zz500_th12_60s_extra59", 'xgboost_base'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_zz500_flying4", 'LabelFirstPeak_th12_60s'),
        # ("LabelFirstPeak_th15_60s", "exp_l3_zz500_flying4", 'LabelFirstPeak_th15_60s'),
        # ("LabelFirstPeak_th20_60s", "exp_l3_zz500_flying4", 'LabelFirstPeak_th20_60s'),
        # ("LabelFirstPeak_th12_120s", "exp_l3_zz500_flying4", 'LabelFirstPeak_th12_120s'),# 运行报错
        # ("LabelFirstPeak_th15_120s", "exp_l3_zz500_flying4", 'LabelFirstPeak_th15_120s'),
        # ("LabelFirstPeak_th20_120s", "exp_l3_zz500_flying4", 'LabelFirstPeak_th20_120s'),
        # ("LabelLongOneMin", "exp_l3_zzkc_flying4", 'LabelLongOneMin'),
        # ("LabelShortOneMin", "exp_l3_zz500_flying4", 'LabelShortOneMin'),
        # ("LabelLongTwoMin", "exp_l3_zz500_flying4", 'LabelLongTwoMin'),
        # ("LabelShortTwoMin", "exp_l3_zz500_flying4", 'LabelShortTwoMin'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_kc_flying4", 'LabelFirstPeak_th12_60s_noflying')
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98')
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_amp')#事件用幅度代替0、1值
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4_train_without", 'LabelFirstPeak_th12_60s') #不用flying因子参与训练,必须新起一个实验名，不然共用dataset
        # ("LabelLongTwoMin", "exp_l3_zzkc_flying4", 'LabelLongTwoMin_factor98_amp'),# 以下8个实验均未采样，同时在main_onnx_tune_l3_multi_version_longshort中跑了8个采样的实验
        # ("LabelShortTwoMin", "exp_l3_zzkc_flying4", 'LabelShortTwoMin_factor98_amp'),
        # ("LabelLongOneMin", "exp_l3_zzkc_flying4", 'LabelLongOneMin_factor98_amp'),
        # ("LabelShortOneMin", "exp_l3_zzkc_flying4", 'LabelShortOneMin_factor98_amp'),
        # ("LabelLongTwoMin", "exp_l3_zzkc_flying4", 'LabelLongTwoMin_factor98'),
        # ("LabelShortTwoMin", "exp_l3_zzkc_flying4", 'LabelShortTwoMin_factor98'),
        # ("LabelLongOneMin", "exp_l3_zzkc_flying4", 'LabelLongOneMin_factor98'),
        # ("LabelShortOneMin", "exp_l3_zzkc_flying4", 'LabelShortOneMin_factor98'),
        ##################20240624##################
        # ("LabelFirstPeak_th12_60s", "exp_l3_kc_flying4", 'LabelFirstPeak_th12_60s_factor98_lowpca'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_kc_flying4", 'LabelFirstPeak_th12_60s_factor98_highpca'),
        ##################20240625##################
        # ("LabelFirstPeak_th05_120s", "exp_l3_kc_flying4", 'LabelFirstPeak_th05_120s_factor98_lowpca'),
        # ("LabelFirstPeak_th05_120s", "exp_l3_kc_flying4", 'LabelFirstPeak_th05_120s_factor98_highpca'),
        # ##################20240626##################
        # ("LabelFirstPeak_th10_60s", "exp_l3_kc_flying4", 'LabelFirstPeak_th10_60s_factor98_lowpca'),
        # ("LabelFirstPeak_th10_60s", "exp_l3_kc_flying4", 'LabelFirstPeak_th10_60s_factor98_highpca'),
        #################20240626##################
        # ("LabelFirstPeak_th12_60s", "exp_l3_kc_flying4", 'LabelFirstPeak_th12_60s_factor98_lowpca_log10'),#对数底为10，不行，只训练了26轮就收敛
        ##################20240627##################
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_log2'),  # 对数底为2
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_amp_log2'),  # 对数底为2
        # ("LabelFirstPeak_th12_60s", "exp_l3_kc_flying4", 'LabelFirstPeak_th12_60s_factor98_lowpca_log2'),  # 对数底为2
        # ("LabelFirstPeak_th12_60s", "exp_l3_kc_flying4", 'LabelFirstPeak_th12_60s_factor98_highpca_log2'),  # 对数底为2
        # ##################20240627##################
        # ("LabelLongTwoMin", "exp_l3_zzkc_flying4", 'LabelLongTwoMin_factor98_log2'),
        # ("LabelShortTwoMin", "exp_l3_zzkc_flying4", 'LabelShortTwoMin_factor98_log2'),
        # ("LabelLongOneMin", "exp_l3_zzkc_flying4", 'LabelLongOneMin_factor98_log2'),
        # ("LabelShortOneMin", "exp_l3_zzkc_flying4", 'LabelShortOneMin_factor98_log2'),
        ##################20240629##################
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_huber1'),  # huber损失函数,huber_slope需要xgboost1.6以上版本
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_huber2'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_huber3'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_huber4'), #各个效果差不多
        ##################20240630##################
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_huber0.5'),  # huber损失函数
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_log2_huber1'),
        ##################20240701##################
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_huber0.5'),  # huber损失函数,huber_slope需要xgboost1.6以上版本（升级后重新训练）
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_huber1'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_huber2'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_huber3'),
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_huber4'),
        ##################20240711##################
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'tmp_tmp'),
    ]:

        # 用幅度特征替代0、1特征
        model_config = copy.deepcopy(model_config_source)
        if version_alias == "LabelFirstPeak_th12_60s_factor98_amp":
            model_config = copy.deepcopy(model_config_source)
            flying_factor = ["FacPriceSpread", "FacOneBigOrder", "FacCumOrdersNetVolOverV0", "FacBreakingP0NumOrders"]
            model_config["data_config"]["flying_factor"] = flying_factor
        # 区分高收益率标的和低收益率标签分别训练
        if version_alias in ["LabelFirstPeak_th12_60s_factor98_lowpca", "LabelFirstPeak_th05_60s_factor98_lowpca", "LabelFirstPeak_th10_60s_factor98_lowpca", "LabelFirstPeak_th12_60s_factor98_lowpca_log2"]:
            model_config = copy.deepcopy(model_config_source)
            SYMBOL_LIST = ['688122.SH','603379.SH','600536.SH','688005.SH','688012.SH','002738.SZ','300558.SZ','688297.SH','600563.SH','603939.SH','600378.SH','688778.SH','688363.SH','688281.SH','688981.SH','688271.SH','600329.SH','688187.SH','300114.SZ','603444.SH','688008.SH','688235.SH','600566.SH','000423.SZ','688220.SH','002756.SZ','603160.SH','600298.SH','688002.SH','002281.SZ','002028.SZ','002223.SZ','002409.SZ','600038.SH','300037.SZ','603338.SH','300373.SZ','603882.SH','300073.SZ','688396.SH','603589.SH','002432.SZ','688568.SH','688375.SH','688777.SH','688029.SH','688520.SH','000988.SZ']
            model_config["symbol_list"] = SYMBOL_LIST
        if version_alias in ["LabelFirstPeak_th12_60s_factor98_highpca", "LabelFirstPeak_th05_60s_factor98_highpca", "LabelFirstPeak_th10_60s_factor98_highpca", "LabelFirstPeak_th12_60s_factor98_highpca_log2"]:
            model_config = copy.deepcopy(model_config_source)
            SYMBOL_LIST = ['688521.SH','300418.SZ','688017.SH','688361.SH','002865.SZ','300474.SZ','688348.SH','688082.SH','688390.SH','688200.SH','688041.SH','688276.SH','688385.SH','688063.SH','688037.SH','603786.SH','688099.SH','688153.SH','603688.SH','688047.SH','002850.SZ','603596.SH','688048.SH','688114.SH','688301.SH','300724.SZ','688318.SH','600129.SH','688120.SH','688234.SH','002192.SZ','300502.SZ','688072.SH','688180.SH','688032.SH','300394.SZ','688052.SH','688169.SH','688409.SH','002791.SZ','688331.SH','603606.SH','688598.SH','301236.SZ','688256.SH','688536.SH']
            model_config["symbol_list"] = SYMBOL_LIST

        # 将收益率标签转换为对数收益率
        if "log2" in version_alias:
            model_config = copy.deepcopy(model_config_source)
            model_config["data_config"]["tagger_log"] = True
            # model_config["data_config"]["tagger_trim"] = 0.7 #截取0.5以下的标签

        if "huber" in version_alias:
            model_config = copy.deepcopy(model_config_source)
            model_config["xgb_config"]["objective"] = 'reg:pseudohubererror'
            model_config['xgb_config']["huber_slope"] = float(version_alias[version_alias.find("huber")+5:])
            model_config['xgb_config']['eval_metric'] = 'mae'

        model_config["tagger_name_list"] = [label_name]  # "LabelFirstPeak_th10_60s"
        if ray.is_initialized():
            ray.shutdown()
        result_file = f"/dfs/group/800657/exp_results/{exp_name}/{exp_name}_{version_alias}_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
        sys.stdout = open(result_file, 'w')
        # sys.stderr = open(result_file, 'w')
        t1 = time.time()
        main(exp_name=exp_name, model_config=model_config, version_alias=version_alias, train_mode = True)
        print("本次试验耗时：", time.time() - t1)
        os.system(f"cp {result_file} /data/user/013150/plot_tmp")
        os.system(f"curl ftp://168.8.2.68/013150/ -T {result_file} -u 'ftphzh:ftphzh2602'")
