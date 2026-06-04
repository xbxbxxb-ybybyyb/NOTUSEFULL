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
import time
import json
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from sklearn.metrics import mean_squared_error as mse
import ray
from artifacts import exp_artifacts, model_save_and_evaluate, parse_format, backtest_save_and_evaluate, model_plot
from artifacts.run.parallel_xbrain_backtest import parallel_run
from artifacts.flying_functions import *


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
        fp =self.fp
        use_pandas = False
        factor_descibe_dict = {}
        label_list = model_config["tagger_name_list"]
        for symbol in model_config["symbol_list"]:
            source_data_path = os.path.join(cached_norm_dataset, "{}_data.parquet".format(symbol))
            if not os.path.exists(source_data_path):
                factor_df_all = fp.load_public_data_from_dfs(symbol=[symbol], factor_list=select_factors,
                                                             start_time=model_config["train_start_time"],
                                                             end_time=model_config["test_end_time"], factor_type='factor',
                                                             data_type=model_config["data_config"]["data_type"])
                factor_df_all = factor_df_all.set_index("timestamp")
                factor_df_all.reindex(columns = select_factors, copy = False)
                if not factor_df_all.empty:
        #                 factor_descibe_dict[symbol] = factor_label_df.describe()
                    factor_config = {}
                    factor_df_all_train = factor_df_all[
                        (factor_df_all.index >= pd.to_datetime(model_config["train_start_time"])) &
                        (factor_df_all.index <= pd.to_datetime(model_config["train_end_time"]))]
                    for factor_name in select_factors:
                        mean = factor_df_all_train[factor_name].mean()
                        std = factor_df_all_train[factor_name].std()
                        factor_config[factor_name] = {"mean":mean, "std":std}
                    with open(os.path.join(os.path.dirname(source_data_path), "{}_factor_config.json".format(symbol)), "w") as f:
                        json.dump(factor_config, f, indent=4)
                    norm_results = []
                    ########耗时2min左右#######
                    for f_name in tqdm(select_factors):
                        sub_result = clip_norm(factor_df_all[[f_name]].values, factor_config[f_name]["mean"], factor_config[f_name]["std"])
                        norm_results.append(sub_result)
                    normal_factor_arr = np.concatenate(norm_results, axis=1)
                    X_all = normal_factor_arr
                    T_all = factor_df_all.index.values
                    factor_norm_df_all = pl.from_numpy(X_all,schema = select_factors).with_columns(pl.Series(T_all).alias("DateTime"))
                    factor_norm_df_all.write_parquet(source_data_path)
            if os.path.exists(os.path.join(os.path.dirname(source_data_path), "{}_factor_config.json".format(symbol))):
                shutil.copyfile(os.path.join(os.path.dirname(source_data_path), "{}_factor_config.json".format(symbol)),
                            os.path.join(self.exp_version_path,
                                         "saved_models/{}_factor_config.json".format(symbol)))


            if os.path.exists(source_data_path) and not use_pandas:
                if not os.path.exists(os.path.join(exp_path, "dataset/{}_flying_data.parquet".format(symbol))):
                    #######################合并数据##########################
                    factor_norm_df_all = pl.read_parquet(source_data_path)
                    label_df_all = fp.load_public_data_from_dfs(symbol=[symbol], factor_list=label_list,
                                                                     start_time=model_config["train_start_time"],
                                                                     end_time=model_config["test_end_time"], factor_type='label',
                                                                     data_type=model_config["data_config"]["data_type"])
                    if label_df_all.empty:
                        continue
                    ############## 去除上市首月的数据, 避免极端行情的影响
                    label_df_all = label_df_all.iloc[14400*22:]
                    label_df_all = label_df_all[["timestamp"]+label_list]
                    label_df_all = pl.from_pandas(label_df_all).rename({"timestamp":"DateTime"})
                    flying_factor = model_config["data_config"]["flying_factor"]
                    edf_resample_df_all = load_flying_factors(symbol, model_config = model_config, use_pandas = False, flying_factors = flying_factor, flying_base_dir = flying_base_dir)

                    factor_label_df_all = factor_norm_df_all.join(label_df_all, on = "DateTime")
                    # 筛选事件数据
                    open_flying_df = factor_label_df_all.join(edf_resample_df_all, on = "DateTime").filter(pl.col("open_flying")!=0)
                    if not os.path.exists(exp_path + "/dataset/"):
                        os.makedirs(exp_path + "/dataset/")
                    open_flying_df.write_parquet(os.path.join(exp_path, "dataset/{}_flying_data.parquet".format(symbol)))
                    print(symbol, " : factor_label_df_all shape: ",factor_label_df_all.shape, ", open_flying_df shape: ", open_flying_df.shape)
                    #########################################################

    def train_loop(self, model_params):
        exp_path = self.exp_path
        symbol_list = model_config["symbol_list"]
        flying_factor = model_config["data_config"]["flying_factor"]
        select_factors = select_factors_multi(self.expa, self.model_config, self.fp)
        self.model_config["factor_name_list"] = select_factors

        T_train_list,X_train_list,Y_train_list,T_valid_list = [], [], [], []
        X_valid_list,Y_valid_list,T_test_list,X_test_list,Y_test_list = [], [], [], [], []

        for symbol in symbol_list:
            if not os.path.exists(os.path.join(exp_path, "dataset/{}_flying_data.parquet".format(symbol))):
                print("无该标的数据：", symbol)
                continue
            open_flying_df = pl.read_parquet(os.path.join(exp_path, "dataset/{}_flying_data.parquet".format(symbol)))
            ########################划分训练测试集################################
            T_train, X_train, F_train, Y_train = generate_split_dataset(model_config, open_flying_df, type = "train")
            T_valid, X_valid, F_valid, Y_valid = generate_split_dataset(model_config, open_flying_df, type = "valid")

            X_train = X_train.astype(np.float32)
            X_valid = X_valid.astype(np.float32)

            print("mask shape:", symbol, T_train.shape, Y_train.flatten())
            T_train_list.append(T_train[-1600000:])
            X_train_list.append(X_train[-1600000:])
            Y_train_list.append(Y_train[-1600000:])
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
        self.model_config["xgb_config"]['tree_method'] = 'hist'
        xgb_regressor = XGBRegressor(**self.model_config["xgb_config"], n_jobs=30)
        print("X_train_all: ", X_train_all.shape, "Y_train_all:",Y_train_all.shape, "X_valid_all:", X_valid_all.shape, "Y_valid_all:", Y_valid_all.shape)
        xgb_regressor.fit(X_train_all, Y_train_all,
              eval_set = [(X_train_all, Y_train_all),(X_valid_all, Y_valid_all)], #xgb_model = xgb_regressor_semiconductor,
              early_stopping_rounds = 8,
              verbose = True)

        # 模型文件存储
        self.expa.model_file_save(model_obj=xgb_regressor, mode=["pkl"], overwrite=True)
        importance_ = xgb_regressor.feature_importances_
        factor_importance = pd.DataFrame({'factor': select_factors+flying_factor, 'importance': importance_})
        factor_importance = factor_importance.sort_values(by='importance', ascending=False)
        print("factor_importance:", factor_importance)
        self.xgb_regressor = xgb_regressor

    def predict_signal(self, xgb_regressor):
        # 加载模型
        exp_path = self.exp_path
        model_config = self.model_config
        select_factors = select_factors_multi(self.expa, self.model_config, self.fp)
        self.model_config["factor_name_list"] = select_factors
        fp = self.fp
        expa = self.expa
        fp = FactorProvider('016884')

        for symbol in model_config["symbol_list"]:
            if not os.path.exists(os.path.join(exp_path, "dataset/{}_flying_data.parquet".format(symbol))):
                print("无该标的数据：", symbol)
                continue
            open_flying_df = pl.read_parquet(os.path.join(exp_path, "dataset/{}_flying_data.parquet".format(symbol)))
            T_test, X_test, F_test, Y_test = generate_split_dataset(model_config, open_flying_df, type = "test")
            print(X_test.shape, Y_test.shape)
            factor_df = fp.load_public_data_from_dfs(symbol=[symbol], factor_list=["ReferenceMidPrice"],
                                                          start_time=model_config["test_start_time"],
                                                          end_time=model_config["test_end_time"], factor_type='factor',
                                                          data_type=model_config["data_config"]["data_type"])
            factor_df = factor_df.set_index("timestamp")
            target_values = factor_df["ReferenceMidPrice"].loc[T_test].values
            # 预测信号
            Y_test_pred = xgb_regressor.predict(X_test)
            # Y_test_pred = (2*Y_test_pred+Y_test_pred_lgbm)/3
            print("test rmse", np.sqrt(mse(Y_test_pred, Y_test)))

            ###########################合成并存储标准信号数据############################
            signal_df = expa.model_signal_save(label_name=model_config["tagger_name_list"][0],
                                               symbol=symbol,
                                               tm_values=list(T_test), yhat_values=Y_test_pred, y_values=Y_test,
                                               target_values=target_values, period=120, target_type="mid")
            expa.model_signal_process_long_short_pred_th_classify(model_config["tagger_name_list"][0], symbol, pred_th_up = 1.5, pred_th_dw = -1.5)
            print("signal_df shape: ", signal_df.shape)

            ###########################生成信号txt数据###################################
            stock, p1, p2 = symbol, 1.5, -1.5
            signal_df_load = expa.model_signal_load(version_alias=version_alias, label_name=label_name, symbol=stock)
            signal_dir = expa.path_of_signal_process_save(evaluate_type="long_short_pred_th_classify",
                                                          version_alias=version_alias,
                                                          label_name=label_name,
                                                          symbol=symbol,
                                                          pred_th_up=p1, pred_th_dw=p2)
            print("signal_dir:", signal_dir)
            model_save_and_evaluate.model_signal_process_long_short_pred_th_classify(signal_df_load, pred_th_up=p1,
                                                                                     pred_th_dw=p2,
                                                                                     symbol=stock,
                                                                                     signal_process_base_dir=signal_dir)

    def analysis_ic(self):
        exp_path = self.exp_path
        for symbol_name in self.model_config["symbol_list"]:
            if not os.path.exists(os.path.join(exp_path, "dataset/{}_flying_data.parquet".format(symbol_name))):
                print("无该标的数据：", symbol_name)
                continue
            signal_df_load = self.expa.model_signal_load(version_alias=self.version_alias, symbol=symbol_name,
                                                    label_name=self.model_config["tagger_name_list"][0])
            print(symbol_name)
            print(signal_df_load[["PREDICTED", "LABEL_VALUE"]].corr())

    def analysis_signal_winloss(self, start_date="2023-12-06", end_date="2024-02-06"):
        exp_path = self.exp_path
        for symbol_name in self.model_config["symbol_list"]:
            if not os.path.exists(os.path.join(exp_path, "dataset/{}_flying_data.parquet".format(symbol_name))):
                print("无该标的数据：", symbol_name)
                continue
            long_pred_th = 1.5
            short_pred_th = -1.5
            print(
                "=====================" + symbol_name + ":" + f"[{long_pred_th}, {short_pred_th}]" + "=====================")
            label_name = self.model_config["tagger_name_list"][0]
            source_signal_df = self.expa.model_signal_load(version_alias, label_name, symbol_name)
            res_df = winloss_func(symbol_name, source_signal_df.copy(), long_pred_th, short_pred_th,
                                  start_date=start_date, end_date=end_date)
            print(res_df)
        #     res_dict[(0.0015, 0.002)].to_csv(os.path.join(exp_version_path,
        #                                "pred_th_win_loss_{}_{}_{}.csv".format(1,5, model_config["test_start_time"], model_config["test_end_time"])))
        #     display(res_dict[(0.0015, 0.002)][res_dict[(0.0015, 0.002)].index<"2024-02-06"].mean())

    def dyanamic_evaluate(self):
        self.analysis_ic()
        # self.analysis_signal_winloss(start_date=self.model_config["test_start_time"], end_date=self.model_config["test_end_time"])

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
                parallel_run(signal_process_dir, plot_save_dir, self.model_config["symbol_list"][0], th1=th1, prob1=probs_up)



def main(exp_name, model_config, version_alias , train_mode = True):
    # assert model_config!=None, "model_config不可为None！"
    instance = L2PXGBoostRegPack(exp_name=exp_name,
                                            model_config = model_config,
                                            version_alias=version_alias
                                            )
    if train_mode == True:
        instance.prepare_data(data_params={})
        instance.train_loop(model_params={})
        instance.xgb_regressor = pd.read_pickle(os.path.join(instance.exp_version_path, "saved_models/tmp_model.pickle.dat"))
        instance.predict_signal(instance.xgb_regressor)
        instance.dyanamic_evaluate()
    else:
        # 只评价信号，不训练
        # instance.dyanamic_evaluate()
        instance.xbrain_backtest()


if __name__ == "__main__":
    #######################################################################
    model_config = {
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
    model_config["train_start_time"] = "20220101"
    model_config["train_end_time"] = "20240131"
    model_config["valid_start_time"] = "20240201"
    model_config["valid_end_time"] = "20240320"
    model_config["test_start_time"] = "20240321"
    model_config["test_end_time"] = "20240430"
    # model_config["train_start_time"] = "20240101"
    # model_config["train_end_time"] = "20240131"
    # model_config["valid_start_time"] = "20240201"
    # model_config["valid_end_time"] = "20240210"
    # model_config["test_start_time"] = "20240211"
    # model_config["test_end_time"] = "20240228"
    stock_set = "zz500"
    if stock_set == "kc50":
        SYMBOL_LIST = pd.read_csv("kc50.csv", header=None)[0].tolist()
        cached_norm_dataset = "/dfs/group/800657/exp_results/kc_dataset"
        # select_factors = pd.read_csv(os.path.join(cached_norm_dataset, "factors.csv"), header=None)[0].tolist()
        select_factors = pd.read_csv(os.path.join(cached_norm_dataset, "factors88.csv"), header=None)[0].tolist()
        overwrite_factors = True
        flying_factor = pd.read_csv("extra_factors.csv", header=None)[0].tolist()
        flying_factor = ["PriceSpread", "OneBigOrder", "CumOrdersNetVolOverV0", "BreakingP0NumOrders"]
        # flying_factor = ["FacPriceSpread", "FacOneBigOrder", "FacCumOrdersNetVolOverV0", "FacBreakingP0NumOrders"]
    elif stock_set == "zz500":
        SYMBOL_LIST = pd.read_csv("zz500_select74.csv", header=None)[0].tolist()
        cached_norm_dataset = "/dfs/group/800657/exp_results/zz500_dataset"
        select_factors = pd.read_csv(os.path.join(cached_norm_dataset, "factors.csv"), header=None)[0].tolist()
        flying_factor = pd.read_csv("extra_factors.csv", header=None)[0].tolist()
        overwrite_factors = True
        flying_factor = ["PriceSpread", "OneBigOrder", "CumOrdersNetVolOverV0", "BreakingP0NumOrders"]
        # flying_factor = ["FacPriceSpread", "FacOneBigOrder", "FacCumOrdersNetVolOverV0", "FacBreakingP0NumOrders"]
    else:
        raise Exception("stock set:", stock_set)
    if(len(flying_factor)>60):
        flying_base_dir = "/dfs/group/800657/library/l3_event/merge_event_data"
    else:
        flying_base_dir = "/dfs/group/800657/library/l3_event/event_data"
    #######################################################################
    model_config["data_config"]["flying_factor"] = flying_factor
    model_config["symbol_list"] = SYMBOL_LIST
    model_config["tagger_name_list"] = [] #"LabelFirstPeak_th10_60s"
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
        # ("LabelFirstPeak_th12_60s", "exp_l3_zz500_th12_60s_extra59", 'xgboost_base'),
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
        ("LabelFirstPeak_th12_60s", "exp_l3_zz500_flying4", 'LabelFirstPeak_th12_60s'),
        ("LabelFirstPeak_th15_60s", "exp_l3_zz500_flying4", 'LabelFirstPeak_th15_60s'),
        ("LabelFirstPeak_th20_60s", "exp_l3_zz500_flying4", 'LabelFirstPeak_th20_60s'),
        ("LabelFirstPeak_th12_120s", "exp_l3_zz500_flying4", 'LabelFirstPeak_th12_120s'),
        ("LabelFirstPeak_th15_120s", "exp_l3_zz500_flying4", 'LabelFirstPeak_th15_120s'),
        ("LabelFirstPeak_th20_120s", "exp_l3_zz500_flying4", 'LabelFirstPeak_th20_120s')
    ]:
        model_config["tagger_name_list"] = [label_name] #"LabelFirstPeak_th10_60s"
        if ray.is_initialized():
            ray.shutdown()
        try:
            base_dir = f"/dfs/group/800657/exp_results/{exp_name}/{version_alias}"
            exp_factor_path = f"{base_dir}/saved_models/factors.csv"
            if overwrite_factors or not os.path.exists(exp_factor_path):
                os.makedirs(f"/dfs/group/800657/exp_results/{exp_name}/{version_alias}/saved_models", exist_ok=True)
                if select_factors:
                    with open(exp_factor_path, "w") as f:
                        for factor in select_factors:
                            f.writelines(factor+",\n")
                # shutil.copyfile("/dfs/group/800657/exp_results/exp_l3_kc50_60s/xgboost_base/saved_models/factors.csv", factor_path)
        except Exception as e:
            print("ERRRO:", e)
        result_file = f"/dfs/group/800657/exp_results/{exp_name}/{exp_name}_{version_alias}_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
        sys.stdout = open(result_file, 'w')
        # sys.stderr = open(result_file, 'w')
        t1 = time.time()
        main(exp_name=exp_name, model_config = model_config, version_alias = version_alias, train_mode = True)
        print("本次试验耗时：", time.time() - t1)
        os.system(f"cp {result_file} /data/user/013150/plot_tmp")
        os.system(f"curl ftp://168.8.2.68/013150/ -T {result_file} -u 'ftphzh:ftphzh2602'")

