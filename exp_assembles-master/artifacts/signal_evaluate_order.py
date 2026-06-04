import pandas as pd
import numpy as np
import datetime as dt


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
                    # 涨停不买
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
                    if next_row[idx_up_end_price_col] / tempOrder["startPrice"] - 1 < para["lossLimit"] and \
                        abs(round(next_row[idx_up_end_price_col],2) - round(tempOrder["startPrice"],2)) > price_deviation:
                        tempOrder.update({"type": "loss"})  # 止损
                        if verbose > 10:
                            print(f'''k: {k}, ret: {next_row[idx_up_end_price_col] / tempOrder[
                                "startPrice"] - 1}, predict_k: {
                            outSampleShortPredict[k]}, endprice_k {next_row[idx_up_end_price_col]}, startprice {
                            tempOrder[
                                "startPrice"]}''')
                        break
                    if next_row[idx_up_end_price_col] / tempOrder["startPrice"] - 1 > para["winLimit"] and \
                        abs(round(next_row[idx_up_end_price_col],2) - round(tempOrder["startPrice"],2)) > price_deviation:
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
                break
        elif outSampleShortPredict[k] <= shortTriggerRatio:
            pred_dw = outSampleLongPredict[k]
            while k < len(outSampleLongPredict) - 1:
                row = subTag_array[k]
                if row[idx_bid1p] == 0:
                    # 跌停不卖
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
                    if 1 - next_row[idx_dw_end_price_col] / tempOrder["startPrice"] < para["lossLimit"] and \
                            abs(round(next_row[idx_dw_end_price_col],2) - round(tempOrder["startPrice"], 2)) > price_deviation:
                        tempOrder.update({"type": "loss"})  # 止损
                        if verbose > 10:
                            print(f'''k: {k}, ret: {1 - next_row[idx_dw_end_price_col] / tempOrder[
                                "startPrice"]}, predict_k: {
                            outSampleLongPredict[k]}, endprice_k {next_row[idx_dw_end_price_col]}, startprice {
                            tempOrder[
                                "startPrice"]}''')
                        break
                    if 1 - next_row[idx_dw_end_price_col] / tempOrder["startPrice"] > para["winLimit"] and \
                            abs(round(next_row[idx_dw_end_price_col],2) - round(tempOrder["startPrice"], 2)) > price_deviation:
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
                break
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
                if next_row[idx_up_end_price_col] / tempOrder["startPrice"] - 1 < para["lossLimit"] and \
                        abs(round(next_row[idx_up_end_price_col], 2) - round(tempOrder["startPrice"],2)) > price_deviation:
                    tempOrder.update({"type": "loss"})  # 止损
                    if verbose > 10:
                        print(f'''k: {k}, ret: {next_row[idx_up_end_price_col] / tempOrder[
                            "startPrice"] - 1}, predict_k: {
                        outSampleShortPredict[k]}, endprice_k {next_row[idx_up_end_price_col]}, startprice {tempOrder[
                            "startPrice"]}''')
                    break
                if next_row[idx_up_end_price_col] / tempOrder["startPrice"] - 1 > para["winLimit"] and \
                        abs(round(next_row[idx_up_end_price_col], 2) - round(tempOrder["startPrice"], 2)) > price_deviation:
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
                if 1 - next_row[idx_dw_end_price_col] / tempOrder["startPrice"] < para["lossLimit"] and \
                    abs(round(next_row[idx_dw_end_price_col], 2) - round(tempOrder["startPrice"], 2)) > price_deviation:
                    tempOrder.update({"type": "loss"})  # 止损
                    if verbose > 10:
                        print(f'''k: {k}, ret: {1 - next_row[idx_dw_end_price_col] / tempOrder[
                            "startPrice"]}, predict_k: {
                        outSampleLongPredict[k]}, endprice_k {next_row[idx_dw_end_price_col]}, startprice {tempOrder[
                            "startPrice"]}''')
                    break
                if 1 - next_row[idx_dw_end_price_col] / tempOrder["startPrice"] > para["winLimit"] and \
                        abs(round(next_row[idx_dw_end_price_col], 2) - round(tempOrder["startPrice"], 2)) > price_deviation:
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


def TradingEvaluate(orders_df, longTriggerRatio=None, shortTriggerRatio=None, verbose=0, trigger_time_limit = 500):
    """
    按天评价信号
    :param orders_df:
    :param longTriggerRatio: 触发阈值上限
    :param shortTriggerRatio: 触发阈值下限
    :param verbose:
    :param trigger_time_limit: 增加仓位限制，一天最多触发500次
    :return:
    """
    TradingOrder = {}
    longTriggerRatio = orders_df[orders_df["pred"] > 0]["pred"].min() if not longTriggerRatio else longTriggerRatio
    shortTriggerRatio = orders_df[orders_df["pred"] < 0]["pred"].max() if not shortTriggerRatio else shortTriggerRatio
    TradingOrder.update({"predUp": longTriggerRatio})
    TradingOrder.update({"predDw": shortTriggerRatio})
    TradingOrder.update({"orders": orders_df.head(trigger_time_limit)})    # 限制一天最多触发500次，降低异常数据影响


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
