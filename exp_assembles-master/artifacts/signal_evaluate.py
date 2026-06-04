from artifacts.dataload_utils import get_l2p_data
from artifacts.flying_functions import load_flying_factors
from artifacts.signal_evaluate_order import allSignalOrder,firstSignalOrder,TradingEvaluate
from artifacts.utils import save_and_append_parquet
from artifacts import exp_artifacts
from xquant.factordata import FactorData
import polars as pl
import pandas as pd
import copy
import time
import ray
import os
from xquant.xqutils.perf_profile import profile
from matplotlib import pyplot as plt


def load_prediction_data(signal_file, symbol_name, flying_adjust = False):
    if not os.path.exists(signal_file):
        print("model_signal_load error: no such file: ", signal_file)
        return pd.DataFrame()
    source_signal_df = pd.read_parquet(signal_file)

    if len(source_signal_df) == 0:
        raise Exception("{} {} {}数据为空！".format(signal_file, start_date, end_date))
    if flying_adjust:
        fa = FactorData()
        dates = fa.tradingday(start_date.replace("-", ""), end_date.replace("-", ""))
        flying_factors = ["PriceSpread", "CumOrdersNetVolOverV0", "BreakingP0NumOrders", "OneBigOrder",
                          "OneBigOrderExtend"]
        edf_resample = load_flying_factors(symbol_name, dates=dates, flying_factors=flying_factors,
                                           sample_method="sum")

        edf_resample = edf_resample.with_columns(
            open_flying_direction=pl.when(pl.col("PriceSpread") > 0).then(1).otherwise(
                pl.when(pl.col("PriceSpread") < 0).then(-1).otherwise(
                    pl.when(pl.col("CumOrdersNetVolOverV0") > 0).then(1).otherwise(
                        pl.when(pl.col("CumOrdersNetVolOverV0") < 0).then(-1).otherwise(
                            pl.when(pl.col("BreakingP0NumOrders") > 0).then(1).otherwise(
                                pl.when(pl.col("BreakingP0NumOrders") < 0).then(-1).otherwise(
                                    pl.when(pl.col("OneBigOrder") > 0).then(1).otherwise(
                                        pl.when(pl.col("OneBigOrder") < 0).then(-1).otherwise(
                                            pl.when(pl.col("OneBigOrderExtend") > 0).then(1).otherwise(
                                                pl.when(pl.col("OneBigOrderExtend") < 0).then(
                                                    -1).otherwise(
                                                    0
                                                ))))))))))
        ).select(["DateTime", "open_flying", "open_flying_direction"] + flying_factors).to_pandas()
        source_signal_df["DateTime"] = pd.to_datetime(source_signal_df["PERIOD_BEGIN"])
        source_signal_df["open_flying_deriction"] = source_signal_df.merge(
            edf_resample, left_on="DateTime", right_on="DateTime", how="left")["open_flying_direction"].values
        print(source_signal_df["open_flying_deriction"].values)
        source_signal_df["PREDICT"] = source_signal_df.apply(
            lambda x: x['PREDICT'] if x["PREDICT"] * x["open_flying_deriction"] >= 0 else 0, axis=1)
        source_signal_df["PREDICTED"] = source_signal_df.apply(
            lambda x: x['PREDICTED'] if x["PREDICTED"] * x["open_flying_deriction"] >= 0 else 0, axis=1)

    return source_signal_df


@ray.remote(max_calls=5)
def SignalEvaluateRemote(symbol_name, long_source_signal_df, short_source_signal_df, para, start_date, end_date,
                         start_time="09:31:00", end_time="14:50:00", base_dir="./", signal_name="", verbose=0,
                         first_point=True):
    return SignalEvaluate(symbol_name, long_source_signal_df, short_source_signal_df, para, start_date, end_date,
                          start_time, end_time, base_dir, signal_name, verbose, first_point)


def SignalEvaluate(symbol_name, long_source_signal_df, short_source_signal_df, para, start_date, end_date,
                   start_time="09:31:00", end_time="14:50:00", base_dir="./", signal_name="", verbose=0,
                   first_point=True, weight_by_daynum=False):
    """
    :param symbol_name:
    :param long_source_signal_df: 涨信号阈值
    :param short_source_signal_df: 跌信号阈值
    :param para: 信号回测参数
    :param start_time:
    :param end_time:
    :param base_dir: verbose>2时，将信号每日数据保存到该文件夹
    :param verbose: 日志选项，默认0，大于2时将信号每日数据保存到文件
    :param first_point: 若为True，使用firstSignalOrder，对一段时间内连续的同向的有效信号点（达到阈值）至只评价第一个， 若为False，使用allSignalOrder函数，对所有有效信号点都评价
    :param  weight_by_daynum, 是否按每日的信号数量加权平均，默认为False，直接按天平均
    :return:
    """

    def process_source_signal_df(source_signal_df, l2p_df):
        source_signal_df = pl.from_pandas(source_signal_df)
        source_signal_df = source_signal_df.with_columns(time=pl.col("PERIOD_BEGIN").dt.strftime("%H:%M:%S")).filter(
            (pl.col("time") >= "{}".format(start_time)) & (
                    pl.col("time") <= "{}".format(end_time)))
        source_signal_df = source_signal_df.with_columns(
            timestamp=pl.col("PERIOD_BEGIN").dt.replace_time_zone("Asia/Shanghai").dt.timestamp(
                time_unit="ms") / 1000.0,
            DateTime=pl.col("PERIOD_BEGIN"),
            SYMBOL=pl.lit(symbol_name)
        )
        merge_signal_df = source_signal_df.join(l2p_df, on="DateTime")
        merge_signal_df = merge_signal_df.to_pandas()
        merge_signal_df = merge_signal_df.rename(columns={
            "SYMBOL": "code", "timestamp": "startTimeStamp", "M_SellPrice": "askPrice", "M_BuyPrice": "bidPrice"
        })
        return merge_signal_df

    start_date1, end_date1 = long_source_signal_df["DATE"].min(), long_source_signal_df["DATE"].max()
    start_date2, end_date2 = short_source_signal_df["DATE"].min(), short_source_signal_df["DATE"].max()
    all_start_date = max(start_date1, start_date2)
    all_end_date = min(end_date1, end_date2)

    fa = FactorData()
    dates = fa.tradingday(all_start_date.replace("-", ""), all_end_date.replace("-", ""))
    if len(dates) < 3:
        raise Exception("前2天的数据作为样本内数据，动态生成阈值, 当前DataFrame只有{}天的数据！".format(dates))
    try:
        insample_start_date = dates[max(dates.index(start_date.replace("-", "")) - 2, 1)]
    except Exception as e:
        print(f"信号数据无{start_date} 的数据: {e}.")
        return pd.DataFrame()
    dates = [date[:4] + "-" + date[4:6] + "-" + date[6:] for date in dates if date >= insample_start_date]
    try:
        l2p_df = get_l2p_data(symbol_name, insample_start_date, end_date.replace("-", "")).select(
            ["DateTime", "M_SellPrice", "M_BuyPrice", "Bid1P", "Ask1P", "M_OpenPx"])
    except Exception as e:
        print(f"get_l2p_data未查询到{symbol_name}-{insample_start_date}-{end_date.replace('-', '')} 的数据: {e}.")
        return pd.DataFrame()
    long_merge_signal_df = process_source_signal_df(long_source_signal_df, l2p_df)
    short_merge_signal_df = process_source_signal_df(short_source_signal_df, l2p_df)

    tradingOrder_list = []
    start_date = pd.to_datetime(start_date).strftime("%Y-%m-%d")
    end_date = pd.to_datetime(end_date).strftime("%Y-%m-%d")
    for didx, date in enumerate(dates):
        try:
            if didx < 2 or date < start_date or date > end_date:
                continue
            # 前2天的数据作为样本内数据，动态生成阈值
            insample_date = dates[didx - 2]
            long_signal_df = long_merge_signal_df[long_merge_signal_df["DATE"] == date]
            long_insample_signal_df = long_merge_signal_df[
                (long_merge_signal_df["DATE"] < date) & (long_merge_signal_df["DATE"] >= insample_date)]
            outSampleLongPredict = long_signal_df["PREDICTED"].values
            inSampleLongPredict = long_insample_signal_df["PREDICTED"].values

            short_signal_df = short_merge_signal_df[short_merge_signal_df["DATE"] == date]
            short_insample_signal_df = short_merge_signal_df[
                (short_merge_signal_df["DATE"] < date) & (short_merge_signal_df["DATE"] >= insample_date)]
            if short_insample_signal_df.empty or long_insample_signal_df.empty:
                print("WARNING: data empty!", date, symbol_name)
                continue
            outSampleShortPredict = short_signal_df["PREDICTED"].values
            inSampleShortPredict = short_insample_signal_df["PREDICTED"].values
            if first_point:
                # 只评价第一个同向的有效信号点
                tradingOrder, pred_up, pred_dw = firstSignalOrder(outSampleLongPredict, inSampleLongPredict,
                                                                  outSampleShortPredict, inSampleShortPredict, para,
                                                                  long_signal_df, verbose=verbose, return_th=True)
            else:
                # 评价所有的有效信号点
                tradingOrder, pred_up, pred_dw = allSignalOrder(outSampleLongPredict, inSampleLongPredict,
                                                                outSampleShortPredict, inSampleShortPredict, para,
                                                                long_signal_df, verbose=verbose, return_th=True)
            ################# 统计不同平仓类型的收益 #############
            tradingOrder = TradingEvaluate(tradingOrder, pred_up, pred_dw, verbose=verbose)
            tradingOrder["symbol"] = symbol_name
            tradingOrder["date"] = date
            tradingOrder_list.append(tradingOrder)

        except Exception as e:
            from traceback import print_exc
            print(print_exc())
            print("SignalEvaluate", e, symbol_name, date)
            continue

    tradingOrder_df = pd.DataFrame(tradingOrder_list)
    if not weight_by_daynum:
        # 按天取平均
        tradingOrder_df["weight"] = 1 / tradingOrder_df["numAaverageDay"].count()
    else:
        # 按每天的开平仓次数加权
        tradingOrder_df["weight"] = tradingOrder_df["numAaverageDay"] / tradingOrder_df["numAaverageDay"].sum()
        # 其他都按weight加权，信号数量不能加权
        tradingOrder_df["numAaverageDay"] = tradingOrder_df["numAaverageDay"] / tradingOrder_df["weight"]

    column_type_dict = tradingOrder_df.dtypes.to_dict()
    result_agg_dict = {}
    for column in column_type_dict:
        if column in ["weight"]:
            continue
        if column in ["triggerTimes", "longTimes", "shortTimes", "winTimes"]:
            result_agg_dict[column] = tradingOrder_df[column].mean()
        if str(column_type_dict[column]).startswith("float") or str(column_type_dict[column]).startswith("int"):
            result_agg_dict[column] = (tradingOrder_df[column] * tradingOrder_df["weight"]).sum()

    result_agg_dict["SYMBOL"] = symbol_name
    result_agg_dict["para"] = str(para)
    result_agg_dict["winLimit"] = para["winLimit"]
    result_agg_dict["lossLimit"] = para["lossLimit"]
    result_agg_dict["longTriggerRatioPercentile"] = para["longTriggerRatioPercentile"]
    result_agg_dict["shortTriggerRatioPercentile"] = para["shortTriggerRatioPercentile"]
    result_agg_dict["exp_version"] = signal_name
    if verbose > 1:
        debug_path = os.path.join(base_dir, f'{symbol_name}_win{int(para["winLimit"] * 10000)}_loss{-int(para["lossLimit"] * 10000)}_detail.pkl')
        os.makedirs(base_dir, exist_ok=True)
        # 不支持并行写文件
        tradingOrder_df["exp_verion"] = signal_name
        tradingOrder_df.to_pickle(debug_path)

    tradingOrder_df_agg = pd.DataFrame([result_agg_dict])

    return tradingOrder_df_agg

@ray.remote(max_calls=5)
def grid_evaluate_remote(signal_files, symbol_name, sig_para, signal_name, start_date,
                  end_date, base_dir="./", verbose=0, flying_adjust = False, first_point=True):
    return grid_evaluate(signal_files, symbol_name, sig_para, signal_name, start_date,
                  end_date, base_dir=base_dir, verbose=verbose, flying_adjust = flying_adjust, first_point=first_point)


def grid_evaluate(signal_files, symbol_name, sig_para, signal_name, start_date,
                  end_date, base_dir="./", verbose=0, flying_adjust = False, first_point=True):
    """
    :param symbol_name:
    :param sig_para:
    :param signal_name: 信号名称标记，一般是版本名
    :return:
    """
    tasks = []
    if type(signal_files)==str:
        source_signal_df = load_prediction_data(signal_files, symbol_name, flying_adjust = flying_adjust)
        long_source_signal_df = source_signal_df
        short_source_signal_df = source_signal_df
    elif type(signal_files)==list and len(signal_files)==2:
        long_source_signal_df = load_prediction_data(signal_files[0], symbol_name, flying_adjust = flying_adjust)
        short_source_signal_df = load_prediction_data(signal_files[1], symbol_name, flying_adjust = flying_adjust)

    if long_source_signal_df.empty or short_source_signal_df.empty:
        return

    result_list = []
    for pctline in [1]:
        # for winLimit in [0.002, 0.003, 0.005, 0.008, 0.01]:
        #     for lossLimit in [-0.002, -0.003, -0.005, -0.008, -0.01]:
        for winLimit in [0.0015, 0.004, 0.006]:
            for lossLimit in [-0.002]:
                tmp_para = copy.deepcopy(sig_para)
                tmp_para["winLimit"] = winLimit
                tmp_para["lossLimit"] = lossLimit
                tmp_para["longTriggerRatioPercentile"] = 100 - pctline
                tmp_para["shortTriggerRatioPercentile"] = pctline
                task = SignalEvaluate(symbol_name, long_source_signal_df, short_source_signal_df, tmp_para,
                                       start_date, end_date, verbose=verbose, signal_name=signal_name,
                                       base_dir=base_dir, first_point=first_point)
                result_list.append(task)
    result_df = pd.concat(result_list)
    save_parquet_path = os.path.join(base_dir, "{}.parquet".format(symbol_name))
    save_and_append_parquet(symbol_name, result_df, save_parquet_path, overwrite_col="exp_version")
    print(result_df)


def main_grid_evaluate(exp_list, symbol_list, target_type, start_date, end_date, para,
                       base_dir="/dfs/group/800657/library/tmp_l3_event/signal_evaluate_log2", verbose=0,
                       first_point=False, flying_adjust = False, test_mode = False):
    if target_type == "mid":
        print("WARING: target_type是mid， 将按midprice标签方式评价！！")
    elif target_type=="longshort":
        print("WARING: target_type是longshort， 将按AskBidPrice标签方式评价！！")
    else:
        raise Exception()

    time.sleep(5)
    if test_mode:
        exp_list = exp_list[:1]
        symbol_list = test_mode[:1]
    if target_type == "mid":
        for label_name, exp_name, version_alias in exp_list:
            base_dir1 = os.path.join(base_dir, version_alias)
            os.makedirs(base_dir1, exist_ok=True)
            tasks = []
            for symbol_name in symbol_list:
                t1 = time.time()
                try:
                    signal_files = f"/dfs/group/800657/exp_results/{exp_name}/{version_alias}/signal_files/{label_name}-{symbol_name}.parquet"
                    if test_mode:
                        grid_evaluate(signal_files, symbol_name, para, start_date=start_date,
                                      end_date=end_date, signal_name=exp_name + "-" + version_alias,
                                      base_dir=base_dir1, verbose=verbose, first_point=first_point,
                                      flying_adjust=flying_adjust)
                        print("耗时：", time.time() - t1)
                    else:
                        tasks.append(grid_evaluate_remote.remote(signal_files, symbol_name, para, start_date=start_date,
                                                                 end_date=end_date,
                                                                 signal_name=exp_name + "-" + version_alias,
                                                                 base_dir=base_dir1, verbose=verbose,
                                                                 first_point=first_point, flying_adjust=flying_adjust))
                except Exception as e:
                    print("model_signal_load error: ", e)
            if not test_mode:
                ray.get(tasks)
    else:
        t1 = time.time()
        for label_name, exp_name, version_alias in [
            # #######################20240710##################
            # ("vwap01_long_ret_60s", "exp_l3_zzkc_flying4", 'vwap01_long_ret_60s_factor98_sample_trim'),#截取0.5以下的标签
            ("smooth_long_ret_60s", "exp_l3_zzkc_flying4", 'smooth_long_ret_60s_factor98_sample_trim'),
            # ("dol_long_ret_60s", "exp_l3_zzkc_flying4", 'dol_long_ret_60s_factor98_sample_trim'),
        ]:
            tasks = []
            for symbol_name in symbol_list:
                base_dir1 = os.path.join(base_dir, version_alias)
                os.makedirs(base_dir1, exist_ok=True)

                long_signal_file = f"/dfs/group/800657/exp_results/{exp_name}/{version_alias}/signal_files/{label_name}-{symbol_name}.parquet"
                version_alias_short = version_alias.replace("Long", "Short")
                label_name_short = label_name.replace("Long", "Short")
                short_signal_file = f"/dfs/group/800657/exp_results/{exp_name}/{version_alias_short}/signal_files/{label_name_short}-{symbol_name}.parquet"
                signal_files = [long_signal_file, short_signal_file]
                if test_mode:
                    grid_evaluate(signal_files, symbol_name, para, start_date=start_date,
                              end_date=end_date, signal_name=exp_name + "-" + version_alias,
                              base_dir=base_dir1, verbose=verbose, first_point=first_point, flying_adjust = flying_adjust)
                    print("耗时：", time.time() - t1)
                else:
                    tasks.append(grid_evaluate_remote.remote(signal_files, symbol_name, para, start_date=start_date,
                              end_date=end_date, signal_name=exp_name + "-" + version_alias,
                              base_dir=base_dir1, verbose=verbose, first_point=first_point, flying_adjust = flying_adjust))
            if not test_mode:
                ray.get(tasks)


if __name__ == '__main__':
    target_type = "mid"  # parse_target_type(label_name)
    if target_type == "mid":
        para = {
            "longMinTriggerRatio": 1.0,
            "shortMinTriggerRatio": -1.0,
            "longTriggerRatioPercentile": 95,
            "shortTriggerRatioPercentile": 5,
            "lossLimit": -0.005,
            "winLimit": 0.005,
            "target_type": "mid"
        }
    elif target_type == "longshort":
        para = {
            "longMinTriggerRatio": 1.0,
            "shortMinTriggerRatio": -1.0,
            "longTriggerRatioPercentile": 95,
            "shortTriggerRatioPercentile": 5,
            "lossLimit": -0.002,
            "winLimit": 0.0015,
            "target_type": "longshort"
        }
    else:
        raise Exception("target_type error: ", target_type)
    exp_list = [
            ##################20240716##################
            # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4_levelone", 'LabelFirstPeak_th12_60s_factor98_levelone_log2'),
            # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4_levelone", 'LabelFirstPeak_th12_60s_factor98_levelone_amp_log2'),
            # ("LabelFirstPeak_th10_120s", "l2p_kc_basket", "l2p_kc_basket"),
            # ("LabelFirstPeak_th10_120s", "l2p_kc2_log", "l2p_kc2_log"),
            # ("LabelFirstPeak_th10_120s", "l2p_688981.SH_v1.1", "l2p_688981.SH_v1.1"),
            # ("LabelFirstPeak_th10_120s", "l2p_688111.SH_v1.1", "l2p_688111.SH_v1.1"),
            # ("LabelFirstPeak_th10_120s", "l2p_kc100_v1", "l2p_kc100_v1"),
            ("LabelFirstPeak_th10_120s", "unite_kc", "unite_kc"),
            # ("LabelFirstPeak_th12_60s", "l3_zzkc_flying4_log2", 'l3_zzkc_flying4_log2'),
            #("LabelFirstPeak_th10_120s", "signal_df_0802", "signal_df_0802"),
            #("LabelFirstPeak_th10_120s", "signal_df_0802_resnet", "signal_df_0802_resnet"),
        ]
    start_date = "2024-08-12"
    end_date = "2024-08-12"
    symbol_list = ["688012.SH", "688041.SH", "688047.SH", "688256.SH", "688271.SH", "688498.SH", "688506.SH",
                   "688017.SH", '688981.SH', "688390.SH", "688525.SH", "688036.SH", "688008.SH", "688036.SH"]
    ray.init(local_mode=True)
    for label_name, exp_name, version_alias in exp_list:
        # TODO 为每个模型添加测试的标的
        if exp_name == "l2p_kc100_v1" and version_alias == "l2p_kc100_v1":
            symbol_list = ["688498.SH"]
        elif exp_name == "unite_kc" and version_alias == "unite_kc":
            symbol_list = ["688256.SH", "688008.SH", "688041.SH"]
            # symbol_list = ["688041.SH"]
        elif exp_name == "tick_kc_basket" and version_alias == "tick_kc_basket":
            symbol_list = ["688256.SH", "688981.SH", "688012.SH"]
        elif exp_name == "tick_688017.SH" and version_alias == "tick_688017.SH":
            symbol_list = ["688017.SH"]
        elif exp_name == "l2p_kc_basket" and version_alias == "l2p_kc_basket":
            symbol_list = ["688012.SH", "688390.SH", "688047.SH", "688271.SH", "688041.SH", "688256.SH"]
            # symbol_list = ["688012.SH", "688041.SH"]
        elif exp_name == "l2p_688981.SH_v1.1" and version_alias == "l2p_688981.SH_v1.1":
            symbol_list = ["688981.SH"]
        elif exp_name == "l2p_688111.SH_v1.1" and version_alias == "l2p_688111.SH_v1.1":
            symbol_list = ["688111.SH"]
        elif exp_name == "l2p_688036.SH" and version_alias == "l2p_688036.SH":
            symbol_list = ["688036.SH"]
        elif exp_name == "l2p_HS800_high" and version_alias == "l2p_HS800_high":
            symbol_list = ["002920.SZ", "300033.SZ", "300223.SZ", "300308.SZ", "300394.SZ", "300474.SZ", "300896.SZ"]
        elif exp_name == "l2p_HS800_low" and version_alias == "l2p_HS800_low":
            symbol_list = ["000977.SZ", "300418.SZ", "002281.SZ"]
        elif exp_name == "l2p_kc2_log" and version_alias == "l2p_kc2_log":
            symbol_list = ['688256.SH', '688036.SH', '688390.SH', '688012.SH', '688047.SH', '688041.SH', '688981.SH',
                           '688111.SH', '688491.SH']
        elif exp_name in ["signal_df_0802", "signal_df_0802_resnet"]:
            symbol_list = ["688981.SH", "688256.SH"]
        elif exp_name == "exp_l3_zzkc_flying4_levelone":
            symbol_list = ['688256.SH', '688036.SH', '688390.SH', '688012.SH', '688047.SH', '688041.SH', '688981.SH',
                           '688111.SH', '688491.SH']
        elif exp_name == "l3_zzkc_flying4_log2" and version_alias == "l3_zzkc_flying4_log2":
            symbol_list = ['688256.SH', '688036.SH', '688390.SH', '688012.SH', '688047.SH', '688041.SH', '688981.SH',
                           '688111.SH', '688491.SH']
        elif exp_name == "exp_l3_zzkc_flying4":
            symbol_list = ['688256.SH', '688036.SH', '688390.SH', '688012.SH', '688047.SH', '688041.SH', '688981.SH',
                           '688111.SH', '688491.SH']
        # elif exp_name == "KC_LabelFirstPeak_th10_60s_log":
        #     symbol_list = ["688271.SH", "688052.SH", "688012.SH", "688981.SH", "688017.SH", "688256.SH",
        #                    "688047.SH", "688041.SH", "688498.SH"]
        else:
            symbol_list = symbol_list
        # verbose为2生成detail文件
        main_grid_evaluate([[label_name, exp_name, version_alias]], symbol_list, target_type,
                           start_date, end_date, para,
                           base_dir="/dfs/group/800657/library/tmp_l3_event/signal_evaluate_log2", verbose=2,
                           first_point=False, flying_adjust=False)

