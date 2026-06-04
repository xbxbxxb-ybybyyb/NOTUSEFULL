import sys
sys.path.insert(0, "..")
import os
import onnx
import json
import warnings
import time
warnings.filterwarnings('ignore')
import numpy as np
import pickle
from onnxmltools.convert import convert_xgboost
from skl2onnx.common.data_types import FloatTensorType, DoubleTensorType
import pandas as pd
from artifacts.model_metrics import compute_metrics, backtest_oneday
from artifacts import online_model, model_metrics, parse_format
from artifacts.model_plot import plot_signal_backtest_results
import datetime as dt
import onnxruntime as rt
from xquant.factordata import FactorData
import ray
from xgboost import XGBRegressor, XGBClassifier
from joblib import Parallel, delayed



def save_model_and_factor_list(factor_name_list, model, mode, savepath, WSIZE=1, FNUM=1):
    """因子list及 模型保存方法(主要分为pkl 或者 onnx)"""
    with open(os.path.join(savepath, "factors.csv"), "w") as f:
        for v in factor_name_list:
            f.write(json.dumps(v))
            f.write(",\n")
    print("Save factor list successed")
    for m in mode:
        if m not in ["pickle", "pkl", "onnx"]:
            raise  Exception('mode只支持"pickle", "pkl", "onnx"')
    if "pickle" in mode or "pkl" in mode:
        try:  # 临时保存
            pickle_path = os.path.join(savepath, "tmp_model.pickle.dat")
            pickle.dump(model, open(pickle_path, "wb"))
            print("Model tmped saved to Pickle at:", pickle_path)
        except Exception as e:
            print("Save pickle failed, cus:", e)
    if "onnx" in mode:
        try:
            onnx_model_converted = convert_xgboost(model, "tree-based regressor",
                                                   [("input", FloatTensorType([None, WSIZE * FNUM]))],
                                                   target_opset=10)
            onnx.save_model(onnx_model_converted, os.path.join(savepath, "model.onnx"))
            print("Save onnx success.")
        except Exception as e:
            print("Save onnx failed, cus:", e)


def load_model(mode, savepath):
    """因子list及 模型保存方法(主要分为pkl 或者 onnx)"""
    if "pickle" in mode or "pkl" in mode:
        pickle_path = os.path.join(savepath, "tmp_model.pickle.dat")
        model = pd.read_pickle(pickle_path)
        return model

    if "onnx" in mode:
        clipper_sess = rt.InferenceSession(os.path.join(savepath, "clipper.onnx"))
        scaler_sess = rt.InferenceSession(os.path.join(savepath, "scaler.onnx"))
        model_sess = rt.InferenceSession(os.path.join(savepath, "model.onnx"))
        print("onnx load success!")
        return clipper_sess, scaler_sess, model_sess


        with open(os.path.join(model_path, "configs.json"), "r") as f:
            configs = json.load(f)

        with open(os.path.join(model_path, "tables_1.json"), "r") as f:
            probs_table1 = json.load(f)
            key = list(map(float, probs_table1.keys()))
            value = list(probs_table1.values())
            probs_table1 = dict(zip(key, value))

        with open(os.path.join(model_path, "tables_2.json"), "r") as f:
            probs_table2 = json.load(f)
            key = list(map(float, probs_table2.keys()))
            value = list(probs_table2.values())
            probs_table2 = dict(zip(key, value))

        return


def generate_signal_without_class(t_values, yhat_values, y_values, target_values,  period=120, target_type="mid"):
    """回测信号生成, n_jobs若大于1则使用并发模式
    Params:
            path: 信号生成地址
            datasettype: test/valid
            yhat_df: 测试预测数据df
            table1: 置信度表格1(小涨小跌)
            table2: 置信度表格2(大涨大跌)
            probs_up:  涨置信度阈值
            probs_dw:  跌置信度阈值
            threshold: 预测值阈值，预测值小于该值直接认为0分类
            amp:    最大/最小预测边界
            period: 信号start-end持续时长
            target_type: 标签类型
    Return:
           sig_df: 信号df
    """
    assert len(yhat_values)==len(t_values), "输入数据长度不一致！"
    assert  len(yhat_values)==len(y_values) ,"输入数据长度不一致！"
    assert  len(yhat_values)==len(target_values), "输入数据长度不一致！"
    assert type(yhat_values) in [np.ndarray, list] and type(t_values) in [np.ndarray, list] and type(target_values) in [np.ndarray, list] and type(y_values) in [np.ndarray, list],"数据类型必须时numpy.array"
    yhat_df = pd.DataFrame(yhat_values, index=t_values, columns=["PREDICTED"])
    yhat_df["TARGET_VALUE"] = target_values  # 预测价格
    yhat_df["LABEL_VALUE"] = y_values
    yhat_df["DATE"] = yhat_df.index
    yhat_df["DATE"] = yhat_df["DATE"].apply(lambda x: str(x)[:10])
    yhat_df["PERIOD_BEGIN"] = yhat_df.index
    yhat_df["PERIOD_END"] = yhat_df.index + dt.timedelta(seconds=period)
    yhat_df.loc[yhat_df.index, "PREDICT"] = yhat_df["PREDICTED"]
    yhat_df.loc[yhat_df.index, "TARGET_TYPE"] = target_type
    return yhat_df

def generate_probs_table(Y_test, Y_test_pred, label_th1=1.0, label_th2=2.0, reg_eval_abs_limits=[1.0, 5.0]):
    probs_table1 = compute_metrics(Y_test_pred, Y_test, reg_eval_abs_limits = reg_eval_abs_limits, reg_eval_th = label_th1)
    probs_table2 = compute_metrics(Y_test_pred, Y_test, reg_eval_abs_limits = reg_eval_abs_limits, reg_eval_th = label_th2)
    return probs_table1, probs_table2


def generate_probs_single_label_th_classify(signal_df, label_th1, label_th2, probs_up, probs_dw, amp = 6, symbol = None, signal_process_base_dir = None):
    # 存储模型的准确率文件
    Y_test_pred, Y_test = signal_df["PREDICTED"].values, signal_df["LABEL_VALUE"].values
    probs_table1, probs_table2 = generate_probs_table(Y_test, Y_test_pred, label_th1=label_th1, label_th2=label_th2, reg_eval_abs_limits=[1, 6.0])
    table1 = online_model.parse_tab2dict(probs_table1)
    table2 = online_model.parse_tab2dict(probs_table2)

    dates = set(signal_df["DATE"].tolist())
    if not signal_process_base_dir:
        def process_inner1(signal_df):
            # 没有并行，速度慢
            signal_df["PROBABILITY"] = signal_df["PREDICTED"].apply(online_model.reg2cls, **{"predict_dict1": table1, "predict_dict2": table2,
                                                   "maxamp": amp, "minamp": -amp, "threshold": label_th1,
                                                   "probs_up": probs_up, "probs_dw": probs_dw})
            signal_df[['D_2', 'D_1', 'O_1', 'R_1', 'R_2']] = signal_df["PROBABILITY"].apply(pd.Series, index=['D_2', 'D_1', 'O_1', 'R_1', 'R_2'])
            return signal_df
        res_list = Parallel(n_jobs=20)(
            delayed(process_inner1)(signal_df[signal_df["DATE"] == v])
            for n, v in enumerate(dates))
        signal_df = pd.concat(res_list)
        return signal_df, table1, table2
    else:
        def process_inner(signal_df, signal_process_base_dir, date, symbol):
            signal_df["PROBABILITY"] = signal_df["PREDICTED"].apply(online_model.reg2cls,
                                                                    **{"predict_dict1": table1,
                                                                       "predict_dict2": table2,
                                                                       "maxamp": amp, "minamp": -amp,
                                                                       "threshold": label_th1,
                                                                       "probs_up": probs_up, "probs_dw": probs_dw})
            signal_df[['D_2', 'D_1', 'O_1', 'R_1', 'R_2']] = signal_df["PROBABILITY"].apply(pd.Series,
                                                                                            index=['D_2', 'D_1',
                                                                                                   'O_1', 'R_1',
                                                                                                   'R_2'])
            online_model.generate_signal_files(signal_df, signal_process_base_dir, date, symbol)

        res = Parallel(n_jobs=20)(
            delayed(process_inner)(signal_df[signal_df["DATE"] == v], signal_process_base_dir, v, symbol)
                for n, v in enumerate(dates))

    return signal_process_base_dir, table1, table2


def evaluate_signal_auc_table_by_day(Y_valid, Y_valid_pred, T_valid, label_th, start_date, end_date, reg_eval_abs_limits=[1, 6.0]):
    # 统计单天信号的准确率，召回率等指标
    Y_valid_date = pd.DataFrame(Y_valid, columns=["label"])
    Y_valid_date["Y_valid_pred"] = Y_valid_pred
    Y_valid_date["t"] = T_valid
    Y_valid_date["date"] = Y_valid_date["t"].apply(lambda x: x.date())
    Y_valid_date["date"] = Y_valid_date["date"].apply(lambda x: x.strftime("%Y%m%d"))
    Y_valid_date["date"] = Y_valid_date["date"].apply(lambda x: str(x))
    tmp = FactorData()
    #     list_date = tmp.tradingday(config["data_config"]["valid_start_time"],config["data_config"]["valid_end_time"])
    list_date = tmp.tradingday(start_date, end_date)
    df_1 = pd.DataFrame()
    df_2 = pd.DataFrame()
    for i in list_date:
        Y_valid_tmp = np.array(Y_valid_date[Y_valid_date["date"] == i]["label"])
        Y_valid_pred_tmp = np.array(Y_valid_date[Y_valid_date["date"] == i]["Y_valid_pred"])
        probs_table1_tmp, probs_table2_tmp, probs_table_df_1_tmp, probs_table_df_2_tmp = model_metrics.evaluate_model_by_day(
            Y_valid_tmp, Y_valid_pred_tmp,
            th1=label_th, th2=2, reg_eval_abs_limits=reg_eval_abs_limits)
        df_1_tmp = probs_table_df_1_tmp
        df_2_tmp = probs_table_df_2_tmp
        df_1_tmp["date"] = i
        df_2_tmp["date"] = i
        if df_1.empty:
            df_1 = df_1_tmp
            df_2 = df_2_tmp
            continue
        df_1 = pd.concat([df_1, df_1_tmp])
        df_2 = pd.concat([df_2, df_2_tmp])
    return df_1, df_2


def evaluate_singal_backtest_eval_stats(signal_process_base_dir, n_jobs = None, debug_mode = False):
    if ray.is_initialized():
        ray.shutdown()
    if n_jobs:
        ray.init(num_cpus = n_jobs, object_store_memory=25000000000, local_mode=False)
    else:
        ray.init(object_store_memory=25000000000, local_mode=False)
    if not debug_mode:
        remote_func = ray.remote(backtest_oneday)
        tasks = [remote_func.remote(signal_process_base_dir, v[:-4]) for n, v in enumerate(os.listdir(signal_process_base_dir)) if v.endswith("txt")]
        pnl_stats_lst = ray.get(tasks)
    else:
        # 本地运行，只跑一天
        pnl_stats_lst = [backtest_oneday(signal_process_base_dir, v[:-4]) for n, v in enumerate(os.listdir(signal_process_base_dir)[:1])]
    pnl_stats_df = pd.DataFrame(pnl_stats_lst)
    pnl_stats_df.set_index("date", drop=True, inplace=True)
    pnl_stats_df.sort_index(inplace=True)
    print("local signal backtest: pnl_stats_df finish")

    if not debug_mode:
        remote_compute_acc = ray.remote(online_model.compute_acc_single_by_file)
        tasks = [remote_compute_acc.remote(os.path.join(signal_process_base_dir, v),
                                           d_1 = 0.0012, d_2 = 0.002, r_1 = 0.0012, r_2 = 0.002, index_as_str = True) for n, v in enumerate(os.listdir(signal_process_base_dir)) if v.endswith("txt")]

        stats_lst = ray.get(tasks)
    else:
        # 本地运行, 只跑一天
        stats_lst = [online_model.compute_acc_single_by_file(os.path.join(signal_process_base_dir, v),
                                           d_1 = 0.0012, d_2 = 0.002, r_1 = 0.0012, r_2 = 0.002) for n, v in enumerate(os.listdir(signal_process_base_dir)[:1])]
    stats_df = pd.concat([i for i in stats_lst if not i.empty])
    stats_df.sort_index(inplace=True)
    print("local signal backtest: stats_df finish")
    try:
        ray.shutdown()
    except:
        pass
    return stats_df, pnl_stats_df


if __name__ == "__main__":
    base_dir = os.path.join("/data/user/quanttest007/013150/exp_result/002594.SZ-002594.SZ_trade_v00")
    TARGET_df_test, T_test, X_train, Y_train, X_valid, Y_valid, X_test, Y_test = pd.read_pickle(
        os.path.join(base_dir, "dataset/data.pkl"))
    Y_test_pred, Y_valid_pred = pd.read_pickle(os.path.join(base_dir, "dataset/data1.pkl"))


    # sig_df = generate_probs2(path, "test", yhat_df,
    #                          table1=table1, table2=table2,
    #                          probs_up=probs, probs_dw=probs,
    #                          threshold=1, amp=6, period=120,
    #                          target_type="mid", n_jobs=32)

    path = os.path.join(base_dir, "signal_files")
    # save_path, yhat_df, period=120, target_type="mid", n_jobs=32
    TARGET_test = TARGET_df_test.loc[T_test]  # 预测价格
    sig_df = generate_signal_without_class(t_values=T_test, yhat_values=Y_test_pred, y_values=Y_test,
                                           target_values=TARGET_test, period=120, target_type="mid")

    print(sig_df)
    # generate_probs_table(Y_test, Y_test_pred, th1=1.0, th2=2.0, reg_eval_abs_limits=[1.0, 5.0])


    th = 1.0
    start_date, end_date = str(T_test[0])[:10].replace("-",""), str(T_test[1])[:10].replace("-", "")
    print("th: ", th, "start_date", start_date, "end_date", end_date)
    df_th1, df_th2 = evaluate_signal_auc_table_by_day(Y_test, Y_test_pred, T_test, label_th = th, start_date=start_date,
                                        end_date=end_date,  reg_eval_abs_limits=[1, 6.0])

    print(df_th1)
    print(df_th2)
    valid_num = 100
    for i in [0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0]:
        sub_df = df_th1[(df_th1["pred_th"] == i) & (df_th1["pred_pth_num"] != 0)]
        # sub_df[sub_df["pred_pth_num"]<50]
        print(i, "预测值个数小于{}, 准确率{}， 召回率{}。".format(valid_num,
                                                   sub_df[sub_df["pred_pth_num"] < valid_num]["pred_acc"].mean(),
                                                   sub_df[sub_df["pred_pth_num"] < valid_num]["recall"].mean()))
        print(i,
              "预测值个数大于{}，准确率{}， 召回率{}。".format(valid_num, sub_df[sub_df["pred_pth_num"] > valid_num]["pred_acc"].mean(),
                                               sub_df[sub_df["pred_pth_num"] < valid_num]["recall"].mean()))

    # # signal_process_base_dir指定目标存储路径,未指定会返回sig_df
    # 问题： 考虑exp_artifacts.py中，self.version_alias可能为None的场景，如backtest_trade_file_load
    version_alias = "xgboost_base"
    label_name = "LabelFirstPeak_th10_120s"
    symbol = "000977.SZ"
    signal_df = pd.read_parquet(
        f"/data/user/016869/exp_result/exp_l2p_000977.SZ/{version_alias}/signal_files/{label_name}-{symbol}.parquet")
    sig_df, table1_json, table2_json = generate_probs_single_label_th_classify(
        signal_df,
        label_th1=1.0,
        label_th2=2.0,
        probs_up=0.62,
        probs_dw=0.62,
        amp=6,
        symbol=symbol
    )

    from artifacts.model_plot import plot_signal_backtest_results
    # signal_process_dir = "/data/user/013150/exp_result/002594.SZ-002594.SZ_trade_v00/signal_files_txt/th0.9_probs0.6/test"
    signal_process_dir = "/data/user/016869/exp_result/exp_l2p_000977.SZ/xgboost_base/LabelFirstPeak_th10_120s-000977.SZ/label_th@1.0-probs_up@0.62-probs_dw@0.62/signal_files_processed"
    stats_df, pnl_stats_df = evaluate_singal_backtest_eval_stats(signal_process_dir, debug_mode=True)
    plot_signal_backtest_results(stats_df, pnl_stats_df, save_file_name="/home/appadmin/tmp.png")

