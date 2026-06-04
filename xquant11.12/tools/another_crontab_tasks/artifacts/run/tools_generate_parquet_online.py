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

import os
import json
import polars as pl

#################################################
SYMBOL_LIST = []

flying_factor = ["PriceSpread", "OneBigOrder", "CumOrdersNetVolOverV0", "BreakingP0NumOrders", "LevelOneChange"]
flying_factor = pd.read_csv("extra_factors.csv", header=None)[0].tolist()
flying_factor = []

model_config["data_config"]["flying_factor"] = flying_factor
model_config["symbol_list"] = SYMBOL_LIST
model_config["train_start_time"] = "20210101"
model_config["train_end_time"] = "20231015"
model_config["valid_start_time"] = "20231016"
model_config["valid_end_time"] = "20231214"
model_config["test_start_time"] = "20231215"
model_config["test_end_time"] = "20240422"

model_config["tagger_name_list"] = ["LabelFirstPeak_th12_60s"] #"LabelFirstPeak_th10_60s"
exp_name = "exp_l3_kc50_th12_60s_flying4"
# exp_name = "exp_l3_kc50_th12_60s"
version_alias = "xgboost_base"
label_name = model_config["tagger_name_list"][0]

######################################
expa = exp_artifacts.ExpArtifacts(exp_name = exp_name)
exp_path = expa.exp_path
expa.activate_version_to_save(model_config, version_alias = "xgboost_base")
exp_version_path = expa.path_of_exp_version()
if False:
    model_config = json.load(open(os.path.join(exp_version_path, "params_jsonstr.json"), "r"))
    select_factors= model_config["factor_name_list"]
    flying_factor = model_config["data_config"]["flying_factor"]
#     print(flying_factor)


# SYMBOL_LIST

##############################################################
from artifacts import online_model, model_save_and_evaluate
import os
import json
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from xquant.factordata import FactorData
from tqdm import tqdm


winloss_result_list = []
################################################################
def main_generate_parquet(symbol):
    xgb_regressor = None
    fd = FactorProvider("016869")
    # factor_type = 'real_factor'
    factor_type = 'factor'
    data_type = "enhanced_tick"#"tick_l2p"
    fa = FactorData()
    from xquant.marketdata import MarketData
    ma = MarketData()
    dates = fa.tradingday(start_date, end_date)

    if True:
        ma_df_all = ma.get_data_by_time_frame("STOCK", symbol, dates[0].replace("-", "") + " 093000000",
                                              dates[-1].replace("-", "") + " 150000000")
        for date in dates:
            factor_name_list = pd.read_csv(os.path.join(model_base_dir, "factors.csv"), header=None).iloc[:,
                               0].values.tolist()
            flying_factor = model_config["data_config"]["flying_factor"]
            # ########################生成采样数据###########################
            # 加载因子库中因子数据
            factor_df_online = fd.load_public_data_from_dfs(symbol=[symbol], factor_list=factor_name_list,
                                                            start_time=start_date, end_time=end_date,
                                                            factor_type=factor_type,
                                                            data_type=data_type
                                                            )
            factor_df_online.dropna(inplace=True, axis=0, how="all")
            factor_df_online["date"] = factor_df_online["timestamp"].apply(lambda x: x.strftime("%Y%m%d"))
            factor_df_online = factor_df_online.set_index("timestamp")
            date_list = sorted(list(set(factor_df_online["date"].tolist())))

            flying_factor_df = load_flying_factors(symbol, dates=[date], use_pandas=False,
                                                   flying_base_dir="/dfs/group/800657/library/l3_event/event_data")
            if len(flying_factor_df) == 0:
                continue
            flying_factor_df = flying_factor_df.to_pandas()
            flying_factor_df = flying_factor_df.set_index("DateTime")

            merge_df = pd.merge(factor_df_online, flying_factor_df, left_index=True, right_index=True, how="inner")
            new_feature_label_df = merge_df[factor_name_list + flying_factor]
            new_feature_label_df[label_name] = 0
            print("factor_df_online: ", factor_df_online.shape, ", new_feature_label_df: ", new_feature_label_df.shape)
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
            factor_config = pd.read_json(os.path.join(model_base_dir, "{}_factor_config.json".format(symbol)))
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

            if True:
                # factor_config = pd.read_json(os.path.join(model_base_dir, "l3_kc50_flying4/{}_factor_config.json".format(symbol)))
                model_path = os.path.join(model_base_dir, "model.onnx")
                model_sess = online_model.load_onnx_model(model_path)
                model_input_name = model_sess.get_inputs()[0].name
                model_label_name = model_sess.get_outputs()[0].name
                rest = model_sess.run([model_label_name], {model_input_name: X_test_norm.astype(np.float32)})[0]
                Y_test_pred = np.array(rest)
            else:
                if not xgb_regressor:
                    xgb_regressor = pd.read_pickle(os.path.join(model_base_dir, "l3_kc50_flying4/tmp_model.pickle.dat"))
                Y_test_pred = xgb_regressor.predict(X_test_norm)
            # ########################生成信号数据###########################
            factor_df_online = fd.load_public_data_from_dfs(symbol=[symbol], factor_list=["ReferenceMidPrice"],
                                                            start_time=date, end_time=date,
                                                            factor_type=factor_type, data_type=data_type)
            factor_df_online = factor_df_online[factor_df_online["timestamp"].isin(T_test)]
            target_values = factor_df_online["ReferenceMidPrice"].values
            signal_df = model_save_and_evaluate.generate_signal_without_class(T_test, Y_test_pred, Y_test,
                                                                              target_values, period=120,
                                                                              target_type="mid")
            signal_df["open_flying"] = merge_df["open_flying"]
            signal_df["PREDICTED"] = signal_df["PREDICTED"] * signal_df["open_flying"]
            signal_df["PREDICT"] = signal_df["PREDICT"] * signal_df["open_flying"]

            # 显示标签和预测值相关性
            res = pd.DataFrame(Y_test_pred, columns=["pred"])
            res["label"] = Y_test
            res = res[res["label"] > -100]
            print(date, res.corr())
            res.plot()

            #########################生成parquet文件########################
            save_parquet_path = "/home/appadmin/signal_files/"
            # save_parquet_path = os.path.join(os.path.join(model_base_dir, f"signal_files/{label_name}-{symbol}.parquet"))
            # source_signal_df = pd.read_parquet(save_parquet_path)
            # source_signal_df = source_signal_df[~source_signal_df["DATE"].isin(set(signal_df["DATE"].tolist()))]
            # new_signal_df = pd.concat([source_signal_df, signal_df], axis = 0)
            new_signal_df.to_parquet(save_parquet_path)

            #         #########################生成止盈止损指标########################
            # date = pd.to_datetime(date).strftime("%Y-%m-%d")
            # res_dict = winloss_func(signal_df.copy(), long_pred_th, short_pred_th,
            #                         start_date=date, end_date=date, local_mode=True)
            # print(symbol, res_dict)
            # a = pd.DataFrame(res_dict).T.iloc[:1, :].reset_index(drop=True)
            # a.insert(0, "方向", ["涨"])
            # b = pd.DataFrame(res_dict).T.iloc[1:2, :].reset_index(drop=True)
            # b.insert(0, "方向", ["跌"])
            #
            # res_df = pd.concat([a, b], axis=1)
            # res_df.insert(0, "日期", [date])
            # winloss_result_list.append(res_df)
            #
            # #########################画上信号图########################
            # save_path = "/home/appadmin/{}".format(symbol)
            # os.makedirs(save_path, exist_ok=True)
            # signal_df["DateTime"] = signal_df["PERIOD_BEGIN"]
            # signal_df = signal_df.set_index("DateTime")
            # signal_df_day = online_model.generate_probs_v3(signal_df["PREDICTED"], long_pred_th, short_pred_th, amp=6,
            #                                                period=120, target_value=signal_df["TARGET_VALUE"].values,
            #                                                target_type="mid")
            # signal_df_day.to_parquet("{}/{}.parquet".format(save_path, pd.to_datetime(date).strftime("%Y-%m-%d")))
            # ma_df_day = ma_df_all[ma_df_all["MDDate"] == date.replace("-", "")]
            # fig = backtest_save_and_evaluate.backtest_plot_signal_trade(signal_df_day,
            #                                                             trade_records_df_day=pd.DataFrame(),
            #                                                             ma_df_day=ma_df_day, plot_save_dir=save_path)
            #
            # #         #####################画上止盈止损##########################
            #         import plotly.graph_objects as go
            #         res_df = pd.DataFrame(res_dict).T.iloc[:2, :]
            #         res_df.insert(0, "方向",["涨", "跌"])
            #         # 将DataFrame转换为Plotly表格所需的数据格式

            #        # 创建一个Figure对象并将表格添加进去
            #         fig[0].add_trace( go.Table(
            #                 header=dict(values=list(res_df.columns),
            #                            fill_color='paleturquoise',
            #                            align='left'),
            #                 cells=dict(values=[res_df[col].tolist() for col in res_df.columns],
            #                            fill_color='lavender',
            #                            align='left')))
            # fig[0].update_layout(width=800, height=600)
            # fig[0].show()


import ray
# model_base_dir = "/data/user/013150/trade_data/COO/l3_kc50_flying4/l3_kc50_flying4"
model_base_dir = "/data/user/013150/trade_data/COO/unite_kc/unite_kc"

symbol_list = ["688256.SH"]#["688012.SH","688041.SH","688047.SH","688256.SH","688271.SH","688036.SH","688169.SH","688506.SH"]
long_pred_th, short_pred_th = 1.5, -1.5
start_date, end_date = "20240520", "20240520"
# start_date, end_date = "20240321", "20240416"
remote_func = ray.remote(main_generate_parquet)
tasks = [remote_func.remote(symbol) for symbol in symbol_list]
ray.get(tasks)
