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
from artifacts import online_model, model_save_and_evaluate
from artifacts.utils import save_backtest_result
import os
import pandas as pd
import json
import time
import shutil
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from xquant.factordata import FactorData
from tqdm import tqdm


################################################################
def main_generate_parquet(symbol, exp_version_path, data_type):
    try:
        xgb_regressor = None
        fp = FactorProvider("016869")
        factor_type = 'real_factor'
        # data_type = "enhanced_tick_norm"
        fa = FactorData()
        from xquant.marketdata import MarketData
        # ma = MarketData()
        # ma_df_all = ma.get_data_by_time_frame("STOCK", symbol, dates[0].replace("-", "") + " 093000000",
        #                                       dates[-1].replace("-", "") + " 150000000")
        dates = fa.tradingday(start_date, end_date)
        signal_path = os.path.join(exp_version_path, "signal_files")
        os.makedirs(signal_path, exist_ok=True)

        save_parquet_path = os.path.join(os.path.join(exp_version_path, f"signal_files/{label_name}-{symbol}.parquet"))
        for date in dates:
            #     model_base_dir = "/dfs/group/800657/exp_results/exp_l3_kc50_th10_60s/xgboost_base"
            model_base_dir = exp_version_path
            #     factor_name_list = pd.read_csv(os.path.join(model_base_dir, "saved_models/factors.csv"), header = None).iloc[:,0].values.tolist()
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
                factor_type = factor_type,
                factor_only = True
            )


            new_feature_label_df = feature_label_df[factor_name_list + flying_factor + [label_name]]
            if new_feature_label_df.empty:
                continue
            T_test, X_test, Y_test = get_prepared(new_feature_label_df, label_name,
                                                  model_config["data_config"]["w_size"], parallel_mode=False)
            X_test = X_test  # [:, 0]
            Y_test = Y_test.flatten()
            # print("T_test, X_test, Y_train: ", len(T_test), X_test.shape, Y_test.shape)
            # ########################预测信号###########################
            today = pd.DataFrame(X_test, columns=factor_name_list + flying_factor)
            #         factor_config = pd.read_json("/dfs/group/800657/exp_results/kc_dataset/{}_factor_config.json".format(symbol))
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

            if True:
                # factor_config = pd.read_json(os.path.join(model_base_dir, "saved_models/{}_factor_config.json".format(symbol)))
                model_path = os.path.join(model_base_dir, "saved_models/model.onnx")
                model_sess = online_model.load_onnx_model(model_path)
                model_input_name = model_sess.get_inputs()[0].name
                model_label_name = model_sess.get_outputs()[0].name
                rest = model_sess.run([model_label_name], {model_input_name: X_test_norm.astype(np.float32)})[0]
                Y_test_pred = np.array(rest)
            else:
                if not xgb_regressor:
                    xgb_regressor = pd.read_pickle(os.path.join(exp_version_path, "saved_models/tmp_model.pickle.dat"))
                Y_test_pred = xgb_regressor.predict(X_test_norm)
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

            signal_df = model_save_and_evaluate.generate_signal_without_class(symbol, T_test, Y_test_pred, Y_test, target_values,
                                                                              period=120, target_type="mid")
            # signal_df["flying_flag"] = merge_df["open_flying"]#.astype(int)

            # 显示标签和预测值相关性
            res = pd.DataFrame(Y_test_pred, columns=["pred"])
            res["label"] = Y_test
            res = res[res["label"] > -100]
            # print(date, res.corr())
            #         res.plot()

            #         #########################生成parquet文件########################
            if os.path.exists(save_parquet_path):
                try:
                    source_signal_df = pd.read_parquet(save_parquet_path)
                    source_signal_df = source_signal_df[~source_signal_df["DATE"].isin(set(signal_df["DATE"].tolist()))]
                    if not "SYMBOL" in source_signal_df.columns:
                        source_signal_df["SYMBOL"] = symbol
                    new_signal_df = pd.concat([source_signal_df, signal_df], axis=0)
                    new_signal_df.to_parquet(save_parquet_path)
                except:
                    print("WARNING: 信号文件损坏：", save_parquet_path)
                    signal_df.to_parquet(save_parquet_path)
            else:
                print("WARNING: 信号文件不存在：", save_parquet_path)
                if not "SYMBOL" in signal_df.columns:
                    signal_df["SYMBOL"] = symbol
                signal_df.to_parquet(save_parquet_path)
    #         #########################生成止盈止损指标########################
    #         date = pd.to_datetime(date).strftime("%Y-%m-%d")
    #         res_dict = winloss_func(signal_df.copy(), long_pred_th, short_pred_th,
    #                                 start_date = date, end_date = date, local_mode = True)
    # #         display(res_dict)
    #         a = pd.DataFrame(res_dict).T.iloc[:1, :].reset_index(drop = True)
    #         a.insert(0, "方向",["涨"])
    #         b = pd.DataFrame(res_dict).T.iloc[1:2, :].reset_index(drop = True)
    #         b.insert(0, "方向",["跌"])

    #         res_df= pd.concat([a, b], axis = 1)
    #         res_df.insert(0, "日期", [date])
    #         winloss_result_list.append(res_df)

    #########################画上信号图########################
    #         save_path = "/home/appadmin/{}".format(symbol)
    #         os.makedirs(save_path, exist_ok = True)
    #         signal_df["DateTime"] = signal_df["PERIOD_BEGIN"]
    #         signal_df = signal_df.set_index("DateTime")
    #         signal_df_day = online_model.generate_probs_v3(signal_df["PREDICTED"], long_pred_th, short_pred_th, amp=6, period=120, target_value=signal_df["TARGET_VALUE"].values, target_type="mid")
    #         signal_df_day.to_parquet("{}/{}.parquet".format(save_path,  pd.to_datetime(date).strftime("%Y-%m-%d")))
    #         ma_df_day = ma_df_all[ma_df_all["MDDate"]==date.replace("-", "")]
    #         fig = backtest_save_and_evaluate.backtest_plot_signal_trade(signal_df_day, trade_records_df_day = pd.DataFrame(), ma_df_day = ma_df_day, plot_save_dir = save_path)

    #         #####################画上止盈止损##########################
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
    #         fig[0].show()
    except:
        import traceback
        print(traceback.print_exc())

if __name__=="__main__":
    import ray
    symbols = pd.read_csv("/dfs/group/800657/exp_results/zz500_dataset/kc_amt_swing.csv", header=None)[0].tolist()
    symbols1 = pd.read_csv("/dfs/group/800657/exp_results/zz500_dataset/zz500_select74.csv", header=None)[0].tolist()
    symbol_list = sorted(list(sorted(set(symbols + symbols1))))
    symbol_list = symbols
    symbol_list = ["688012.SH","688041.SH","688047.SH","688256.SH","688271.SH","688498.SH","688506.SH", "688017.SH", '688981.SH', "688390.SH", "688525.SH",  "688036.SH", "688008.SH", "688036.SH"]
    symbol_list = ["688256.SH"]
    # symbol_list = ['688525.SH', '688361.SH', '688037.SH','688506.SH', '688536.SH', '688409.SH', '688318.SH','688052.SH', '688521.SH', '688390.SH', '688200.SH', '688981.SH']
    # start_date, end_date = "20240426", "20240613"
    start_date, end_date = "20240722", "20240724"


    flag_generate_parquet = True
    flag_backup_excel = False
    flag_winloss = True
    ray.init(local_mode=False)
    
    for label_name, exp_name, version_alias in [
        # #######################20240705##################
        # ("LabelFirstPeak_th10_120s", "unite_kc", "unite_kc"),
        # ("LabelFirstPeak_th10_120s", "tick_kc_basket", "tick_kc_basket"),
        # ("LabelFirstPeak_th10_120s", "l2p_kc100_v1", "l2p_kc100_v1"), 
        # ("LabelFirstPeak_th10_120s", "tick_688017.SH", "tick_688017.SH"),
        # ("LabelFirstPeak_th10_120s", "l2p_kc_basket", "l2p_kc_basket"),
        # ("LabelFirstPeak_th10_120s", "l2p_688981.SH_v1.1", "l2p_688981.SH_v1.1"),
        # ("LabelFirstPeak_th10_120s", "l2p_688111.SH_v1.1", "l2p_688111.SH_v1.1"),
        # ("LabelFirstPeak_th10_120s", "l2p_688036.SH", "l2p_688036.SH"),
        # ("LabelFirstPeak_th10_120s", "l2p_HS800_high", "l2p_HS800_high"),
        # ("LabelFirstPeak_th10_120s", "l2p_HS800_low", "l2p_HS800_low"),
        
        # ("vwap01_long_ret_60s", "exp_l3_zzkc_flying4", 'vwap01_long_ret_60s_factor98_sample_log2'),  # 对样本进行采样
        # ("vwap01_short_ret_60s", "exp_l3_zzkc_flying4", 'vwap01_short_ret_60s_factor98_sample_log2'),
        # ("smooth_long_ret_60s", "exp_l3_zzkc_flying4", 'smooth_long_ret_60s_factor98_sample_log2'),
        # ("smooth_short_ret_60s", "exp_l3_zzkc_flying4", 'smooth_short_ret_60s_factor98_sample_log2'),
        # ("dol_long_ret_60s", "exp_l3_zzkc_flying4", 'dol_long_ret_60s_factor98_sample_log2'),
        # ("dol_short_ret_60s", "exp_l3_zzkc_flying4", 'dol_short_ret_60s_60s_factor98_sample_log2'),
        # ("LabelFirstPeak_th10_60s", "KC_LabelFirstPeak_th10_60s_log", 'KC_LabelFirstPeak_th10_60s_log'),
        ("LabelFirstPeak_th10_60s", "l2p_kc2_log", 'l2p_kc2_log'),
    ]:
        # TODO 为每个模型添加测试的标的
        if exp_name == "l2p_kc100_v1":
            symbol_list = ["688498.SH"]
            data_type = "tick_l2p"
        elif exp_name == "unite_kc":
            symbol_list = ["688256.SH", "688008.SH", "688041.SH"]
            symbol_list = ["688256.SH"]
            data_type = "enhanced_tick_norm"
        elif exp_name == "tick_kc_basket":
            symbol_list = ["688256.SH", "688981.SH", "688012.SH"]
            data_type = "enhanced_tick_norm"
        elif exp_name == "tick_688017.SH":
            symbol_list = ["688017.SH"]
            data_type = "enhanced_tick_norm"
        elif exp_name == "l2p_kc_basket":
            symbol_list = ["688012.SH", "688390.SH", "688047.SH", "688271.SH", "688041.SH", "688256.SH"]
            data_type = "tick_l2p"
        elif exp_name == "l2p_688981.SH_v1.1":
            symbol_list = ["688981.SH"]
            data_type = "tick_l2p"
        elif exp_name == "l2p_688111.SH_v1.1":
            symbol_list = ["688111.SH"]
            data_type = "tick_l2p"
        elif exp_name == "l2p_688036.SH":
            symbol_list = ["688036.SH"]
            data_type = "tick_l2p"
        elif exp_name == "l2p_HS800_high":
            symbol_list = ["002920.SZ", "300033.SZ", "300223.SZ", "300308.SZ","300394.SZ", "300474.SZ", "300896.SZ"]
            data_type = "tick_l2p"
        elif exp_name == "l2p_HS800_low":
            symbol_list = ["000977.SZ", "300418.SZ", "002281.SZ"]
            data_type = "tick_l2p"
        elif exp_name == "KC_LabelFirstPeak_th10_60s_log":
            symbol_list = ["688271.SH", "688052.SH", "688012.SH", "688981.SH", "688017.SH", "688256.SH", "688047.SH",
                       "688041.SH", "688498.SH"]
            data_type = "tick_l2p"
        elif exp_name == "l2p_kc2_log":
            symbol_list = ["688271.SH", "688052.SH", "688012.SH", "688981.SH", "688017.SH", "688256.SH", "688047.SH",
                       "688041.SH", "688498.SH"][:1]
            data_type = "tick_l2p"
        t1 = time.time()
        from artifacts.parse_param import parse_target_type
        target_type = parse_target_type(label_name)  # "longshort" #评价指标的类型，mid是中间价收益率，longshort是端到端涨跌收益率
        ######################(1)生成实验数据###########################
        SYMBOL_LIST = []  # pd.read_csv("kc50.csv", header=None)[0].tolist()
        expa = exp_artifacts.ExpArtifacts(exp_name=exp_name)
        exp_path = expa.exp_path
        expa.activate_version_to_save(model_config, version_alias=version_alias)
        exp_version_path = expa.path_of_exp_version()

        if False:
            model_config = json.load(open(os.path.join(exp_version_path, "params_jsonstr.json"), "r"))
            select_factors = model_config["factor_name_list"]
            flying_factor = model_config["data_config"]["flying_factor"]
            # pd.read_csv("kc50.csv", header=None)[0].tolist()
            SYMBOL_LIST = model_config["symbol_list"]
            print("SYMBOL_LIST:", len(SYMBOL_LIST))
            print("select_factors:", len(select_factors))
        else:
            model_config["factor_name_list"] = pd.read_csv(os.path.join(exp_version_path, "saved_models/factors.csv"), header=None)[0].tolist()
            flying_factor = []
            model_config["data_config"]["flying_factor"] = flying_factor
            SYMBOL_LIST = []

        ############################(2)生成Parquet文件##############################
        if flag_generate_parquet:
            remote_func = ray.remote(main_generate_parquet)
            tasks = [remote_func.remote(symbol, exp_version_path, data_type) for symbol in symbol_list]
            ray.get(tasks)
        ############################(3)计算止盈止损率指标##############################
        if flag_winloss:
            result_list = []
            for symbol_name in symbol_list:
                try:
                    tasks_dict = {}
                    for path in ["signal_all_new.xlsx"]:
                        excel_path = os.path.join(exp_version_path, target_type + "_" + path)
                        tasks_dict[excel_path] = []
                        print("=====================" + symbol_name +"=====================")
                        try:
                            source_signal_df = expa.model_signal_load(version_alias, label_name, symbol_name)
                        except Exception as e:
                            print("ERROR: model_signal_load failed! ", e)
                            continue

                        @ray.remote(max_calls=10)
                        def inner_func(symbol_name, source_signal_df, long_pred_th, short_pred_th, start_date, end_date,
                                       target_type,
                                       win_limits):
                            res_df = winloss_func(symbol_name, source_signal_df, long_pred_th, short_pred_th,
                                                  start_date=start_date, end_date=end_date, local_mode=True,
                                                  target_type=target_type, win_limits=win_limits)
                            save_backtest_result(res_df, symbol_name, output_path=excel_path)
                            agg_df, eval_dict = winloss_func_agg(res_df, verbose=1)
                            return agg_df

                        if target_type == "mid":
                            th_list = [1.0, 1.1, 1.2, 1.4, 1.5, 1.6, 1.8, 2.0, 2.2]
                            th_list = [1.2]
                        else:
                            th_list = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4]
                        for th in th_list:
                            for win_limit in [0.001, 0.0015][1:]:
                                long_pred_th = th
                                short_pred_th = -th
                                print("=====================" + symbol_name + ":" + f"[{long_pred_th}, {short_pred_th}]" + "=====================")
                                # long short标签数量多，评价很慢
                                if target_type == "longshort":
                                    if "SHORT" in label_name.upper():
                                        long_pred_th = 20*long_pred_th
                                    if "LONG" in label_name.upper():
                                        short_pred_th = 20*short_pred_th
                                task = inner_func.remote(symbol_name, source_signal_df, long_pred_th,
                                                                short_pred_th, start_date, end_date,
                                                                target_type=target_type, win_limits=[win_limit])
                                tasks_dict[excel_path].append(task)
                    for excel_path in tasks_dict.keys():
                        results = ray.get(tasks_dict[excel_path])
                        result_agg_df = pd.concat(results)
                        save_backtest_result(result_agg_df, symbol_name,
                                             output_path=excel_path.replace("new.xlsx", "agg_new.xlsx"))
                except Exception as e:
                    import traceback
                    print(traceback.print_exc())
                    print(e)
                    pass
        print("耗时：", time.time()-t1)
    ray.shutdown()