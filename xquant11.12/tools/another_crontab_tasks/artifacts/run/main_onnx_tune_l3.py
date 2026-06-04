import os
from xgboost import XGBRegressor, XGBClassifier
import numpy as np
import pandas as pd
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from sklearn.metrics import mean_squared_error as mse
import ray
from artifacts import exp_artifacts, model_save_and_evaluate, parse_format, backtest_save_and_evaluate, model_plot
from artifacts.factor_save_and_evaluate import get_prepared
from artifacts.run.parallel_xbrain_backtest import parallel_run
import time
import json
import pickle
import copy


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
        self.symbol = self.symbol_list[0]

        self.expa.path_of_exp_version()
        self.fp = FactorProvider('016884')

    def __select_factor_by_analysis(self, data_type, symbol, start_date, end_date, tagger_name_list, thres_limit):
        res_list = []
        for year in range(int(start_date[:4]), int(end_date[:4]) + 1):
            year_start = max("{}0101".format(year), start_date)
            year_end = min("{}1231".format(year), end_date)
            print(year_start, year_end)
            res = self.fp.load_factor_analysis_res(data_type=data_type, stock=symbol, start_date=year_start,
                                              end_date=year_end,
                                              label_name=tagger_name_list[0])
            res_list.append(res)
        res = pd.concat(res_list, axis=0)
        print("factor analysis dateframe shape: ", res.shape)

        valid_count = res["valid_count"].quantile(0.1)
        factor_res = res[res["valid_count"] >= valid_count].groupby("factor_name").mean()

        # 删选因子数据
        thres_1, thres_2 = thres_limit
        factor_res_filter = factor_res[(factor_res["normal_ic"] >= thres_2) | (factor_res["normal_ic"] <= thres_1)]
        factor_res_filter = factor_res_filter[~np.isnan(factor_res_filter["tratified_short_p_value_10"])]
        print("factor_res_filter shape: ", factor_res_filter.shape)
        select_factors = list(set(factor_res_filter.index.tolist()))
        fac = self.fp.load_info_from_dfs(factor_type="factor", source_type="public", data_type="tick_l2p")
        select_factors = set(select_factors) & set(fac)
        select_factors = list(select_factors)
        print("select_factors", select_factors)
        return select_factors


    def __factor_process(self, factor_label_df, label_name, w_size):
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
                                                 w_size, parallel_mode=True)
        print("T_train, X_train, Y_train: ", len(T_train), X_train.shape, Y_train.shape)
        T_valid, X_valid, Y_valid = get_prepared(feature_label_df_valid, label_name,
                                                 w_size, parallel_mode=True)
        print("T_valid, X_valid, Y_valid: ", len(T_valid), X_valid.shape, Y_valid.shape)
        T_test, X_test, Y_test = get_prepared(feature_label_df_test, label_name,
                                              w_size,
                                              parallel_mode=True)
        print("T_test, X_test, Y_test: ", len(T_test), X_test.shape, Y_test.shape)

        X_train = X_train[:, 0]
        Y_train = Y_train[:, 0]
        X_valid = X_valid[:, 0]
        Y_valid = Y_valid[:, 0]
        X_test = X_test[:, 0]
        Y_test = Y_test[:, 0]
        return T_train, X_train, Y_train, T_valid, X_valid, Y_valid, T_test, X_test, Y_test

    def __factor_process_filter_by_flying(self, factor_label_df, flying_factor_df, label_name, w_size,
                                          object_spill_path="/dfs/user/013150/tmp/"):
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

        ###################################################
        flying_factor = ["PriceSpread", "OneBigOrder", "CumOrdersNetVolOverV0", "BreakingP0NumOrders",
                         "ActivePriceVolume"]
        target_columns = factor_label_df.columns.to_list() + flying_factor
        merge_df = pd.merge(feature_label_df_train, flying_factor_df, left_index=True, right_index=True, how="left")
        merge_df = merge_df[merge_df["open_flying"] != 0]
        new_feature_label_df_train = merge_df.reindex(columns=target_columns)
        print("feature_label_df_train: ", feature_label_df_train.shape, ", new_feature_label_df_train: ",
              new_feature_label_df_train.shape)

        T_train, X_train, Y_train = get_prepared(new_feature_label_df_train, label_name,
                                                 w_size, parallel_mode=True, object_spill_path=object_spill_path)
        print("T_train, X_train, Y_train: ", len(T_train), X_train.shape, Y_train.shape)

        ###################################################
        merge_df = pd.merge(feature_label_df_valid, flying_factor_df, left_index=True, right_index=True, how="left")
        merge_df = merge_df[merge_df["open_flying"] != 0]
        new_feature_label_df_valid = merge_df.reindex(columns=target_columns)
        print("feature_label_df_valid: ", feature_label_df_valid.shape, ", new_feature_label_df_valid: ",
              new_feature_label_df_valid.shape)

        T_valid, X_valid, Y_valid = get_prepared(new_feature_label_df_valid, label_name,
                                                 w_size, parallel_mode=True, object_spill_path=object_spill_path)
        print("T_valid, X_valid, Y_valid: ", len(T_valid), X_valid.shape, Y_valid.shape)
        ###################################################
        merge_df = pd.merge(feature_label_df_test, flying_factor_df, left_index=True, right_index=True, how="left")
        merge_df = merge_df[merge_df["open_flying"] != 0]
        new_feature_label_df_test = merge_df.reindex(columns=target_columns)
        print("feature_label_df_test: ", feature_label_df_test.shape, ", new_feature_label_df_test: ",
              new_feature_label_df_test.shape)
        T_test, X_test, Y_test = get_prepared(new_feature_label_df_test, label_name,
                                              w_size,
                                              parallel_mode=True, object_spill_path=object_spill_path)
        print("T_test, X_test, Y_test: ", len(T_test), X_test.shape, Y_test.shape)

        X_train = X_train[:, 0]
        Y_train = Y_train[:, 0]
        X_valid = X_valid[:, 0]
        Y_valid = Y_valid[:, 0]
        X_test = X_test[:, 0]
        Y_test = Y_test[:, 0]

        return T_train, X_train, Y_train, T_valid, X_valid, Y_valid, T_test, X_test, Y_test

    def __load_factor_label(self, data_type, start_date, end_date, stock, factor_list, label_list, tagger_limit):
        # factor_list_all = list(self.fp.load_info_from_dfs('factor', 'public', self.data_type))
        if True:
            factor_df_all = self.fp.load_public_data_from_dfs(symbol=[stock], factor_list=factor_list[:],
                                                              start_time=start_date,
                                                              end_time=end_date, factor_type='factor',
                                                              data_type=data_type)
            factor_df_all = factor_df_all.set_index('timestamp')

            label_df_all = self.fp.load_public_data_from_dfs(symbol=[stock], factor_list=label_list,
                                                             start_time=start_date,
                                                             end_time=end_date, factor_type='label',
                                                             data_type=data_type)
            label_df_all = label_df_all.set_index('timestamp')
            for label_name in self.tagger_name_list:
                # 过滤极值
                label_df_all = label_df_all[
                    abs(label_df_all[label_name]) <= tagger_limit]
            print("factor_df_all shape:", factor_df_all.shape, "label_df_all shape:", label_df_all.shape)
            source_factor_label_df = pd.merge(factor_df_all, label_df_all, left_index=True, right_index=True)
            print("source_factor_label_df shape: ", source_factor_label_df.shape)
            return source_factor_label_df
            # source_factor_label_df.to_parquet(os.path.join(self.exp_path, "dataset/factor_label_df.parquet"))
        else:
            source_factor_label_df = pd.read_parquet(os.path.join(exp_path, "dataset/factor_label_df.parquet"))
            print("source_factor_label_df shape: ", source_factor_label_df.shape)
            return source_factor_label_df


    def __load_flying_factors(self):
        def resample_flying_factors(edf):
            how_method_dict = {
                'ActivePriceVolume': "sum",
                'BreakingP0NumOrders': 'sum',
                'OneBigOrder': 'sum',
                'CumOrdersNetVolOverV0': 'sum',
                'PriceSpread': 'sum',
                'LevelOneChange': 'sum',
                "Timestamp": "last",
                "MDDate": "last",
                "MDTime": "last"
            }
            how_method_dict = {k: v for k, v in how_method_dict.items() if k in edf.columns}

            edf_resample = edf.resample(rule='1s', closed='left', label='right').agg(how_method_dict)
            # print("edf_resample:", edf_resample.groupby("MDDate")["ActivePriceVolume"].count().iloc[0])

            edf_resample["open_flying"] = (edf_resample["PriceSpread"] != 0) | \
                                          (edf_resample["BreakingP0NumOrders"] != 0) | \
                                          (edf_resample["OneBigOrder"] != 0) | \
                                          (edf_resample["CumOrdersNetVolOverV0"] != 0
                                           #                                            (edf_resample["ActivePriceVolume"]!=0)
                                           )

            edf_resample["close_flying"] = (edf_resample["LevelOneChange"] != 0)
            return edf_resample

        self.flying_factor = ["PriceSpread", "OneBigOrder", "CumOrdersNetVolOverV0", "BreakingP0NumOrders",
                         "ActivePriceVolume"]

        from xquant.factordata import FactorData
        from tqdm import tqdm
        import polars as pl
        fa = FactorData()
        start_date = self.model_config["train_start_time"]
        end_date = self.model_config["test_end_time"]
        dates = fa.tradingday(start_date, end_date)

        use_pandas = True
        flying_base_dir = "/dfs/group/800657/library/l3_event/event_data"

        ###########################################
        data_list = []
        if use_pandas:
            for date in dates:
                sub_edf = pd.read_parquet(os.path.join(flying_base_dir, "{}/{}-{}.pqt".format(symbol, symbol, date)))
                sub_edf = sub_edf.set_index('DateTime')
                try:
                    if not sub_edf.empty:
                        sub_edf_resample = resample_flying_factors(sub_edf)
                        data_list.append(sub_edf_resample)
                except:
                    print("sub_edf_resample error: ",symbol ," ", date)
            edf_resample = pd.concat(data_list)
            print("edf_resample:", edf_resample.shape)
            # 用polars读取速度快10倍
            # edf_resample.to_parquet(os.path.join(flying_base_dir, "{}.pqt".format(symbol)))
        else:
            for date in tqdm(dates):
                sub_edf = pl.read_parquet(os.path.join(flying_base_dir, "{}/{}-{}.pqt".format(symbol, symbol, date)))
                sub_edf = sub_edf.with_columns(pl.col("LevelOneChange").cast(pl.Float32))
                sub_edf_resample = resample_flying_factors(sub_edf)
                if not len(sub_edf) == 0:
                    data_list.append(sub_edf_resample)
            edf_resample = pl.concat(data_list)
            # edf_resample.write_parquet(os.path.join(flying_base_dir, "{}.pqt".format(symbol)))
        return edf_resample

        #         flying_open_idx = edf_resample[edf_resample["open_flying"]==True].index.tolist()
        #     flying_close_idx = edf_resample[edf_resample["close_flying"]==True].index.tolist()

    def prepare_data(self, data_params):

        select_factors = self.__select_factor_by_analysis(self.data_type,
                                                          self.symbol,
                                                          self.model_config["train_start_time"],
                                                          self.model_config["train_end_time"],
                                                          self.tagger_name_list,
                                                          self.model_config["data_config"]["thres"]
                                                          )
        self.model_config["factor_name_list"] = select_factors
        source_factor_label_df = self.__load_factor_label(self.data_type,
                                                          self.model_config["train_start_time"],
                                                          self.model_config["test_end_time"],
                                                          self.symbol,
                                                          select_factors,
                                                          self.model_config["tagger_name_list"]+["LabelReferenceMidPx"],
                                                          self.model_config["data_config"]["tagger_limit"])
        factor_label_df = source_factor_label_df.loc[:, select_factors + self.model_config["tagger_name_list"]]

        label_name = self.tagger_name_list[0]
        #############################################
        # T_train, X_train, Y_train, T_valid, X_valid, Y_valid, T_test, X_test, Y_test = self.__factor_process(
        #     factor_label_df, label_name, self.model_config["data_config"]["w_size"])
        #############################################
        edf_resample = self.__load_flying_factors()
        T_train, X_train, Y_train, T_valid, X_valid, Y_valid, T_test, X_test, Y_test = self.__factor_process_filter_by_flying(
            factor_label_df, edf_resample, label_name, self.model_config["data_config"]["w_size"])

        if not os.path.exists(self.exp_path + "/dataset/{}/".format(self.model_config["symbol_list"][0])):
            os.makedirs(self.exp_path + "/dataset/{}/".format(self.model_config["symbol_list"][0]))
        pickle.dump((T_train, X_train, Y_train, T_valid, X_valid, Y_valid, T_test, X_test, Y_test),
                    open(os.path.join(self.exp_path, "dataset/{}_flying_data.pkl".format(self.model_config["symbol_list"][0])),
                         "wb"))

        self.select_factors = select_factors
        self.factor_label_df = factor_label_df
        self.target_values = source_factor_label_df["LabelReferenceMidPx"].loc[T_test].values
        self.factor_label_df = self.factor_label_df
        self.T_train, self.X_train, self.Y_train, self.T_valid, self.X_valid, self.Y_valid, self.T_test, self.X_test, self.Y_test = T_train, X_train, Y_train, T_valid, X_valid, Y_valid, T_test, X_test, Y_test


    def train_loop(self, model_params):
        xgb_regressor = XGBRegressor(**self.model_config["xgb_config"])
        xgb_regressor.fit(self.X_train, self.Y_train,
                          eval_set=[(self.X_train, self.Y_train), (self.X_valid, self.Y_valid)],  # xgb_model = xgb_regressor_semiconductor,
                          early_stopping_rounds=15,
                          verbose=True)

        # 模型文件存储
        self.expa.model_file_save(model_obj=xgb_regressor, mode=["pkl", "onnx"], overwrite=True)
        importance_ = xgb_regressor.feature_importances_
        factor_importance = pd.DataFrame({'factor': self.select_factors+self.flying_factor, 'importance': importance_})
        factor_importance.sort_values(by='importance', ascending=False)
        print("factor_importance:", factor_importance)
        self.xgb_regressor = xgb_regressor


    def predict_signal(self, xgb_regressor, T_test, X_test, Y_test, target_values = None):
        # 加载模型
        # xgb_regressor = self.expa.model_file_load(version_alias="xgboost_base", mode="pkl")
        Y_test_pred = xgb_regressor.predict(X_test)
        # Y_test_pred_lgbm  = lgbm_regressor.predict(X_test)
        # Y_test_pred = (2*Y_test_pred+Y_test_pred_lgbm)/3
        # Y_valid_pred = xgb_regressor.predict(self.X_valid)
        # print("valid rmse", np.sqrt(mse(Y_valid_pred, self.Y_valid)))
        print("test rmse", np.sqrt(mse(Y_test_pred, Y_test)))

        # 合成并存储标准信号数据
        if not target_values.all():
            target_values = self.factor_label_df["LabelReferenceMidPx"].loc[self.T_test].values
        signal_df = self.expa.model_signal_save(label_name=self.model_config["tagger_name_list"][0],
                                           symbol=self.symbol,
                                           tm_values=T_test, yhat_values=Y_test_pred, y_values=Y_test,
                                           target_values=target_values, period=120, target_type="mid")
        print("signal_df shape: ", signal_df.shape)
        self.signal_df = signal_df

    def dyanamic_evaluate(self):
        # 加载信号数据
        # signal_df_load = self.expa.model_signal_load(version_alias=self.version_alias, symbol=self.model_config["symbol_list"][0],
        #                                         label_name=self.model_config["tagger_name_list"][0])
        for th1 in [1.2, 1.4]:
            # (1) 生成信号评价指标
            df_th1, df_th2 = self.expa.model_signal_evaluation_single_label_th_classify(
                label_name=self.model_config["tagger_name_list"][0],
                symbol=self.model_config["symbol_list"][0],
                label_th=th1, pred_th_abs_limits=[1, 6.0])
            res_detail = df_th1[df_th1["pred_pth_label_th_num"] >= 80].groupby(["pred_th"])[
                ["pred_pth_label_th_num", "pred_acc", "recall"]].agg(["mean", "count"])
            print("res_detail:", res_detail)
            
            for probs_up in [0.64, 0.66]:
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
                stats_df, pnl_stats_df = model_save_and_evaluate.model_signal_evaluation_backtest_eval_stats(signal_process_dir)
                print("signal_process_path_dir:", signal_process_dir)

                # 推荐生成的路径跟阈值目录同级
                save_file_name = os.path.join(signal_process_dir, "../..", 'local_th{}_probs{}.png'.format(th1, probs_up))
                print("plot save_file_name:", save_file_name)
                model_plot.plot_signal_backtest_results(stats_df, pnl_stats_df, save_file_name)

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
                parallel_run(signal_process_dir, plot_save_dir, self.symbol, th1=th1, prob1=probs_up)



def main(exp_name="688396.SH_trade_v0", model_config = None, train_mode = True):
    assert model_config!=None, "model_config不可为None！"

    instance = L2PXGBoostRegPack(exp_name=exp_name,
                                            model_config = model_config,
                                            version_alias="xgboost_flying"
                                            )
    if train_mode == True:
        instance.prepare_data(data_params={})
        instance.train_loop(model_params={})
        instance.predict_signal(instance.xgb_regressor, instance.T_test,
                                instance.X_test, instance.Y_test, instance.target_values)
        # instance.dyanamic_evaluate()
    else:
        # 只评价信号，不训练
        # instance.dyanamic_evaluate()
        instance.xbrain_backtest()


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
            'tree_method': 'hist',
            'gamma': 0.5,
            'learning_rate': 0.01,
            'lambda': 2,
            'subsample': 0.7,
            'colsample_bytree': 0.7,
            'max_depth': 14,
            'n_estimators': 3000,
            'seed': 4,
            "n_jobs": 30,
        },
        "metrics": {"reg_eval_abs_limits": [1.0, 3.0],
                    "reg_eval_th": 0.5},
        "model": {"name": "mlp"},
        "optimizer": {"name": "adam", "lr": 0.001, },
        "criterion": {"name": "mse"},
        "Model_save_mode": ["pkl", "onnx"],
    }

    params_list = [
        # ("603019.SH", "exp_l2p_603019.SH", {
        #     "train_start_time": "20210102",
        #     "train_end_time": "20220731",
        #     "valid_start_time": "20220801",
        #     "valid_end_time": "20230113",
        #     "test_start_time": "20230114",
        #     "test_end_time": "20230930", }),
        # ("000977.SZ", "exp_l2p_000977.SZ", {
        #     "train_start_time": "20210102",
        #     "train_end_time": "20230731",
        #     "valid_start_time": "20230801",
        #     "valid_end_time": "20231031",
        #     "test_start_time": "20231101",
        #     "test_end_time": "20231220",
        # }),
        # ("300373.SZ", "exp_l2p_300373.SZ", {
        #     "train_start_time": "20210102",
        #     "train_end_time": "20230831",
        #     "valid_start_time": "20230901",
        #     "valid_end_time": "20231131",
        #     "test_start_time": "20231201",
        #     "test_end_time": "20240123", }),
        # ("002230.SZ", "exp_l2p_002230.SZ", {
        #     "train_start_time": "20210102",
        #     "train_end_time": "20230831",
        #     "valid_start_time": "20230901",
        #     "valid_end_time": "20231131",
        #     "test_start_time": "20231201",
        #     "test_end_time": "20240123", }),
        # ("300373.SZ", "exp_l2p_300373.SZ_v1", {
        #     "train_start_time": "20210102",
        #     "train_end_time": "20231031",
        #     "valid_start_time": "20231101",
        #     "valid_end_time": "20231130",
        #     "test_start_time": "20231201",
        #     "test_end_time": "20240123", }),
        # ("002230.SZ", "exp_l2p_002230.SZ_v1", {
        #     "train_start_time": "20210102",
        #     "train_end_time": "20231031",
        #     "valid_start_time": "20231101",
        #     "valid_end_time": "20231130",
        #     "test_start_time": "20231201",
        #     "test_end_time": "20240123", }),
        ("688981.SH", "exp_l2p_688981.SH", {
            "train_start_time": "20210101",
            "train_end_time": "20230930",
            "valid_start_time": "20231001",
            "valid_end_time": "20231130",
            "test_start_time": "20231201",
            "test_end_time": "20240229",
        }),
        ("688012.SH", "exp_l2p_688012.SH", {
            "train_start_time": "20210101",
            "train_end_time": "20230930",
            "valid_start_time": "20231001",
            "valid_end_time": "20231130",
            "test_start_time": "20231201",
            "test_end_time": "20240229",
        }),
        ("688256.SH", "exp_l2p_688256.SH", {
            "train_start_time": "20210101",
            "train_end_time": "20230930",
            "valid_start_time": "20231001",
            "valid_end_time": "20231130",
            "test_start_time": "20231201",
            "test_end_time": "20240229",
        }),
        ("688271.SH", "exp_l2p_688271.SH", {
            "train_start_time": "20210101",
            "train_end_time": "20230930",
            "valid_start_time": "20231001",
            "valid_end_time": "20231130",
            "test_start_time": "20231201",
            "test_end_time": "20240229",
        }),
        ("688041.SH", "exp_l2p_688041.SH", {
            "train_start_time": "20210101",
            "train_end_time": "20230930",
            "valid_start_time": "20231001",
            "valid_end_time": "20231130",
            "test_start_time": "20231201",
            "test_end_time": "20240229",
        }),
        ("688390.SH", "exp_l2p_688390.SH", {
            "train_start_time": "20210101",
            "train_end_time": "20230930",
            "valid_start_time": "20231001",
            "valid_end_time": "20231130",
            "test_start_time": "20231201",
            "test_end_time": "20240229",
        }),
    ]


    train_mode = True #开始训练模型
    for symbol, exp_name, dataset_config in params_list:
        # if symbol != "000977.SZ":
        #     continue
        if ray.is_initialized():
            ray.shutdown()

        ray.init(num_cpus=30, object_store_memory=25000000000, local_mode=True, num_gpus=0)
        t1 = time.time()
        print(symbol, exp_name, dataset_config)
        config["symbol_list"] = [symbol]
        config["train_start_time"] =  dataset_config["train_start_time"]
        config["train_end_time"] = dataset_config["train_end_time"]
        config["valid_start_time"] = dataset_config["valid_start_time"]
        config["valid_end_time"] = dataset_config["valid_end_time"]
        config["test_start_time"] = dataset_config["test_start_time"]
        config["test_end_time"] = dataset_config["test_end_time"]

        main(exp_name=exp_name, model_config=config, train_mode = train_mode)
        print("本次试验耗时：", time.time() - t1)
        try:
            ray.shutdown()
        except:
            pass