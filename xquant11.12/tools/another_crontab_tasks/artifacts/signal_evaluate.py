import pandas as pd
import numpy as np
import json
import datetime as dt
import sys
sys.path.insert(0, "/data/user/013150/online_scripts/another_crontab_tasks")
from artifacts.dataload_utils import get_l2p_data
from artifacts.flying_functions import load_flying_factors
from artifacts.exp_artifacts import ExpArtifacts
from artifacts.parse_param import parse_target_type
from artifacts.utils import save_and_append_parquet,save_and_append_pickle
from xquant.xqutils.perf_profile import profile
from artifacts import exp_artifacts
from xquant.factordata import FactorData
import polars as pl
import copy
import time
import ray
import os
import pickle
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import pyplot as plt


def plot_winloss_table(symbol_name, win_limit, loss_limit, signal_evaluate_df_detail, pdf, weight_by_daynum=False,
                       verbose=1):
    tradingOrder_df_agg_list = []
    for pred in [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4]:
        tradingOrder_list = []
        for ridx, row in signal_evaluate_df_detail.iterrows():
            orders = row["orders"]
            orders = orders[(orders["pred"] >= pred) | (orders["pred"] <= -pred)]
            if len(orders[(orders["pred"] >= pred)]) == 0 or len(orders[(orders["pred"] <= -pred)]) == 0:
                continue
            tradingOrder = TradingEvaluate(orders)
            tradingOrder["symbol"] = row["symbol"]
            tradingOrder["date"] = row["date"]
            tradingOrder_list.append(tradingOrder)

        if len(tradingOrder_list) == 0:
            continue
        tradingOrder_df = pd.DataFrame(tradingOrder_list)
        if not weight_by_daynum:
            # 按天取平均
            tradingOrder_df["weight"] = 1 / tradingOrder_df["numAaverageDay"].count()
        else:
            # 按每天的开平仓次数加权
            tradingOrder_df["weight"] = tradingOrder_df["numAaverageDay"] / tradingOrder_df["numAaverageDay"].sum()

        column_type_dict = tradingOrder_df.dtypes.to_dict()
        result_agg_dict = {}
        for column in column_type_dict:
            if column in ["weight"]:
                continue
            if column in ["triggerTimes", "longTimes", "shortTimes", "winTimes"]:
                result_agg_dict[column] = tradingOrder_df[column].mean()
                continue
            if str(column_type_dict[column]).startswith("float") or str(column_type_dict[column]).startswith("int"):
                result_agg_dict[column] = (tradingOrder_df[column] * tradingOrder_df["weight"]).sum()
        result_agg_dict["pred"] = pred
        result_agg_dict['date_count'] = len(tradingOrder_df)
        tradingOrder_df_agg = pd.DataFrame([result_agg_dict])
        tradingOrder_df_agg_list.append(tradingOrder_df_agg)

    sdate = signal_evaluate_df_detail['date'].min()
    edate = signal_evaluate_df_detail['date'].max()
    result_df = pd.concat(tradingOrder_df_agg_list).round(5)
    result_df = result_df.rename(columns={
        'date_count': '有效天数',
        'pred': '预测阈值',
        'triggerTimes': '日均触发次数',
        'longTimes': '买入次数',
        'shortTimes': '卖出次数',
        'winTimes': '税后获胜次数',
        'winRate': '胜率',
        'averageRetTrigger': '平均回报',
        'averageRetWin': '获胜平均回报',
        'averageRetLoss': '亏损平均回报',
        'averageRetProfitLossRatio': '盈亏比',
        'maxLoss': '单日最大亏损',
        'averagePositionTime': '平均持仓时间',
        'win_mean': '止盈回报',
        'loss_mean': '止损回报',
        'reversal_mean': '反转信号回报',
        'timeout_mean': '超时回报',
        'loss_count': '止损占比',
        'reversal_count': '反转占比',
        'timeout_count': '超时占比',
        'win_count': '止盈占比',
    }).reindex(
        columns=['预测阈值', '有效天数', '日均触发次数', '买入次数', '卖出次数', '税后获胜次数', '胜率', '平均回报', '获胜平均回报', '亏损平均回报', '盈亏比', '单日最大亏损',
                 '平均持仓时间',
                 '止盈回报', '止损回报', '反转信号回报', '超时回报', '止盈占比', '止损占比', '反转占比', '超时占比'])
    if verbose > 0:
        print(result_df)
    if True:
        # 创建一个新的图表
        columns = result_df.columns
        fig, ax = plt.subplots(figsize=(len(columns) + 0.3, len(result_df) + 0.3))
        ax = plt.gca()
        ax.axis('off')  # 关闭坐标轴
        ax.text(0.2, 0.95,
                f"{'=' * 10} {symbol_name} {sdate} {edate} 止盈止损线 win{win_limit}，loss{loss_limit}（税后收益） {'=' * 10}  ",
                fontsize=20)

        table = ax.table(cellText=result_df.values, colLabels=result_df.columns, loc='center',
                         colWidths=[0.05] * len(result_df.columns),  # 为每列设置宽度
                         # cellPadding = [0.1]*len(result_df.columns),
                         cellLoc='left',
                         # fontsize=8, bbox=[0, 0, 1, 1]
                         fontsize=4)  # 设置字体大小
        # table.set(pad = 0.01)
        # plt.tight_layout(pad=0.1)
        table.auto_set_column_width(col=list(range(len(result_df.columns))))
        table.scale(xscale=1, yscale=2)

        pdf.savefig()
        plt.close()
        # plt.show()

        # 保存为 PDF 文件
        # plt.savefig('/home/appadmin/output.pdf', bbox_inches='tight')


def allSignalOrder(outSampleLongPredict, inSampleLongPredict, outSampleShortPredict, inSampleShortPredict, para,
                   subTag_df, verbose=0, return_th=False):
    """
    将开平仓信号转换为订单，平仓考虑三个条件：止盈、止损；持仓时间；和信号阈值反转,
    对所有预测值达到阈值的点进行评估（区别于signalOrder近对达到阈值的第一个点进行评估）
    用样本外的信号预测值Top分位数卡信号，确保每日评价的信号个数大致相近
    :param outSampleLongPredict:
    :param inSampleLongPredict:
    :param outSampleShortPredict:
    :param inSampleShortPredict:
    :param para:
    :param subTag_df:
    :param verbose:
    :return:
    """
    assert len(outSampleLongPredict) == len(
        outSampleShortPredict), "outSampleShortPredict和outSampleLongPredict的信号个数应保持一致！ {} vs {}".format(
        len(outSampleLongPredict), len(outSampleShortPredict), )
    target_type = para["target_type"]
    if target_type == "mid":
        up_start_price_col = "TARGET_VALUE"
        up_end_price_col = "TARGET_VALUE"
        dw_start_price_col = "TARGET_VALUE"
        dw_end_price_col = "TARGET_VALUE"
        price_deviation = 0.01  # 价差，抢单成本
        print("up_start_price_col: {}, up_end_price_col: {}, price_deviation: {}".format(up_start_price_col,
                                                                                         up_end_price_col,
                                                                                         price_deviation))
    elif target_type == "longshort":
        up_start_price_col = "TARGET_VALUE"
        up_end_price_col = "TARGET_VALUE"
        dw_start_price_col = "TARGET_VALUE"
        dw_end_price_col = "TARGET_VALUE"
        price_deviation = 0.01  # 价差，抢单成本
        print("up_start_price_col: {}, up_end_price_col: {}, price_deviation: {}".format(up_start_price_col,
                                                                                         up_end_price_col,
                                                                                         price_deviation))
        # up_start_price_col = "Ask1P"
        # up_end_price_col = "Bid1P"
        # dw_start_price_col = "Bid1P"
        # dw_end_price_col = "Ask1P"
        # price_deviation = 0.0 #价差，抢单成本
        # print("up_start_price_col: {}, up_end_price_col: {}, price_deviation: {}".format(up_start_price_col, up_end_price_col, price_deviation))
    else:
        raise Exception("计算止盈止损收益率的价格类型ret_type仅支持mid, longshort!")
    orders = []
    # 找到每一列的位置
    columns = subTag_df.columns.tolist()
    idx_up_start_price_col = columns.index(up_start_price_col)
    idx_up_end_price_col = columns.index(up_end_price_col)
    idx_dw_start_price_col = columns.index(dw_start_price_col)
    idx_dw_end_price_col = columns.index(dw_end_price_col)
    idx_start_timestamp = columns.index('startTimeStamp')
    idx_code = columns.index('code')
    idx_bid1p = columns.index('Bid1P')
    idx_ask1p = columns.index('Ask1P')
    subTag_array = subTag_df.values

    #########################需要根据样本外的重算信号阈值（保证信号个数接近）##########################
    try:
        longTriggerRatio = max(
            [para["longMinTriggerRatio"], np.percentile(inSampleLongPredict, para["longTriggerRatioPercentile"])])
        shortTriggerRatio = min(
            [para["shortMinTriggerRatio"], np.percentile(inSampleShortPredict, para["shortTriggerRatioPercentile"])])
        print("longTriggerRatio: {}, shortTriggerRatio: {} ".format(longTriggerRatio, shortTriggerRatio))
    except Exception as e:
        print(e, inSampleLongPredict)
        longTriggerRatio = para["longMinTriggerRatio"]
        shortTriggerRatio = para["shortMinTriggerRatio"]

    sample_k = 0
    # 有有效信号时，一直往后看，直到以下条件满足：信号反向、或者信号达到止损、或者到达预测时间
    while sample_k < len(outSampleLongPredict) - 1:
        k = sample_k
        if outSampleLongPredict[k] >= longTriggerRatio:
            pred_up = outSampleLongPredict[k]
            while k < len(outSampleLongPredict) - 1:
                row = subTag_array[k]
                if row[idx_ask1p] == 0:
                    # 跌停不买
                    k += 1
                    continue

                tempOrder = {
                    "code": row[idx_code],
                    "direction": "long",
                    "startTime": dt.datetime.fromtimestamp(row[idx_start_timestamp]).strftime("%Y-%m-%d %H:%M:%S"),
                    "startPrice": round(row[idx_up_start_price_col], 3) + price_deviation
                }

                if subTag_array[k + 1][idx_start_timestamp] - row[idx_start_timestamp] > 3600:
                    # 跨天
                    k += 1
                    continue

                k += 1
                while k < len(outSampleShortPredict) - 1:
                    # 判断终止条件：信号反向、或者信号达到止损、或者到达预测时间
                    next_row = subTag_array[k]
                    if outSampleShortPredict[k] <= shortTriggerRatio:
                        tempOrder.update({"type": "reversal"})  # 趋势反转
                        if verbose > 10:
                            print(f'''k: {k}, ret: {next_row[idx_up_end_price_col] / tempOrder[
                                "startPrice"] - 1}, predict_k: {
                            outSampleShortPredict[k]}, endprice_k {next_row[idx_up_end_price_col]}, startprice {
                            tempOrder[
                                "startPrice"]}''')
                        break
                    if next_row[idx_start_timestamp] - row[idx_start_timestamp] > 120:
                        tempOrder.update({"type": "timeout"})  # 趋势反转
                        if verbose > 10:
                            print(f'''k: {k}, ret: {next_row[idx_up_end_price_col] / tempOrder[
                                "startPrice"] - 1}, predict_k: {
                            outSampleShortPredict[k]}, endprice_k {next_row[idx_up_end_price_col]}, startprice {
                            tempOrder[
                                "startPrice"]}''')
                        break
                    if next_row[idx_up_end_price_col] / tempOrder["startPrice"] - 1 < para["lossLimit"]:
                        tempOrder.update({"type": "loss"})  # 止损
                        if verbose > 10:
                            print(f'''k: {k}, ret: {next_row[idx_up_end_price_col] / tempOrder[
                                "startPrice"] - 1}, predict_k: {
                            outSampleShortPredict[k]}, endprice_k {next_row[idx_up_end_price_col]}, startprice {
                            tempOrder[
                                "startPrice"]}''')
                        break
                    if next_row[idx_up_end_price_col] / tempOrder["startPrice"] - 1 > para["winLimit"]:
                        tempOrder.update({"type": "win"})  # 止盈
                        if verbose > 10:
                            print(f'''k: {k}, ret: {next_row[idx_up_end_price_col] / tempOrder[
                                "startPrice"] - 1}, predict_k: {
                            outSampleShortPredict[k]}, endprice_k {next_row[idx_up_end_price_col]}, startprice {
                            tempOrder[
                                "startPrice"]}''')
                        break
                    k += 1

                end_row = subTag_array[k]
                tempOrder.update({
                    "endTime": dt.datetime.fromtimestamp(end_row[idx_start_timestamp]).strftime("%Y-%m-%d %H:%M:%S"),
                    #                 # 以bidprice判断止损，以askprice判断收益
                    #                 "endPrice": round(subTag_df.iloc[k]["askPrice"][0] - 0.01 if subTag_df.iloc[k]["askPrice"][0] != 0 else subTag_df.iloc[k]["bidPrice"][0], 3),
                    #                 "endPrice": round(end_row[up_start_price_col] - 0.01 if end_row[up_end_price_col] == 0 else end_row[up_end_price_col], 3),
                    "endPrice": round(
                        end_row[idx_up_end_price_col] - price_deviation if end_row[idx_up_end_price_col] != 0 else
                        end_row[idx_up_start_price_col],
                        3),
                })
                if tempOrder["endPrice"] == 0.0:
                    tempOrder["returnRate"] = 0.0
                else:
                    tempOrder["returnRate"] = round(tempOrder["endPrice"] / tempOrder["startPrice"] - 1, 5)
                tempOrder["pred"] = pred_up
                orders.append(tempOrder)
                sample_k += 1
                break
        elif outSampleShortPredict[k] <= shortTriggerRatio:
            pred_dw = outSampleLongPredict[k]
            while k < len(outSampleLongPredict) - 1:
                row = subTag_array[k]
                if row[idx_bid1p] == 0:
                    # 涨停不卖
                    k += 1
                    continue

                tempOrder = {
                    "code": row[idx_code],
                    "direction": "short",
                    "startTime": dt.datetime.fromtimestamp(row[idx_start_timestamp]).strftime("%Y-%m-%d %H:%M:%S"),
                    "startPrice": round(row[idx_dw_start_price_col], 3) - price_deviation
                }
                ##################断点调试####################
                if tempOrder["startTime"] == "2024-05-06 13:00:10":
                    a = 1
                ######################################

                if subTag_array[k + 1][idx_start_timestamp] - row[idx_start_timestamp] > 3600:
                    # 跨天信号不判断
                    k += 1
                    continue

                k += 1
                while k < len(outSampleLongPredict) - 1:
                    next_row = subTag_array[k]
                    if outSampleLongPredict[k] >= longTriggerRatio:
                        tempOrder.update({"type": "reversal"})  # 趋势反转
                        if verbose > 10:
                            print(f'''k: {k}, ret: {1 - next_row[idx_dw_end_price_col] / tempOrder[
                                "startPrice"]}, predict_k: {
                            outSampleLongPredict[k]}, endprice_k {next_row[idx_dw_end_price_col]}, startprice {
                            tempOrder[
                                "startPrice"]}''')
                        break
                    if 1 - next_row[idx_dw_end_price_col] / tempOrder["startPrice"] < para["lossLimit"]:
                        tempOrder.update({"type": "loss"})  # 止损
                        if verbose > 10:
                            print(f'''k: {k}, ret: {1 - next_row[idx_dw_end_price_col] / tempOrder[
                                "startPrice"]}, predict_k: {
                            outSampleLongPredict[k]}, endprice_k {next_row[idx_dw_end_price_col]}, startprice {
                            tempOrder[
                                "startPrice"]}''')
                        break
                    if 1 - next_row[idx_dw_end_price_col] / tempOrder["startPrice"] > para["winLimit"]:
                        tempOrder.update({"type": "win"})  # 止盈
                        if verbose > 10:
                            print(f'''k: {k}, ret: {1 - next_row[idx_dw_end_price_col] / tempOrder[
                                "startPrice"]}, predict_k: {
                            outSampleLongPredict[k]}, endprice_k {next_row[idx_dw_end_price_col]}, startprice {
                            tempOrder[
                                "startPrice"]}''')
                        break
                    if next_row[idx_start_timestamp] - row[idx_start_timestamp] > 120:
                        tempOrder.update({"type": "timeout"})  # 趋势反转
                        break
                    k += 1

                end_row = subTag_array[k]
                tempOrder.update({
                    "endTime": dt.datetime.fromtimestamp(subTag_array[k][idx_start_timestamp]).strftime(
                        "%Y-%m-%d %H:%M:%S"),
                    #               "endPrice": round(subTag_df.iloc[k]["bidPrice"][0] + 0.01 if subTag_df.iloc[k]["bidPrice"][0] != 0 else subTag_df.iloc[k]["askPrice"][0], 3),
                    #               "endPrice": round(end_row[dw_start_price_col] + 0.01 if end_row[dw_end_price_col] == 0 else end_row[dw_end_price_col], 3),
                    "endPrice": round(
                        end_row[idx_dw_end_price_col] + price_deviation if end_row[idx_dw_end_price_col] != 0 else
                        end_row[idx_dw_start_price_col], 3),
                })
                if tempOrder["endPrice"] == 0.0:
                    tempOrder["returnRate"] = 0.0
                else:
                    tempOrder["returnRate"] = round(1 - tempOrder["endPrice"] / tempOrder["startPrice"], 5)
                tempOrder["pred"] = pred_dw
                orders.append(tempOrder)
                sample_k += 1
                break
        else:
            sample_k += 1

    orders_df = pd.DataFrame(orders)
    # if verbose>0:
    #     print(orders_df)
    if not return_th:
        return orders_df
    else:
        return orders_df, longTriggerRatio, shortTriggerRatio


def firstSignalOrder(outSampleLongPredict, inSampleLongPredict, outSampleShortPredict, inSampleShortPredict, para,
                     subTag_df,
                     verbose=0, return_th=False):
    """
    将开平仓信号转换为订单，平仓考虑三个条件：止盈、止损；持仓时间；和信号阈值反转；
    只考虑第一个信号点，目的是弱化信号个数，侧重信号的反向能力，逻辑如下：如果开仓信号为Long，一段区间内连续的Long信号只有第一个信号转换为订单，对第一个信号生成的订单，按平仓条件计算平仓时间和平仓收益
    用样本外的信号预测值Top分位数卡信号，确保每日评价的信号个数大致相近
    :param outSampleLongPredict:
    :param inSampleLongPredict:
    :param outSampleShortPredict:
    :param inSampleShortPredict:
    :param para:
    :param subTag_df:
    :param verbose:
    :return:
    """
    assert len(outSampleLongPredict) == len(
        outSampleShortPredict), "outSampleShortPredict和outSampleLongPredict的信号个数应保持一致！ {} vs {}".format(
        len(outSampleLongPredict), len(outSampleShortPredict), )
    target_type = para["target_type"]
    if target_type == "mid":
        up_start_price_col = "TARGET_VALUE"
        up_end_price_col = "TARGET_VALUE"
        dw_start_price_col = "TARGET_VALUE"
        dw_end_price_col = "TARGET_VALUE"
        price_deviation = 0.01  # 价差，抢单成本
    elif target_type == "longshort":
        up_start_price_col = "Ask1P"
        up_end_price_col = "Bid1P"
        dw_start_price_col = "Bid1P"
        dw_end_price_col = "Ask1P"
        price_deviation = 0.0  # 价差，抢单成本
    else:
        raise Exception("计算止盈止损收益率的价格类型ret_type仅支持mid, longshort!")
    orders = []
    # 找到每一列的位置
    columns = subTag_df.columns.tolist()
    idx_up_start_price_col = columns.index(up_start_price_col)
    idx_up_end_price_col = columns.index(up_end_price_col)
    idx_dw_start_price_col = columns.index(dw_start_price_col)
    idx_dw_end_price_col = columns.index(dw_end_price_col)
    idx_start_timestamp = columns.index('startTimeStamp')
    idx_code = columns.index('code')
    idx_bid1p = columns.index('Bid1P')
    idx_ask1p = columns.index('Ask1P')
    subTag_array = subTag_df.values  # 单天计算性能提升一个数量级

    #########################需要根据样本外的重算信号阈值（保证信号个数接近）##########################
    longTriggerRatio = max(
        [para["longMinTriggerRatio"], np.percentile(inSampleLongPredict, para["longTriggerRatioPercentile"])])
    shortTriggerRatio = min(
        [para["shortMinTriggerRatio"], np.percentile(inSampleShortPredict, para["shortTriggerRatioPercentile"])])
    print("longTriggerRatio: {}, shortTriggerRatio: {} ".format(longTriggerRatio, shortTriggerRatio))

    k = 0
    # 有有效信号时，一直往后看，直到以下条件满足：信号反向、或者信号达到止损、或者到达预测时间
    while k < len(outSampleLongPredict) - 1:
        pred = outSampleLongPredict[k]
        if outSampleLongPredict[k] >= longTriggerRatio:
            row = subTag_array[k]
            if row[idx_ask1p] == 0:
                # 跌停不买
                k += 1
                continue

            tempOrder = {
                "code": row[idx_code],
                "direction": "long",
                "startTime": dt.datetime.fromtimestamp(row[idx_start_timestamp]).strftime("%Y-%m-%d %H:%M:%S"),
                "startPrice": round(row[idx_up_start_price_col], 3) + price_deviation
            }

            if subTag_array[k + 1][idx_start_timestamp] - row[idx_start_timestamp] > 3600:
                # 跨天
                k += 1
                continue

            k += 1
            while k < len(outSampleShortPredict) - 1:
                # 判断终止条件：信号反向、或者信号达到止损、或者到达预测时间
                next_row = subTag_array[k]
                if outSampleShortPredict[k] <= shortTriggerRatio:
                    tempOrder.update({"type": "reversal"})  # 趋势反转
                    if verbose > 10:
                        print(f'''k: {k}, ret: {next_row[idx_up_end_price_col] / tempOrder[
                            "startPrice"] - 1}, predict_k: {
                        outSampleShortPredict[k]}, endprice_k {next_row[idx_up_end_price_col]}, startprice {tempOrder[
                            "startPrice"]}''')
                    break
                if next_row[idx_start_timestamp] - row[idx_start_timestamp] > 120:
                    tempOrder.update({"type": "timeout"})  # 趋势反转
                    if verbose > 10:
                        print(f'''k: {k}, ret: {next_row[idx_up_end_price_col] / tempOrder[
                            "startPrice"] - 1}, predict_k: {
                        outSampleShortPredict[k]}, endprice_k {next_row[idx_up_end_price_col]}, startprice {tempOrder[
                            "startPrice"]}''')
                    break
                if next_row[idx_up_end_price_col] / tempOrder["startPrice"] - 1 < para["lossLimit"]:
                    tempOrder.update({"type": "loss"})  # 止损
                    if verbose > 10:
                        print(f'''k: {k}, ret: {next_row[idx_up_end_price_col] / tempOrder[
                            "startPrice"] - 1}, predict_k: {
                        outSampleShortPredict[k]}, endprice_k {next_row[idx_up_end_price_col]}, startprice {tempOrder[
                            "startPrice"]}''')
                    break
                if next_row[idx_up_end_price_col] / tempOrder["startPrice"] - 1 > para["winLimit"]:
                    tempOrder.update({"type": "win"})  # 止盈
                    if verbose > 10:
                        print(f'''k: {k}, ret: {next_row[idx_up_end_price_col] / tempOrder[
                            "startPrice"] - 1}, predict_k: {
                        outSampleShortPredict[k]}, endprice_k {next_row[idx_up_end_price_col]}, startprice {tempOrder[
                            "startPrice"]}''')
                    break
                k += 1

            end_row = subTag_array[k]
            tempOrder.update({
                "endTime": dt.datetime.fromtimestamp(end_row[idx_start_timestamp]).strftime("%Y-%m-%d %H:%M:%S"),
                #                 # 以bidprice判断止损，以askprice判断收益
                #                 "endPrice": round(subTag_df.iloc[k]["askPrice"][0] - 0.01 if subTag_df.iloc[k]["askPrice"][0] != 0 else subTag_df.iloc[k]["bidPrice"][0], 3),
                #                 "endPrice": round(end_row[up_start_price_col] - 0.01 if end_row[up_end_price_col] == 0 else end_row[up_end_price_col], 3),
                "endPrice": round(
                    end_row[idx_up_end_price_col] - price_deviation if end_row[idx_up_end_price_col] != 0 else end_row[
                        idx_up_start_price_col],
                    3),
            })
            tempOrder["returnRate"] = round(tempOrder["endPrice"] / tempOrder["startPrice"] - 1, 5)
            tempOrder["pred"] = pred
            orders.append(tempOrder)
        elif outSampleShortPredict[k] <= shortTriggerRatio:
            row = subTag_array[k]
            if row[idx_bid1p] == 0:
                # 涨停不卖
                k += 1
                continue

            tempOrder = {
                "code": row[idx_code],
                "direction": "short",
                "startTime": dt.datetime.fromtimestamp(row[idx_start_timestamp]).strftime("%Y-%m-%d %H:%M:%S"),
                "startPrice": round(row[idx_dw_start_price_col], 3) - price_deviation
            }
            ##################断点调试####################
            if tempOrder["startTime"] == "2024-05-06 13:00:10":
                a = 1
            ######################################

            if subTag_array[k + 1][idx_start_timestamp] - row[idx_start_timestamp] > 3600:
                # 跨天信号不判断
                k += 1
                continue

            k += 1
            while k < len(outSampleLongPredict) - 1:
                next_row = subTag_array[k]
                if outSampleLongPredict[k] >= longTriggerRatio:
                    tempOrder.update({"type": "reversal"})  # 趋势反转
                    if verbose > 10:
                        print(f'''k: {k}, ret: {1 - next_row[idx_dw_end_price_col] / tempOrder[
                            "startPrice"]}, predict_k: {
                        outSampleLongPredict[k]}, endprice_k {next_row[idx_dw_end_price_col]}, startprice {tempOrder[
                            "startPrice"]}''')
                    break
                if 1 - next_row[idx_dw_end_price_col] / tempOrder["startPrice"] < para["lossLimit"]:
                    tempOrder.update({"type": "loss"})  # 止损
                    if verbose > 10:
                        print(f'''k: {k}, ret: {1 - next_row[idx_dw_end_price_col] / tempOrder[
                            "startPrice"]}, predict_k: {
                        outSampleLongPredict[k]}, endprice_k {next_row[idx_dw_end_price_col]}, startprice {tempOrder[
                            "startPrice"]}''')
                    break
                if 1 - next_row[idx_dw_end_price_col] / tempOrder["startPrice"] > para["winLimit"]:
                    tempOrder.update({"type": "win"})  # 止盈
                    if verbose > 10:
                        print(f'''k: {k}, ret: {1 - next_row[idx_dw_end_price_col] / tempOrder[
                            "startPrice"]}, predict_k: {
                        outSampleLongPredict[k]}, endprice_k {next_row[idx_dw_end_price_col]}, startprice {tempOrder[
                            "startPrice"]}''')
                    break
                if next_row[idx_start_timestamp] - row[idx_start_timestamp] > 120:
                    tempOrder.update({"type": "timeout"})  # 趋势反转
                    break
                k += 1

            end_row = subTag_array[k]
            tempOrder.update({
                "endTime": dt.datetime.fromtimestamp(subTag_array[k][idx_start_timestamp]).strftime(
                    "%Y-%m-%d %H:%M:%S"),
                #               "endPrice": round(subTag_df.iloc[k]["bidPrice"][0] + 0.01 if subTag_df.iloc[k]["bidPrice"][0] != 0 else subTag_df.iloc[k]["askPrice"][0], 3),
                #               "endPrice": round(end_row[dw_start_price_col] + 0.01 if end_row[dw_end_price_col] == 0 else end_row[dw_end_price_col], 3),
                "endPrice": round(
                    end_row[idx_dw_end_price_col] + price_deviation if end_row[idx_dw_end_price_col] != 0 else end_row[
                        idx_dw_start_price_col], 3),
            })
            tempOrder["returnRate"] = round(1 - tempOrder["endPrice"] / tempOrder["startPrice"], 5)
            tempOrder["pred"] = pred
            orders.append(tempOrder)
        else:
            k += 1

    orders_df = pd.DataFrame(orders)
    # if verbose>0:
    #     print(orders_df)
    if not return_th:
        return orders_df
    else:
        return orders_df, longTriggerRatio, shortTriggerRatio


def TradingEvaluate(orders_df, longTriggerRatio=None, shortTriggerRatio=None, verbose=0):
    TradingOrder = {}
    longTriggerRatio = orders_df[orders_df["pred"] > 0]["pred"].min() if not longTriggerRatio else longTriggerRatio
    shortTriggerRatio = orders_df[orders_df["pred"] < 0]["pred"].max() if not shortTriggerRatio else shortTriggerRatio
    TradingOrder.update({"predUp": longTriggerRatio})
    TradingOrder.update({"predDw": shortTriggerRatio})
    TradingOrder.update({"orders": orders_df})

    threshold = 0.0005  # 盈利阈值
    triggerTimes = len(TradingOrder["orders"])  # 触发次数
    winTimes = 0  # 获利次数
    winRate = 0  # 胜率
    numAaverageDay = 0  # 日均开仓次数
    longTimes = 0  # 开多仓次数
    shortTimes = 0  # 开空仓次数
    averageReturnRate = 0  # 平均收益率
    averageReturnRateWin = 0  # 平均获利收益率
    averageReturnRateLoss = 0  # 平均亏损收益率
    profitLossRatio = 0  # 盈亏比
    maxLoss = 0  # 最大亏损
    averagePositionTime = 0  # 平均持仓时间
    if triggerTimes != 0:
        winRate = winTimes / triggerTimes
        dates = list(
            sorted(set(TradingOrder["orders"]["startTime"].apply(lambda x: pd.to_datetime(x).strftime("%Y%m%d")))))
        numAaverageDay = triggerTimes / len(dates)
        TradingOrder.update({"start_date": dates[0]})
        TradingOrder.update({"end_date": dates[-1]})
    if triggerTimes > 0:
        for oidx, order in TradingOrder["orders"].iterrows():
            # 计算持仓时间(min)
            startTime = dt.datetime.strptime(order["startTime"], "%Y-%m-%d %H:%M:%S")
            endTime = dt.datetime.strptime(order["endTime"], "%Y-%m-%d %H:%M:%S")
            if startTime.hour <= 11 and endTime.hour >= 13:
                averagePositionTime += (endTime - startTime).seconds - 90 * 60
            else:
                averagePositionTime += (endTime - startTime).seconds
                # 计算开多和开空次数
            if order["direction"] == 'long':
                longTimes += 1
            else:
                shortTimes += 1
            # 计算收益率相关值
            averageReturnRate += order["returnRate"] - threshold
            if order["returnRate"] > threshold:
                winTimes += 1
                averageReturnRateWin += order["returnRate"] - threshold
            else:
                averageReturnRateLoss += order["returnRate"] - threshold
                if order["returnRate"] < maxLoss:
                    maxLoss = order["returnRate"]  # 后面扣税
        averagePositionTime /= triggerTimes
        winRate = winTimes / triggerTimes
        averageReturnRate /= triggerTimes
        if winTimes > 0:
            averageReturnRateWin /= winTimes
        if triggerTimes > winTimes:
            averageReturnRateLoss /= (triggerTimes - winTimes)
            profitLossRatio = averageReturnRateWin / abs(averageReturnRateLoss) if averageReturnRateLoss != 0 else 0.0
    TradingOrder.update({"triggerTimes": triggerTimes})
    TradingOrder.update({"numAaverageDay": numAaverageDay})
    TradingOrder.update({"winTimes": winTimes})
    TradingOrder.update({"winRate": winRate})
    TradingOrder.update({"longTimes": longTimes})
    TradingOrder.update({"shortTimes": shortTimes})
    TradingOrder.update({"averageRetTrigger": averageReturnRate})
    TradingOrder.update({"averageRetWin": averageReturnRateWin})
    TradingOrder.update({"averageRetLoss": averageReturnRateLoss})
    TradingOrder.update({"averageRetProfitLossRatio": profitLossRatio})
    TradingOrder.update({"maxLoss": maxLoss - threshold})
    TradingOrder.update({"averagePositionTime": averagePositionTime})
    try:
        df1 = TradingOrder["orders"].groupby("type").agg({"returnRate": ["mean"]}).T.reset_index(drop=True)
    except:
        print(TradingOrder["orders"])
        raise Exception()
    df1.columns = [i + "_mean" for i in df1.columns]
    df2 = TradingOrder["orders"].groupby("type").agg({"returnRate": ["count"]}).T.reset_index(drop=True)
    df2.columns = [i + "_count" for i in df2.columns]
    for col in df1.columns:
        TradingOrder[col] = df1[col][0]
    for col in df2.columns:
        TradingOrder[col] = df2[col][0] / df2.sum(axis=1)[0]
    # from pprint import pprint
    # if verbose>0:
    #     a = copy.deepcopy(TradingOrder)
    #     a.pop("orders")
    #     pprint(a)
    return TradingOrder


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
    l2p_df = get_l2p_data(symbol_name, insample_start_date, end_date.replace("-", "")).select(
        ["DateTime", "M_SellPrice", "M_BuyPrice", "Bid1P", "Ask1P", "M_OpenPx"])
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
        # tradingOrder_df.to_pickle(debug_path)
        save_and_append_pickle(tradingOrder_df, debug_path, overwrite_col="date")

    tradingOrder_df_agg = pd.DataFrame([result_agg_dict])

    return tradingOrder_df_agg

@ray.remote(max_calls=5)
def grid_evaluate_remote(symbol_name, long_source_signal_df, short_source_signal_df, sig_para, signal_name, start_date,
                  end_date, base_dir="./", verbose=0, first_point=True):
    return grid_evaluate(symbol_name, long_source_signal_df, short_source_signal_df, sig_para, signal_name, start_date,
                  end_date, base_dir=base_dir, verbose=verbose, first_point=first_point)


def grid_evaluate(symbol_name, long_source_signal_df, short_source_signal_df, sig_para, signal_name, start_date,
                  end_date, base_dir="./", verbose=0, first_point=True):
    """
    :param symbol_name:
    :param long_source_signal_df:
    :param short_source_signal_df:
    :param sig_para:
    :param signal_name: 信号名称标记，一般是版本名
    :return:
    """
    tasks = []
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
                task = SignalEvaluateRemote.remote(symbol_name, long_source_signal_df, short_source_signal_df, tmp_para,
                                                   start_date, end_date, verbose=verbose, signal_name=signal_name,
                                                   base_dir=base_dir, first_point=first_point)
                # print(result)
                tasks.append(task)
    result_list = ray.get(tasks)
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
            expa = exp_artifacts.ExpArtifacts(exp_name=exp_name)
            tasks = []
            for symbol_name in symbol_list:
                t1 = time.time()
                try:
                    signal_file = f"/dfs/group/800657/exp_results/{exp_name}/{version_alias}/signal_files/{label_name}-{symbol_name}.parquet"
                    if not os.path.exists(signal_file):
                        print("model_signal_load error: no such file: ", signal_file)
                        continue
                    source_signal_df = pd.read_parquet(signal_file)

                    if len(source_signal_df) == 0:
                        raise Exception("{} {}数据为空！".format(start_date, end_date))
                    if flying_adjust:
                        fa = FactorData()
                        dates = fa.tradingday(start_date.replace("-", ""),  end_date.replace("-", ""))
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
                        print(source_signal_df)
                        source_signal_df["open_flying_deriction"] = source_signal_df.merge(
                            edf_resample, left_on = "DateTime", right_on = "DateTime", how = "left")["open_flying_direction"].values
                        print(source_signal_df["open_flying_deriction"].values)
                        source_signal_df["PREDICT"] = source_signal_df.apply(lambda x: x['PREDICT'] if x["PREDICT"] * x["open_flying_deriction"]>=0 else 0, axis = 1)
                        source_signal_df["PREDICTED"] = source_signal_df.apply(lambda x: x['PREDICTED'] if x["PREDICTED"] * x["open_flying_deriction"]>=0 else 0, axis = 1)

                    grid_evaluate(symbol_name, source_signal_df, source_signal_df, para, start_date=start_date,
                              end_date=end_date, signal_name=exp_name + "-" + version_alias, base_dir=base_dir1,
                              verbose=verbose, first_point=first_point)
                    print("耗时：", time.time() - t1)
                except Exception as e:
                    print("model_signal_load error: ", e)

    else:
        t1 = time.time()
        for label_name, exp_name, version_alias in [
            # ("LabelLongOneMin", "exp_l3_zzkc_flying4", 'LabelLongOneMin_factor98_amp_sample'),
            # ("LabelLongTwoMin", "exp_l3_zzkc_flying4", 'LabelLongTwoMin_factor98_amp_sample')
            # #######################20240705##################
            # ("vwap01_long_ret_60s", "exp_l3_zzkc_flying4", 'vwap01_long_ret_60s_factor98_sample_log2'),  # 对样本进行采样
            # ("smooth_long_ret_60s", "exp_l3_zzkc_flying4", 'smooth_long_ret_60s_factor98_sample_log2'),
            # ("dol_long_ret_60s", "exp_l3_zzkc_flying4", 'dol_long_ret_60s_factor98_sample_log2'),
            # #######################20240710##################
            # ("vwap01_long_ret_60s", "exp_l3_zzkc_flying4", 'vwap01_long_ret_60s_factor98_sample_trim'),#截取0.5以下的标签
            ("smooth_long_ret_60s", "exp_l3_zzkc_flying4", 'smooth_long_ret_60s_factor98_sample_trim'),
            # ("dol_long_ret_60s", "exp_l3_zzkc_flying4", 'dol_long_ret_60s_factor98_sample_trim'),
        ]:
            for symbol_name in symbol_list:
                base_dir1 = os.path.join(base_dir, version_alias)
                os.makedirs(base_dir1, exist_ok=True)

                long_signal_file = f"/dfs/group/800657/exp_results/{exp_name}/{version_alias}/signal_files/{label_name}-{symbol_name}.parquet"
                long_source_signal_df = pd.read_parquet(long_signal_file)
                # long_source_signal_df = long_source_signal_df[
                #     (long_source_signal_df["DATE"] >= start_date) & (long_source_signal_df["DATE"] <= end_date)]
                if "l3" in exp_name:
                    long_source_signal_df["PREDICT"] = long_source_signal_df["PREDICT"] * long_source_signal_df[
                        "flying_flag"]
                    long_source_signal_df["PREDICTED"] = long_source_signal_df["PREDICTED"] * long_source_signal_df[
                        "flying_flag"]

                version_alias_short = version_alias.replace("Long", "Short")
                label_name_short = label_name.replace("Long", "Short")
                short_signal_file = f"/dfs/group/800657/exp_results/{exp_name}/{version_alias_short}/signal_files/{label_name_short}-{symbol_name}.parquet"
                short_source_signal_df = pd.read_parquet(short_signal_file)
                # short_source_signal_df = short_source_signal_df[
                #     (short_source_signal_df["DATE"] >= start_date) & (short_source_signal_df["DATE"] <= end_date)]

                if len(short_source_signal_df) == 0 or len(long_source_signal_df) == 0:
                    raise Exception("{} {}数据为空！".format(start_date, end_date))
                if "l3" in exp_name:
                    short_source_signal_df["PREDICT"] = short_source_signal_df["PREDICT"] * \
                                                        short_source_signal_df["flying_flag"]
                    short_source_signal_df["PREDICTED"] = short_source_signal_df["PREDICTED"] * \
                                                          short_source_signal_df["flying_flag"]

                grid_evaluate(symbol_name, long_source_signal_df, short_source_signal_df, para, start_date=start_date,
                              end_date=end_date, signal_name=exp_name + "-" + version_alias,
                              base_dir=base_dir1, verbose=verbose, first_point=first_point)
                print("耗时：", time.time() - t1)

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
            # ("LabelFirstPeak_th10_120s", "l2p_kc_basket", "l2p_kc_basket"),
            # ("LabelFirstPeak_th10_120s", "l2p_kc2_log", "l2p_kc2_log"),
            # ("LabelFirstPeak_th10_120s", "l2p_688981.SH_v1.1", "l2p_688981.SH_v1.1"),
            # ("LabelFirstPeak_th10_120s", "l2p_688111.SH_v1.1", "l2p_688111.SH_v1.1"),
            # ("LabelFirstPeak_th10_120s", "l2p_kc100_v1", "l2p_kc100_v1"),
            # ("LabelFirstPeak_th10_120s", "unite_kc", "unite_kc"),
            # ("LabelFirstPeak_th10_120s", "tick_kc_basket", "tick_kc_basket"),
            ("LabelFirstPeak_th10_120s", "tick_688017.SH", "tick_688017.SH"),
            ("LabelFirstPeak_th10_120s", "l2p_688036.SH", "l2p_688036.SH"),
            # ("LabelFirstPeak_th10_120s", "l2p_HS800_high", "l2p_HS800_high"),
            # ("LabelFirstPeak_th10_120s", "l2p_HS800_low", "l2p_HS800_low"),
            # L3
            ("LabelFirstPeak_th12_60s", "l3_zzkc_flying4_log2", 'l3_zzkc_flying4_log2'),
            ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4_levelone", 'LabelFirstPeak_th12_60s_factor98_levelone_log2'),
            ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_zzkc_flying4_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_levelone_log2'),
            ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_log2'),
            # #################################################################################
            # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98'),
            # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_amp'),#事件用幅度代替0、1值
            # ("LabelFirstPeak_th12_60s", "exp_l3_kc_flying4", 'LabelFirstPeak_th12_60s_factor98_lowpca'),
            # ("LabelFirstPeak_th12_60s", "exp_l3_kc_flying4", 'LabelFirstPeak_th12_60s_factor98_highpca'),
            # # #######################20240626###################
            # ("LabelFirstPeak_th05_120s", "exp_l3_kc_flying4", 'LabelFirstPeak_th05_120s_factor98_lowpca'),
            # ("LabelFirstPeak_th05_120s", "exp_l3_kc_flying4", 'LabelFirstPeak_th05_120s_factor98_highpca'),
            # #######################20240626###################
            # ("LabelFirstPeak_th10_60s", "exp_l3_kc_flying4",'LabelFirstPeak_th10_60s_factor98_lowpca'),
            # ("LabelFirstPeak_th10_60s", "exp_l3_kc_flying4",'LabelFirstPeak_th10_60s_factor98_highpca')
            # #######################20240627###################
            #("LabelFirstPeak_th10_60s", "KC_LabelFirstPeak_th10_60s_log", 'KC_LabelFirstPeak_th10_60s_log'),
            # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_log2'),  # 对数底为2
            # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_amp_log2'),  # 对数底为2
            # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_huber0.5'),  # huber损失函数
            # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_log2_huber1')
            # #######################20240715##################
            ##################20240716##################
            # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4_levelone", 'LabelFirstPeak_th12_60s_factor98_levelone_log2'),
            # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4_levelone", 'LabelFirstPeak_th12_60s_factor98_levelone_amp_log2'),
            # ("LabelFirstPeak_th10_120s", "l2p_kc_basket", "l2p_kc_basket"),
            # ("LabelFirstPeak_th10_120s", "l2p_kc2_log", "l2p_kc2_log"),
            # ("LabelFirstPeak_th10_120s", "l2p_688981.SH_v1.1", "l2p_688981.SH_v1.1"),
            # ("LabelFirstPeak_th10_120s", "l2p_688111.SH_v1.1", "l2p_688111.SH_v1.1"),
            # ("LabelFirstPeak_th10_120s", "l2p_kc100_v1", "l2p_kc100_v1"),
            # ("LabelFirstPeak_th10_120s", "unite_kc", "unite_kc"),
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

