import os
from xgboost import XGBRegressor, XGBClassifier
import numpy as np
import pandas as pd
from ray import tune
import matplotlib.pyplot as plt
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from sklearn.metrics import mean_squared_error as mse
import ray
from artifacts import exp_artifacts, model_save_and_evaluate, parse_format, backtest_save_and_evaluate, model_plot
from artifacts.factor_save_and_evaluate import get_prepared
from artifacts.run.parallel_xbrain_backtest import parallel_run
import time
import json


class L2PXGBoostRegPack:
    def __init__(self, exp_name, model_config, version_alias):
        self.data_type = "tick_l2p"
        self.expa = exp_artifacts.ExpArtifacts(exp_name=exp_name)
        self.exp_path = self.expa.exp_path
        self.expa.activate_version_to_save(model_config, version_alias=version_alias)
        self.version_alias = version_alias
        self.model_config = model_config
        self.factor_name_list = model_config["factor_name_list"]
        self.tagger_name_list = model_config["tagger_name_list"]
        self.symbol_list = model_config["symbol_list"]
        self.symbol = self.symbol_list[0]

        self.expa.path_of_exp_version()
        self.fp = FactorProvider('016884')

    def __select_factor_by_analysis(self):
        res = self.fp.load_factor_analysis_res(data_type=self.data_type, stock=self.symbol,
                                               label_name=self.tagger_name_list[0])
        res = res[res["MDDate"] < self.model_config["valid_end_time"]]
        factor_res = res[res["valid_count"] > 10000].groupby("factor_name").mean()

        # 删选因子数据
        thres_1, thres_2 = self.model_config["data_config"]["thres"]
        factor_res_filter = factor_res[(factor_res["normal_ic"] >= thres_2 ) | (factor_res["normal_ic"] <= thres_1) ]
        factor_res_filter = factor_res_filter[~np.isnan(factor_res_filter["tratified_short_p_value_10"])]
        print("factor_res_filter shape: ", factor_res_filter.shape)
        select_factors = list(set(factor_res_filter.index.tolist()))
        print("select_factors", select_factors)
        return select_factors

    def __factor_process(self, factor_label_df, label_name):
        # 将DataFrame转换为numpy数组
        feature_label_df_train = factor_label_df[
            (factor_label_df.index >= pd.to_datetime(self.model_config["train_start_time"])) &
            (factor_label_df.index <= pd.to_datetime(self.model_config["train_end_time"]))]
        feature_label_df_valid = factor_label_df[
            (factor_label_df.index >= pd.to_datetime(self.model_config["valid_start_time"])) &
            (factor_label_df.index <= pd.to_datetime(self.model_config["valid_end_time"]))]
        feature_label_df_test = factor_label_df[
            (factor_label_df.index >= pd.to_datetime(self.model_config["test_start_time"])) &
            (factor_label_df.index <= pd.to_datetime(self.model_config["test_end_time"]))]

        T_train, X_train, Y_train = get_prepared(feature_label_df_train, label_name,
                                                 self.model_config["data_config"]["w_size"], parallel_mode=True)
        print("T_train, X_train, Y_train: ", len(T_train), X_train.shape, Y_train.shape)
        T_valid, X_valid, Y_valid = get_prepared(feature_label_df_valid, label_name,
                                                 self.model_config["data_config"]["w_size"], parallel_mode=True)
        print("T_valid, X_valid, Y_valid: ", len(T_valid), X_valid.shape, Y_valid.shape)
        T_test, X_test, Y_test = get_prepared(feature_label_df_test, label_name,
                                              self.model_config["data_config"]["w_size"],
                                              parallel_mode=True)
        print("T_test, X_test, Y_test: ", len(T_test), X_test.shape, Y_test.shape)

        X_train = X_train[:, 0]
        Y_train = Y_train[:, 0]
        X_valid = X_valid[:, 0]
        Y_valid = Y_valid[:, 0]
        X_test = X_test[:, 0]
        Y_test = Y_test[:, 0]

        # if not os.path.exists(self.exp_path + "/dataset/online/{}/".format(self.model_config["symbol_list"][0])):
        #     os.makedirs(self.exp_path + "/dataset/online/{}/".format(self.model_config["symbol_list"][0]))
        # pickle.dump((T_train, X_train, Y_train, T_valid, X_valid, Y_valid, T_test, X_test, Y_test),
        #             open(os.path.join(self.exp_path, "dataset/online/{}/data.pkl".format(self.model_config["symbol_list"][0])),
        #                  "wb"))
        return T_train, X_train, Y_train, T_valid, X_valid, Y_valid, T_test, X_test, Y_test

    def __load_factor_label(self, factor_list, label_list):
        # factor_list_all = list(self.fp.load_info_from_dfs('factor', 'public', self.data_type))
        start_date = self.model_config["train_start_time"]
        end_date = self.model_config["test_end_time"]
        stock = self.symbol

        if True:
            factor_df_all = self.fp.load_public_data_from_dfs(symbol=[stock], factor_list=factor_list[:],
                                                              start_time=start_date,
                                                              end_time=end_date, factor_type='factor',
                                                              data_type=self.data_type)
            factor_df_all = factor_df_all.set_index('timestamp')

            label_df_all = self.fp.load_public_data_from_dfs(symbol=[stock], factor_list=label_list,
                                                             start_time=start_date,
                                                             end_time=end_date, factor_type='label',
                                                             data_type=self.data_type)
            label_df_all = label_df_all.set_index('timestamp')
            for label_name in label_list:
                # 过滤极值
                label_df_all = label_df_all[
                    abs(label_df_all[label_name]) <= self.model_config["data_config"]["tagger_limit"]]
            source_factor_label_df = pd.merge(factor_df_all, label_df_all, left_index=True, right_index=True)
            print("source_factor_label_df shape: ", source_factor_label_df.shape)
            return source_factor_label_df
            # source_factor_label_df.to_parquet(os.path.join(self.exp_path, "dataset/factor_label_df.parquet"))
        else:
            source_factor_label_df = pd.read_parquet(os.path.join(exp_path, "dataset/factor_label_df.parquet"))
            print("source_factor_label_df shape: ", source_factor_label_df.shape)
            return source_factor_label_df

    def prepare_data(self, data_params):
        select_factors = self.__select_factor_by_analysis()
        if "ReferenceMidPrice" not in select_factors:
            select_factors = select_factors+["ReferenceMidPrice"]
        self.model_config["factor_name_list"] = select_factors
        source_factor_label_df = self.__load_factor_label(select_factors, self.model_config["tagger_name_list"])
        factor_label_df = source_factor_label_df.loc[:, select_factors + self.model_config["tagger_name_list"]]

        label_name = self.tagger_name_list[0]
        T_train, X_train, Y_train, T_valid, X_valid, Y_valid, T_test, X_test, Y_test = self.__factor_process(
            factor_label_df, label_name)

        self.select_factors = select_factors
        self.factor_label_df = factor_label_df
        self.T_train, self.X_train, self.Y_train, self.T_valid, self.X_valid, self.Y_valid, self.T_test, self.X_test, self.Y_test = T_train, X_train, Y_train, T_valid, X_valid, Y_valid, T_test, X_test, Y_test


    def train_loop(self, model_params):
        self.model_config["xgb_config"]["tree_method"] = "gpu_hist"
        xgb_regressor = XGBRegressor(**self.model_config["xgb_config"])
        xgb_regressor.fit(self.X_train, self.Y_train,
                          eval_set=[(self.X_train, self.Y_train), (self.X_valid, self.Y_valid)],  # xgb_model = xgb_regressor_semiconductor,
                          early_stopping_rounds=10,
                          verbose=True)

        # 模型文件存储
        self.expa.model_file_save(model_obj=xgb_regressor, mode="pkl", overwrite=True)
        self.expa.model_file_save(model_obj=xgb_regressor, mode="onnx", overwrite=True)

        importance_ = xgb_regressor.feature_importances_
        factor_importance = pd.DataFrame({'factor': self.select_factors, 'importance': importance_})
        factor_importance.sort_values(by='importance', ascending=False)
        print("factor_importance:", factor_importance)
        self.xgb_regressor = xgb_regressor


    def predict_signal(self):
        # 加载模型
        # xgb_regressor = self.expa.model_file_load(version_alias="xgboost_base", mode="pkl")
        Y_test_pred = self.xgb_regressor.predict(self.X_test)
        # Y_test_pred_lgbm  = lgbm_regressor.predict(X_test)
        # Y_test_pred = (2*Y_test_pred+Y_test_pred_lgbm)/3
        Y_valid_pred = self.xgb_regressor.predict(self.X_valid)

        print("valid rmse", np.sqrt(mse(Y_valid_pred, self.Y_valid)))
        print("test rmse", np.sqrt(mse(Y_test_pred, self.Y_test)))

        # 合成并存储标准信号数据
        target_values = self.factor_label_df["ReferenceMidPrice"].loc[self.T_test].values
        signal_df = self.expa.model_signal_save(label_name=self.model_config["tagger_name_list"][0],
                                           symbol=self.symbol,
                                           tm_values=self.T_test, yhat_values=Y_test_pred, y_values=self.Y_test,
                                           target_values=target_values, period=120, target_type="mid")
        print("signal_df shape: ", signal_df.shape)
        self.signal_df = signal_df

    def dyanamic_evaluate(self):
        # 加载信号数据
        # signal_df_load = self.expa.model_signal_load(version_alias=self.version_alias, symbol=self.model_config["symbol_list"][0],
        #                                         label_name=self.model_config["tagger_name_list"][0])
        for th1 in [1.0, 1.2, 1.4]:
            for probs_up in [0.62, 0.64, 0.66]:
                # (1) 生成信号评价指标
                df_th1, df_th2 = self.expa.model_signal_evalatioin_single_label_th_classify(
                    label_name=self.model_config["tagger_name_list"][0],
                    symbol=self.model_config["symbol_list"][0],
                    label_th=th1, pred_th_abs_limits=[1, 6.0])
                res_detail = df_th1[df_th1["pred_pth_label_th_num"] >= 80].groupby(["pred_th"])[
                    ["pred_pth_label_th_num", "pred_acc", "recall"]].agg(["mean", "count"])
                print("res_detail:", res_detail)

                # (2)存储信号分类文件
                result = self.expa.model_signal_process_single_label_th_classify(
                    label_name=self.model_config["tagger_name_list"][0],
                    symbol=self.model_config["symbol_list"][0], label_th1=th1,
                    probs_up=probs_up, probs_dw=probs_up, njobs=30)
                assert result == True, "信号分类文件存储失败！"
                signal_process_dir = self.expa.path_of_signal_process_save(
                    label_name=self.model_config["tagger_name_list"][0],
                    symbol=self.model_config["symbol_list"][0],
                    label_th1=th1,
                    label_th2=2,
                    probs_up=probs_up,
                    probs_dw=probs_up)
                # (3)绘制信号可视化图
                stats_df, pnl_stats_df = model_save_and_evaluate.evaluate_singal_backtest_eval_stats(signal_process_dir)
                print("signal_process_path_dir:", signal_process_dir)

                # 推荐生成的路径跟阈值目录同级
                save_file_name = os.path.join(signal_process_dir, "../..", 'local_th{}_probs{}.png'.format(th1, probs_up))
                print("plot save_file_name:", save_file_name)
                model_plot.plot_signal_backtest_results(stats_df, pnl_stats_df, save_file_name)

    def xbrain_backtest(self):
        ray.init(num_cpus=30, ignore_reinit_error=True, local_mode=False,
                 _system_config={"object_spilling_config": json.dumps(
                     {"type": "filesystem", "params": {"directory_path": "/data/user/013150/tmp/"}, })})
        th1 = 1.2
        probs_up = 0.62
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
        parallel_run(signal_process_dir, plot_save_dir, self.symbol, th1=th1, prob1=probs_up)



def main(exp_name="688396.SH_trade_v0", model_config = None, train_mode = True):
    assert model_config!=None, "model_config不可为None！"

    instance = L2PXGBoostRegPack(exp_name=exp_name,
                                            model_config = model_config,
                                            version_alias="xgboost_base"
                                            )
    if train_mode == True:
        instance.prepare_data(data_params={})
        instance.train_loop(model_params={})
        instance.predict_signal()
        instance.dyanamic_evaluate()
    else:
        # 只评价信号，不训练
        instance.dyanamic_evaluate()
        # instance.xbrain_backtest()


if __name__ == "__main__":
    config = {
        # 数据段配置
        "symbol_list": [],
        "train_start_time": "20210101",
        "train_end_time": "20221201",
        "valid_start_time": "20221202",
        "valid_end_time": "20230321",
        "test_start_time": "20230322",
        "test_end_time": "20231031",
        "factor_name_list": [],  # 按条数筛选后写入
        "tagger_name_list": ["LabelFirstPeak_th10_120s"],

        "data_config": {
            "w_size": 1,
            "n_job": 2,
            "transform": True,
            "clip_type": "3sigma",
            "scaler_type": "z-score",
            "quantile": [0.02, 0.98],
            "tagger_limit": 60,
            "raw_name_list": [],
            "thres": [-0.02, 0.02],
            "other_factor_list": "",
            # 因子列表， 为空的话为全量
            "factor_json_path": ""
        },
        # 模型段配置
        "xgb_config": {
            'objective': 'reg:squarederror',
            'booster': 'gbtree',
            'tree_method': 'gpu_hist',
            'gamma': 0.5,
            'learning_rate': 0.005,
            'lambda': 2,
            'subsample': 0.7,
            'colsample_bytree': 0.7,
            'max_depth': 14,
            'n_estimators': 3000,
            'seed': 4,
            "n_jobs": 32,
        },
        "metrics": {"reg_eval_abs_limits": [1.0, 3.0],
                    "reg_eval_th": 0.5},
        "model": {"name": "mlp"},
        "optimizer": {"name": "adam", "lr": 0.001, },
        "criterion": {"name": "mse"},
        "Model_save_mode": ["pkl", "onnx"],
    }

    # "688008.SH",
    # "688036.SH",
    # "688599.SH",
    # "688981.SH",
    # "688256.SH",
    # "688777.SH",

    params_list = [
        ("688012.SH", "exp_l2p_688012.SH", {
            "train_start_time": "20210101",
            "train_end_time": "20221231",
            "valid_start_time": "20230101",
            "valid_end_time": "20230531",
            "test_start_time": "20230601",
            "test_end_time": "20230914", }),
        ("688111.SH", "exp_l2p_688111.SH", {
            "train_start_time": "20210102",
            "train_end_time": "20221231",
            "valid_start_time": "20230101",
            "valid_end_time": "20230331",
            "test_start_time": "20230401",
            "test_end_time": "20230904", }),
        ("603019.SH", "exp_l2p_603019.SH", {
            "train_start_time": "20210102",
            "train_end_time": "20220731",
            "valid_start_time": "20220801",
            "valid_end_time": "20230113",
            "test_start_time": "20230114",
            "test_end_time": "20230930", }),
        ("000858.SZ", "exp_l2p_000858.SZ", {
            "train_start_time": "20210102",
            "train_end_time": "20221125",
            "valid_start_time": "20221126",
            "valid_end_time": "20230512",
            "test_start_time": "20230513",
            "test_end_time": "20230930", }),
        ("002594.SZ", "exp_l2p_002594.SZ", {
            "train_start_time": "20210102",
            "train_end_time": "20220930",
            "valid_start_time": "20221008",
            "valid_end_time": "20230430",
            "test_start_time": "20230501",
            "test_end_time": "20230930", }),
        ("000977.SZ", "exp_l2p_000977.SZ", {
            "train_start_time": "20210102",
            "train_end_time": "20230131",
            "valid_start_time": "20230223",
            "valid_end_time": "20230516",
            "test_start_time": "20230517",
            "test_end_time": "20230914",
        }),
        ("002230.SZ", "exp_l2p_002230.SZ", {
            "train_start_time": "20210102",
            "train_end_time": "20230113",
            "valid_start_time": "20230217",
            "valid_end_time": "20230531",
            "test_start_time": "20230601",
            "test_end_time": "20230913", }),
    ]

    for symbol, exp_name, dataset_config in params_list:
        # if symbol != "000977.SZ":
        #     continue
        if ray.is_initialized():
            ray.shutdown()

        ray.init(num_cpus=30, object_store_memory=25000000000, local_mode=False, num_gpus=1)
        t1 = time.time()
        print(symbol, exp_name, dataset_config)
        config["symbol_list"] = [symbol]
        config["train_start_time"] =  dataset_config["train_start_time"]
        config["train_end_time"] = dataset_config["train_end_time"]
        config["valid_start_time"] = dataset_config["valid_start_time"]
        config["valid_end_time"] = dataset_config["valid_end_time"]
        config["test_start_time"] = dataset_config["test_start_time"]
        config["test_end_time"] = dataset_config["test_end_time"]

        main(exp_name=exp_name, model_config=config, train_mode = False)
        print("本次试验耗时：", time.time() - t1)
        try:
            ray.shutdown()
        except:
            pass