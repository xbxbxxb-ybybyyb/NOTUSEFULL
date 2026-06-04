import pandas as pd
import numpy as np
import json
from xquant.factordata import FactorData
import os
import ray
import datetime
from artifacts import online_model, parse_format
from artifacts.dataload_utils import get_l2p_data
from artifacts.utils import start_ray_cluster
import polars as pl
from xquant.xqutils.perf_profile import profile

def _reg_eval_by_day(y_true, y_pred, reg_eval_th, reg_eval_abs_limits):
    # concate infer, 从低到高
    sort_index = np.argsort(y_pred, axis=0)
    prediction_output = y_pred[sort_index].reshape(-1, 1)
    label_gold = y_true[sort_index].reshape(-1, 1)
    concat_infer = np.concatenate([prediction_output, label_gold], axis=1)
    n = concat_infer.shape[0]

    # k lst
    k_lst = [10, 20, 30, 40, 50, 100, 200]
    n_sp = 11

    # 预测值acc
    lst = [
        x / 10 for x in list(range(int(reg_eval_abs_limits[0] * 10), int(reg_eval_abs_limits[1] * 10) + 1))]
    lst_neg = [-x for x in lst]
    lst_neg.sort()
    vs = lst_neg + lst
    precisions, recalls, n_preds, n_labels, n_true = [], [], [], [], []
    pred = concat_infer[:, 0]
    label = concat_infer[:, 1]
    for v in vs:
        if v < 0.0:
            n_pred = np.sum(pred <= v)
            n_label = np.sum(label <= -reg_eval_th)
            n_pred_true = np.sum((pred <= v) * (label <= -reg_eval_th))
        else:
            n_pred = np.sum(pred >= v)
            n_label = np.sum(label >= reg_eval_th)
            n_pred_true = np.sum((pred >= v) * (label >= reg_eval_th))
        n_preds.append(n_pred)
        n_labels.append(n_label)
        n_true.append(n_pred_true)
        if n_pred != 0:
            precisions.append(n_pred_true / n_pred)
            recalls.append(n_pred_true / n_label)
        else:
            precisions.append(0.0)
            recalls.append(0.0)
    probs_table = ['{}:{:.3f}/{}'.format(v, p, n) for v, p, n in zip(vs, precisions, n_preds)]
    probs_table_df = pd.DataFrame({"th": reg_eval_th, "pred_th": vs, "pred_pth_num": n_preds, "label_th_num": n_labels,
                                   "pred_pth_label_th_num": n_true, "pred_acc": precisions, "recall": recalls})
    # print('预测值准确率: {}'.format(probs_table))
    # print(probs_table)
    return probs_table, probs_table_df


def evaluate_model_by_day(true_y, pred_y, th1=1.0, th2=2.0, reg_eval_abs_limits=[1.0, 5.0]):
    if type(pred_y) == list:
        pred_y = np.array(pred_y)
    if type(true_y) == list:
        true_y = np.array(true_y)
    probs_table1, probs_table_df_1 = _reg_eval_by_day(true_y, pred_y, reg_eval_th = th1, reg_eval_abs_limits= reg_eval_abs_limits)
    probs_table2, probs_table_df_2 = _reg_eval_by_day(true_y, pred_y, reg_eval_th = th2, reg_eval_abs_limits= reg_eval_abs_limits)
    return probs_table1, probs_table2, probs_table_df_1, probs_table_df_2



def _key_class_acc_and_symbol_acc(y_true, y_pred, pred_th=1.0, true_th=1.0):
    y_true_cp = y_true.copy().reshape(-1)
    y_pred_cp = y_pred.copy().reshape(-1)
    idx = np.where((y_pred_cp <= -pred_th) | (y_pred_cp >= pred_th))
    y_pred_key = y_pred_cp[idx]
    y_true_key = y_true_cp[idx]
    try:
        # 排除0，是因为我们任务既然给出信号了，0的真实标签的误差相比预测信号比较大，不能算符号正确
        key_symbol_acc = round(sum(y_pred_key * y_true_key > 0) / len(y_pred_key),4)
    except:
        key_symbol_acc = 0.0
    count = sum(y_true_key[np.where(y_pred_key <= -pred_th)] <= -true_th) + \
        sum(y_true_key[np.where(y_pred_key >= pred_th)] >= true_th)
    try:
        key_class_acc = round(count / len(y_pred_key),4)
    except:
        key_class_acc = 0.0
    # print('预测标签阈值 {:.6f}, 真实标签阈值 {:.6f}: key_symbol_acc {:.3f}, key_class_acc {:.3f}'.format(
    #     pred_th, true_th, key_symbol_acc, key_class_acc))
    return (pred_th, true_th, key_symbol_acc, key_class_acc)


def _key_and_symbol(etf_y_true_test, etf_y_pred_test_mlp, reg_eval_abs_limits, reg_eval_th=1.0):
    for pred_th in [x / 10 for x in
                    list(range(int(reg_eval_abs_limits[0] * 10), int(reg_eval_abs_limits[1] * 10) + 1))]:
        # for pred_th in [x/10 for x in list(np.arange(reg_eval_abs_limits[0]* 10, reg_eval_abs_limits[1] * 10 + 1/1000, 1/1000))]:
        _key_class_acc_and_symbol_acc(etf_y_true_test, etf_y_pred_test_mlp, pred_th, reg_eval_th)


def _reg_eval(y_true, y_pred, reg_eval_abs_limits=[1.0, 2.5], reg_eval_th=1.0):
    """
    按阈值计算信号准确率
    :param y_true:
    :param y_pred:
    :param reg_eval_abs_limits:
    :param reg_eval_th:
    :return:
    """

    def _top_bottom_k_rst_eval(k, concat_infer):
        top_k_rst = concat_infer[-int(concat_infer.shape[0] / k):]
        mis_num = 0
        for rst in top_k_rst:
            if rst[0] * rst[1] < 0:
                mis_num = mis_num + 1
        top_k_acc = 1.0 - mis_num * 1.0 / int(concat_infer.shape[0] / k)

        bottom_k_rst = concat_infer[:int(concat_infer.shape[0] / k)]
        mis_bottom_num = 0
        for rst in bottom_k_rst:
            if rst[0] * rst[1] < 0:
                mis_bottom_num = mis_bottom_num + 1
        bottom_k_acc = 1.0 - mis_bottom_num * 1.0 / int(concat_infer.shape[0] / k)

        # print('top_{}_symbol_acc: {:.3f}; bottom_{}_symbol_acc: {:.3f}'.format(
        #     k, top_k_acc, k, bottom_k_acc))
        return top_k_acc, bottom_k_acc

    # concate infer, 从低到高
    sort_index = np.argsort(y_pred, axis=0)
    prediction_output = y_pred[sort_index].reshape(-1, 1)
    label_gold = y_true[sort_index].reshape(-1, 1)
    concat_infer = np.concatenate([prediction_output, label_gold], axis=1)
    n = concat_infer.shape[0]

    # k lst
    k_lst = [10, 20, 30, 40, 50, 100, 200]
    n_sp = 11

    # min/max avg value
    for k in k_lst:
        min_avg = np.mean(concat_infer[:int(n / k), 0])
        max_avg = np.mean(concat_infer[-int(n / k):, 0])
        # print('max_avg_{}: {:.3f}; min_avg_{}: {:.3f}'.format(
        #     k, max_avg, k, min_avg))

    # 分位predict 0~1
    vs = []
    for i in range(n_sp):
        idx_ratio = i / (n_sp - 1)
        vs.append(concat_infer[int((n - 1) * idx_ratio), 0])
    print('分位数predict: {}'.format(['{:.3f}'.format(v) for v in vs]))

    # top botttom acc
    for k in k_lst:
        _top_bottom_k_rst_eval(k, concat_infer)

    # 预测值acc
    lst = [
        x / 10 for x in list(range(int(reg_eval_abs_limits[0] * 10), int(reg_eval_abs_limits[1] * 10) + 1))]
    lst_neg = [-x for x in lst]
    lst_neg.sort()
    vs = lst_neg + lst
    precisions, n_preds = [], []
    pred = concat_infer[:, 0]
    label = concat_infer[:, 1]
    for v in vs:
        if v < 0.0:
            n_pred = np.sum(pred <= v)
            n_pred_true = np.sum((pred <= v) * (label <= -reg_eval_th))
        else:
            n_pred = np.sum(pred >= v)
            n_pred_true = np.sum((pred >= v) * (label >= reg_eval_th))
        n_preds.append(n_pred)
        if n_pred != 0:
            precisions.append(n_pred_true / n_pred)
        else:
            precisions.append(0.0)
    probs_table = ['{}:{:.3f}/{}'.format(v, p, n) for v, p, n in zip(vs, precisions, n_preds)]
    # print('预测值准确率: {}'.format(probs_table))
    return probs_table


def compute_metrics(pred_y, true_y, reg_eval_abs_limits, reg_eval_th):
    if type(pred_y) == list:
        pred_y = np.array(pred_y)
    if type(true_y) == list:
        true_y = np.array(true_y)
    # compute metrics 1
    probs_table = _reg_eval(true_y, pred_y, reg_eval_abs_limits= reg_eval_abs_limits,
                           reg_eval_th=reg_eval_th)
    if False:
        # 耗时长，且不够全面
        _key_and_symbol(true_y, pred_y,reg_eval_abs_limits, reg_eval_th=reg_eval_th)
    return probs_table


###########本地信号回测#########################
def __getCho(s):
    s = np.sign(s)
    if not isinstance(s, pd.core.series.Series):
        s = pd.Series(s)
    prt_ary = s.groupby(s).count().values / float(len(s))
    return -(np.log2(prt_ary) * prt_ary).sum()


def pct(base, cur):
    return (cur - base) / base


def __match_order6(hold_time, pnl_list, order_queue, total_ask_value, item, end_condition=[0.003, 0.005, 0.003, 0.005]):
    # end_condition ：【看跌止损， 看跌止盈， 看涨止损， 看涨止盈】
    indx = np.argmax(item[["D_2", "D_1", "O_1", "R_1", "R_2"]].values, axis=0)
    mark = ["D_2", "D_1", "O_1", "R_1", "R_2"]
    direction = mark[indx]
    fee = 0.0005
    for i in range(len(order_queue) - 1, -1, -1):
        order = order_queue[i]
        # 如果信号超时，或者当前时间已经超过14:50了
        if (order[-1] <= item.PERIOD_BEGIN
                or item.PERIOD_BEGIN >= datetime.datetime(item.PERIOD_BEGIN.year, item.PERIOD_BEGIN.month,
                                                          item.PERIOD_BEGIN.day, 14, 50)):
            #             if (order[0][:1] == direction[:1]
            #                 and item.PERIOD_BEGIN < datetime.datetime(item.PERIOD_BEGIN.year,item.PERIOD_BEGIN.month, item.PERIOD_BEGIN.day,14,50)):
            #                 continue
            if order[0].startswith("R"):
                pnl = item.TARGET_VALUE - order[1] - item.TARGET_VALUE * fee
                pnl_list.append(pnl)
                hold_time.append(item.PERIOD_BEGIN - order[-1] + datetime.timedelta(seconds=300))
                total_ask_value.append(item.TARGET_VALUE)
                order_queue.pop(i)
            else:
                pnl = order[1] - item.TARGET_VALUE - order[1] * fee
                pnl_list.append(pnl)
                hold_time.append(item.PERIOD_BEGIN - order[-1] + datetime.timedelta(seconds=300))
                total_ask_value.append(order[1])
                order_queue.pop(i)
        else:
            # 如果是看跌订单
            if order[0].startswith("D_"):
                # 如果当前预测方向和订单方向一致，说明可能还有更好的机会。
                if direction.startswith("D_") and (order[1] - item.TARGET_VALUE) / order[1] < 0.003:
                    continue
                # 如果达到止损线，则止损。
                elif item.TARGET_VALUE >= order[3]:
                    pnl = order[1] - item.TARGET_VALUE - order[1] * fee
                    pnl_list.append(pnl)
                    order_queue.pop(i)
                    total_ask_value.append(order[1])
                    hold_time.append(item.PERIOD_BEGIN - order[-1] + datetime.timedelta(seconds=300))
                # 如果达到止盈线，则止盈
                #                 elif item.TARGET_VALUE <= order[2]:
                elif (order[1] - item.TARGET_VALUE) / order[1] >= 0.005:
                    pnl = order[1] - item.TARGET_VALUE - order[1] * fee
                    pnl_list.append(pnl)
                    order_queue.pop(i)
                    total_ask_value.append(order[1])
                    hold_time.append(item.PERIOD_BEGIN - order[-1] + datetime.timedelta(seconds=300))
            else:
                # 看涨
                if direction[:1].startswith("R_") and (item.TARGET_VALUE - order[1]) / order[1] < 0.003:
                    continue
                elif item.TARGET_VALUE <= order[3]:
                    pnl = item.TARGET_VALUE - order[1] - item.TARGET_VALUE * fee
                    pnl_list.append(pnl)
                    order_queue.pop(i)
                    total_ask_value.append(item.TARGET_VALUE)
                    hold_time.append(item.PERIOD_BEGIN - order[-1] + datetime.timedelta(seconds=300))
                #                 elif item.TARGET_VALUE >= order[2]:
                elif (item.TARGET_VALUE - order[1]) / order[1] >= 0.005:
                    pnl = item.TARGET_VALUE - order[1] - item.TARGET_VALUE * fee
                    pnl_list.append(pnl)
                    order_queue.pop(i)
                    total_ask_value.append(item.TARGET_VALUE)
                    hold_time.append(item.PERIOD_BEGIN - order[-1] + datetime.timedelta(seconds=300))

def __return_flag(df):
    if np.argmax(df) in ["R_1", 0]:
        return 1
    if np.argmax(df) in ["R_2", 1]:
        return 2
    if np.argmax(df) in ["D_1", 3]:
        return -1
    if np.argmax(df) in ["D_2", 4]:
        return -2
    return 0

def __generate_order(item_series):
    indx = np.argmax(item_series[["D_2","D_1","O_1","R_1","R_2"]].values,axis=0)
    if indx==0:
        return ("D_2",item_series.TARGET_VALUE,item_series.TARGET_VALUE*(1-0.002), item_series.TARGET_VALUE*(1+0.0008), item_series.PERIOD_END)
    if indx==1:
        return ("D_1",item_series.TARGET_VALUE,item_series.TARGET_VALUE*(1-0.0012), item_series.TARGET_VALUE*(1+0.0008), item_series.PERIOD_END)
    if indx==2:
        return ("O_1",)
    if indx==3:
        return ("R_1",item_series.TARGET_VALUE,item_series.TARGET_VALUE*(1+0.0012), item_series.TARGET_VALUE*(1-0.0008), item_series.PERIOD_END)
    if indx==4:
        return ("R_2",item_series.TARGET_VALUE,item_series.TARGET_VALUE*(1+0.002), item_series.TARGET_VALUE*(1-0.0008), item_series.PERIOD_END)

def backtest_oneday(signal_process_base_dir, date="2022-12-06"):
    """回测一天"""
    if not os.path.exists(os.path.join(signal_process_base_dir, date + ".txt")):
        return {}
    signal_process_df = parse_format.parse_signal_txt(os.path.join(signal_process_base_dir, date + ".txt"))
    # print("BackTest on: ", date)
    signal_process_df["flag"] = signal_process_df[["D_2", "D_1", "O_1", "R_1", "R_2"]].apply(__return_flag, axis=1)
    signal_process_df["cho"] = signal_process_df["flag"].rolling(2, 1).apply(__getCho)
    order_queue = []
    pnl_list = []
    hold_time = []
    total_ask_value = []
    for i in signal_process_df.index:
        item = signal_process_df.loc[i]
        __match_order6(hold_time, pnl_list, order_queue, total_ask_value, item)
        new_order = __generate_order(item)
        if not new_order[0].startswith("O_"):
            #         if not new_order[0].startswith("O_") and item.cho<0.5:
            order_queue.append(new_order)

    res_dict = {}
    res_dict["date"] = date
    res_dict["pnl"] = sum(pnl_list)
    res_dict["total_num"] = len(pnl_list)
    res_dict["pos"] = len([v for v in pnl_list if v >= 0])
    res_dict["pos/total"] = res_dict["pos"] / res_dict["total_num"] if res_dict["total_num"] != 0 else 0
    res_dict["order"] = len(order_queue)
    res_dict["total_value"] = sum(total_ask_value)
    res_dict["mean_hold_time"] = np.mean([v.total_seconds() for v in hold_time])
    res_dict["rate"] = res_dict["pnl"] / res_dict["total_value"] if res_dict["total_value"] != 0 else 0
    res_dict["hold_time"] = np.array([v.total_seconds() for v in hold_time])
    res_dict["pnl_list"] = np.array(pnl_list)
    return res_dict
###########本地信号回测#########################


def judge_long(lis, profit, loss, start_price, time_arr, end_time):
    for iidx,i in enumerate(lis):
        if time_arr[iidx]>=end_time:
            break
        if i > profit and round(i,2)-round(start_price,2)>0.01:
            return 2
        if i < loss and round(start_price,2)-round(i,2)>0.01:
            return 0
    return 1


def judge_short(lis, profit, loss, start_price, time_arr, end_time):
    for iidx,i in enumerate(lis):
        if time_arr[iidx]>=end_time:
            break
        if i < profit and round(start_price,2)-round(i, 2)>0.01:
            return 2
        if i > loss and round(i,2)-round(start_price,2)>0.01:
            return 0
    return 1


def find_stop(signal_df, profit_ratio, loss_ratio, target_type = "mid"):
    """
    计算有效信号的止盈率，止损率
    :param signal_df: 标准的DataFrame列，此外还必须有PROBABILITY，五分类列
    :param profit_ratio:
    :param loss_ratio:
    :return:
    """
    if target_type=="mid":
        up_start_price_col = "TARGET_VALUE"
        up_end_price_col = "TARGET_VALUE"
        dw_start_price_col = "TARGET_VALUE"
        dw_end_price_col = "TARGET_VALUE"
    elif target_type=="longshort":
        up_start_price_col = "Ask1P"
        up_end_price_col = "Bid1P"
        dw_start_price_col = "Bid1P"
        dw_end_price_col = "Ask1P"
    else:
        raise Exception("计算止盈止损收益率的价格类型ret_type仅支持mid, longshort!")

    df = signal_df.reset_index()
    res_lis = []
    res_up_down = pd.DataFrame()
    info_dic = {"up_up":0,
                "up_0" :0,
                "up_dw":0,
                "dw_up":0,
                "dw_0" :0,
                "dw_dw":0
               }
    valid_df = df[df["cls"]!=2]
    arr_period_begin = df["PERIOD_BEGIN"].values
    arr_period_end = df["PERIOD_END"].values
    arr_up_end_price = df[up_end_price_col].values
    arr_dw_end_price = df[dw_end_price_col].values
    for ridx, (_, row) in enumerate(df.iterrows()):
        if row["cls"] != 2:
            t1 = arr_period_begin[ridx]
            t2 = arr_period_end[ridx]
            # #print(t1,t2)
            # try:
            #     idx2 = df.loc[df["PERIOD_BEGIN"] >= t2].index[0]
            # except:
            #     idx2 = df.index[-1]
            # #print(idx, idx2)
            # tmp = df.iloc[idx:idx2]
            #print(t1,t2, row["TARGET_VALUE"] )

            if row["cls"] > 2:  # 看涨
                profit = row[up_start_price_col] * (1 + profit_ratio)
                loss =   row[up_start_price_col] * (1 - loss_ratio)
                res = judge_long(arr_up_end_price[ridx:], profit, loss, row[up_start_price_col], time_arr = arr_period_begin[ridx:] ,end_time = t2)
                #print(res)
                if res == 2:
                    info_dic["up_up"] += 1
                if res == 1:
                    info_dic["up_0"] += 1
                if res == 0:
                    info_dic["up_dw"] += 1
                #print("看涨", t1,t2, row["TARGET_VALUE"],res )
            else:               # 看跌
                profit = row[dw_start_price_col] * (1 - profit_ratio)
                loss =   row[dw_start_price_col] * (1 + loss_ratio)
                res = judge_short(list(arr_dw_end_price[ridx:]), profit, loss, row[dw_start_price_col], time_arr = arr_period_begin[ridx:], end_time = t2)
                if res == 2:
                    info_dic["dw_dw"] += 1
                if res == 1:
                    info_dic["dw_0"] += 1
                if res == 0:
                    info_dic["dw_up"] += 1
                #print("看跌", t1,t2, row["TARGET_VALUE"],res )
        else:
            res = np.nan
        res_lis.append(res)
    #print(info_dic)
    up_total = info_dic["up_up"] + info_dic["up_0"] + info_dic["up_dw"]
#     try:
#         print("涨： 共{}个\t 止盈率：{}\t 平率：{}\t 止损率：{}".format(up_total,  round(info_dic["up_up"]/up_total,4),
#                                                                     round(info_dic["up_0"] /up_total,4),
#                                                                     round(info_dic["up_dw"]/up_total,4) ))
#     except:
#         pass
    dw_total = info_dic["dw_up"] + info_dic["dw_0"] + info_dic["dw_dw"]
#     try:
#         print("跌： 共{}个\t 止盈率：{}\t 平率：{}\t 止损率：{}".format(dw_total,  round(info_dic["dw_dw"]/dw_total,4),
#                                                                     round(info_dic["dw_0"] /dw_total,4),
#                                                                     round(info_dic["dw_up"]/dw_total,4) ))
#     except:
#         pass
    up_zero = False
    dw_zero = False
    try:
        if not up_total:
            up_total = 1
            up_zero= True
        if not dw_total:
            dw_total = 1
            dw_zero = True
        res_up_down = pd.DataFrame(
            {'涨信号个数': up_total, '涨信号止盈个数': info_dic["up_up"], '涨信号平个数': info_dic["up_0"], '涨信号止损个数': info_dic["up_dw"],
             '涨信号止盈率': round(info_dic["up_up"] / up_total, 4) if up_total else 0, '涨信号平率': round(info_dic["up_0"] / up_total, 4) if up_total else 0,
             '涨信号止损率': round(info_dic["up_dw"] / up_total, 4) if up_total else 0,
             '跌信号个数': dw_total, '跌信号止盈个数': info_dic["dw_dw"], '跌信号平个数': info_dic["dw_0"], '跌信号止损个数': info_dic["dw_up"],
             '跌信号止盈率': round(info_dic["dw_dw"] / dw_total, 4) if dw_total else 0, '跌信号平率': round(info_dic["dw_0"] / dw_total, 4) if dw_total else 0,
             '跌信号止损率': round(info_dic["dw_up"] / dw_total, 4) if dw_total else 0},
            index=[df.iloc[0]['Date']])
        res_up_down['止盈率'] = profit_ratio
        res_up_down['止损率'] = loss_ratio
        if up_zero:
            res_up_down["涨信号个数"] = 0
        if dw_zero:
            res_up_down["跌信号个数"] = 0
    except Exception as e:
        print(e)
    #     print('Done!')
    return res_up_down


###### 计算全部信号的止盈止损，只能阈值0,0，返回信号dataframe多一列
def find_stop_all(signal_df, profit_ratio, loss_ratio, target_type = "mid"):
    """
    计算有效信号的止盈率，止损率
    :param signal_df: 标准的DataFrame列，此外还必须有PROBABILITY，五分类列
    :param profit_ratio:
    :param loss_ratio:
    :return:
    """
    if target_type=="mid":
        up_start_price_col = "TARGET_VALUE"
        up_end_price_col = "TARGET_VALUE"
        dw_start_price_col = "TARGET_VALUE"
        dw_end_price_col = "TARGET_VALUE"
    elif target_type=="longshort":
        up_start_price_col = "Ask1P"
        up_end_price_col = "Bid1P"
        dw_start_price_col = "Bid1P"
        dw_end_price_col = "Ask1P"
    else:
        raise Exception("计算止盈止损收益率的价格类型ret_type仅支持mid, longshort!")

    df = signal_df.reset_index()
    res_lis = []
    valid_df = df[df["cls"]!=2]
    arr_period_begin = df["PERIOD_BEGIN"].values
    arr_period_end = df["PERIOD_END"].values
    arr_up_end_price = df[up_end_price_col].values
    arr_dw_end_price = df[dw_end_price_col].values
    for ridx, (_, row) in enumerate(df.iterrows()):
        if row["cls"] != 2:
            t1 = arr_period_begin[ridx]
            t2 = arr_period_end[ridx]
            # #print(t1,t2)
            # try:
            #     idx2 = df.loc[df["PERIOD_BEGIN"] >= t2].index[0]
            # except:
            #     idx2 = df.index[-1]
            # #print(idx, idx2)
            # tmp = df.iloc[idx:idx2]
            #print(t1,t2, row["TARGET_VALUE"] )

            if row["cls"] > 2:  # 看涨
                profit = row[up_start_price_col] * (1 + profit_ratio)
                loss =   row[up_start_price_col] * (1 - loss_ratio)
                res = judge_long(arr_up_end_price[ridx:], profit, loss, row[up_start_price_col], time_arr = arr_period_begin[ridx:] ,end_time = t2)
            else:               # 看跌
                profit = row[dw_start_price_col] * (1 - profit_ratio)
                loss =   row[dw_start_price_col] * (1 + loss_ratio)
                res = judge_short(list(arr_dw_end_price[ridx:]), profit, loss, row[dw_start_price_col], time_arr = arr_period_begin[ridx:], end_time = t2)
        else:
            res = np.nan
        res_lis.append(res)

    df['state'] = res_lis

    return df



def winloss_stop_table_daily(signal_df, long_pred_th = 1.2, short_pred_th = -1.2, target_type = "mid",
                             win_limits = [0.0015], loss_limits = [0.002], t_sta="09:33:00",
                             use_self_prob = False, local_mode = False):
    """
      统计单天信号，在指定止盈止损线情况下的，止盈止损率
      :param signal_df: 标准的信号原始DataFram
      :param long_pred_th: 有效信号的上涨阈值
      :param short_pred_th: 有效信号的下跌阈值
      :param win_limits:
      :param loss_limits:
      :param t_sta: 计算有效信号的开始时间,
      :param use_self_prob: 是否使用signal_df中自带的PROBABILITY字段
      :return:
      """
    if long_pred_th == 0  and short_pred_th == 0:
        new_find_stop = find_stop_all
    else:
        new_find_stop = find_stop
    if not "PREDICT" in signal_df.columns:
        signal_df["PREDICT"] = signal_df["PREDICTED"]
    if not "PREDICTED" in signal_df.columns:
        signal_df["PREDICTED"] = signal_df["PREDICT"]
    assert type(win_limits) == list and type(loss_limits) == list, "win_limits和loss_limits必须为list类型"
    if not use_self_prob:
        signal_df["PROBABILITY"] = signal_df["PREDICT"].apply(
            lambda x: online_model.reg2cls_v3(x, minMap=-6, maxMap=6, long_pred_th=long_pred_th,
                                              short_pred_th=short_pred_th))
    use_pandas = False
    t_sta = int(t_sta.replace(":", ""))

    if use_pandas:
        # slow
        # print("use_pandas:", use_pandas)
        signal_df["DateTime"] = signal_df["PERIOD_BEGIN"]
        signal_df = signal_df.set_index("DateTime")
        signal_df['Date'] = signal_df.index
        signal_df['Date'] = signal_df['Date'].apply(lambda x: str(x)[:10])

        df = signal_df
        df["PERIOD_BEGIN"] = df["PERIOD_BEGIN"].apply(lambda x: int(str(x).replace(":", "")[-6:]))
        df["PERIOD_END"] = df["PERIOD_END"].apply(lambda x: int(str(x).replace(":", "")[-6:]))
        df = df[(df["PERIOD_BEGIN"] >= t_sta)]
        df["PERIOD_BEGIN"] = df["PERIOD_BEGIN"].apply(lambda x: str(x))
        df["info_probs"] = ""
        df["cls"] = df["PROBABILITY"].apply(lambda x: np.argmax(eval(str(x))))
        df["up"] = df.apply(lambda row: row["TARGET_VALUE"] if row["cls"] > 2 else np.nan, axis=1)
        df["dw"] = df.apply(lambda row: row["TARGET_VALUE"] if row["cls"] < 2 else np.nan, axis=1)
    else:
        # print("use_pandas:", use_pandas)
        signal_df = pl.from_pandas(signal_df)
        try:
            df1 = signal_df.with_columns(
                PERIOD_BEGIN=pl.col("PERIOD_BEGIN").str.strptime(dtype=pl.Datetime, format="%Y-%m-%d %H:%M:%S"),
                PERIOD_END=pl.col("PERIOD_END").str.strptime(dtype=pl.Datetime, format="%Y-%m-%d %H:%M:%S"),
            )
        except:
            df1 = signal_df
        df1 = df1.with_columns(Date=pl.col("PERIOD_BEGIN").dt.strftime("%Y-%m-%d"),
                               DateTime=pl.col("PERIOD_BEGIN"),
                               TimeStamp=pl.col("PERIOD_BEGIN").dt.replace_time_zone("Asia/Shanghai").dt.timestamp(
                                   time_unit="ms"),
                               PERIOD_BEGIN=pl.col("PERIOD_BEGIN").dt.strftime("%H%M%S").cast(pl.Int32),
                               PERIOD_END=pl.col("PERIOD_END").dt.strftime("%H%M%S").cast(pl.Int32),
                               cls=pl.col("PROBABILITY").list.arg_max()
                               ). \
            with_columns(up=pl.when(pl.col("cls") > 2).then(pl.col("TARGET_VALUE")).otherwise(np.nan),
                         dw=pl.when(pl.col("cls") < 2).then(pl.col("TARGET_VALUE")).otherwise(np.nan),
                         ). \
            filter(pl.col("PERIOD_BEGIN") >= t_sta)
        df1 = df1.sort(by="DateTime")
        if target_type != "mid":
            symbol = signal_df["SYMBOL"][0]
            start_date, end_date = df1["Date"].min(), df1["Date"].max()
            l2p_df = get_l2p_data(symbol, start_date, end_date).select(["DateTime", "Ask1P", "Bid1P", "M_OpenPx"])
            df1 = df1.join(l2p_df, on="DateTime")
            df = df1.to_pandas().reset_index(drop=True)
        else:
            df = df1.to_pandas().reset_index(drop=True)

    res_dict = {}
    dates = sorted(list(set(df['Date'])))
    if not local_mode:
        start_ray_cluster(num_cpus=10, restart=False)
        remote_func = ray.remote(new_find_stop)
        for win_ratio in win_limits:
            for loss_ratio in loss_limits:
                tasks = [remote_func.remote(
                    df[df['Date'] == i],
                    win_ratio,
                    loss_ratio,
                    target_type
                ) for i in dates]
                res_tmp = ray.get(tasks)
                res = pd.concat(res_tmp)
                res = res.sort_index()
                res['止盈线'] = win_ratio
                res['止损线'] = loss_ratio
            res_dict[(win_ratio, loss_ratio)] = res
        # ray.shutdown()
    else:
        for win_ratio in win_limits:
            for loss_ratio in loss_limits:
                res_tmp = [new_find_stop(
                    df[df['Date'] == i],
                    win_ratio,
                    loss_ratio,
                    target_type
                ) for i in dates]
                res = pd.concat(res_tmp)
                res = res.sort_index()
                res['止盈线'] = win_ratio
                res['止损线'] = loss_ratio
            res_dict[(win_ratio, loss_ratio)] = res
    return res_dict


def winloss_func_agg(res_df, verbose = 1):
    """
    先调用winloss_func，再调用本函数
    :param res_df:
    :return:
    """
    ##################汇总整个区间内止盈止损指标######################
    a = res_df["涨信号止盈个数"].sum() + res_df["跌信号止盈个数"].sum()
    b = res_df["涨信号平个数"].sum() + res_df["跌信号平个数"].sum()
    c = res_df["涨信号止损个数"].sum() + res_df["跌信号止损个数"].sum()
    abc = res_df["总信号个数"].sum()
    win_tol = a / abc
    eq_tol = b / abc
    loss_tol = c / abc
    num_tol = abc
    win_day = res_df["总止盈率"].mean()
    eq_day = res_df["总平率"].mean()
    loss_day = res_df["总止损率"].mean()
    num_day = res_df["总信号个数"].mean()

    up_win_tol = round(res_df["涨信号止盈个数"].sum() / res_df["涨信号个数"].sum(), 3) if res_df["涨信号个数"].sum() else 0
    up_eq_tol = round(res_df["涨信号平个数"].sum() / res_df["涨信号个数"].sum(), 3) if res_df["涨信号个数"].sum() else 0
    up_loss_tol = round(res_df["涨信号止损个数"].sum() / res_df["涨信号个数"].sum(), 3) if res_df["涨信号个数"].sum() else 0
    up_num_tol = round(res_df["涨信号个数"].sum(), 3)
    # up_win_day = round(res_df.mean()["涨信号止盈率"], 3)
    # up_loss_day = round(res_df.mean()["涨信号止损率"], 3)
    # up_eq_day = round(res_df.mean()["涨信号平率"], 3)
    # up_num_day = round(res_df.mean()["涨信号个数"], 3)
    up_win_day = round(res_df["涨信号止盈率"].mean(), 3)
    up_loss_day = round(res_df["涨信号止损率"].mean(), 3)
    up_eq_day = round(res_df["涨信号平率"].mean(), 3)
    up_num_day = round(res_df["涨信号个数"].mean(), 3)

    dw_win_tol = round(res_df["跌信号止盈个数"].sum() / res_df["跌信号个数"].sum(), 3) if res_df["跌信号个数"].sum() else 0
    dw_eq_tol = round(res_df["跌信号平个数"].sum() / res_df["跌信号个数"].sum(), 3) if res_df["跌信号个数"].sum() else 0
    dw_loss_tol = round(res_df["跌信号止损个数"].sum() / res_df["跌信号个数"].sum(), 3) if res_df["跌信号个数"].sum() else 0
    dw_num_tol = round(res_df["跌信号个数"].sum(), 3)
    # dw_win_day = round(res_df.mean()["跌信号止盈率"], 3)
    # dw_loss_day = round(res_df.mean()["跌信号止损率"], 3)
    # dw_eq_day = round(res_df.mean()["跌信号平率"], 3)
    # dw_num_day = round(res_df.mean()["跌信号个数"], 3)
    dw_win_day = round(res_df["跌信号止盈率"].mean(), 3)
    dw_loss_day = round(res_df["跌信号止损率"].mean(), 3)
    dw_eq_day = round(res_df["跌信号平率"].mean(), 3)
    dw_num_day = round(res_df["跌信号个数"].mean(), 3)

    eva_dict = {"涨总体": {"个数": up_num_tol, "止盈率": up_win_tol, "平率": up_eq_tol, "止损率": up_loss_tol},
                "跌总体": {"个数": dw_num_tol, "止盈率": dw_win_tol, "平率": dw_eq_tol, "止损率": dw_loss_tol},
                "涨跌总体": {"个数": num_tol, "止盈率": win_tol, "平率": eq_tol, "止损率": loss_tol},
                "涨日均": {"个数": up_num_day, "止盈率": up_win_day, "平率": up_eq_day, "止损率": up_loss_day},
                "跌日均": {"个数": dw_num_day, "止盈率": dw_win_day, "平率": dw_eq_day, "止损率": dw_loss_day},
                "涨跌日均": {"个数": num_day, "止盈率": win_day, "平率": eq_day, "止损率": loss_day},
                }
    agg_df = pd.DataFrame(eva_dict)
    agg_df = agg_df.unstack().to_frame().T
    agg_df.columns = [col[0]+col[1] for col in agg_df.columns.to_flat_index()]
    res_df = res_df.reset_index()
    sdate, edate = res_df["index"].min(), res_df["index"].max()
    try:
        symbol_name = res_df["标的"].iloc[0]
        short_pred_th = res_df["跌阈值"].iloc[0]
        long_pred_th = res_df["涨阈值"].iloc[0]
        agg_df.insert(0, "跌阈值", short_pred_th)
        agg_df.insert(0, "涨阈值", long_pred_th)
        agg_df.insert(0, "止损线", res_df["止损线"].iloc[0])
        agg_df.insert(0, "止盈线", res_df["止盈线"].iloc[0])
    except:
        pass
        symbol_name = ""
    agg_df.insert(0, "结束日期", edate)
    agg_df.insert(0, "开始日期", sdate)
    agg_df["信号质量加权"] = (a - 2.5 * c - 0.5 * b) / abc
    eva_dict.update( {"信号质量加权": (a - 2.5 * c - 0.5 * b) / abc})
    if verbose:
        print(f"======================{symbol_name} {short_pred_th} {long_pred_th}===========================")
        print(f"涨信号【总体】：信号个数: {up_num_tol}， 止盈率：{up_win_tol}, 平率： {up_eq_tol}， 止损率： {up_loss_tol}")
        print(f"跌信号【总体】：信号个数: {dw_num_tol}，止盈率：{dw_win_tol}, 平率： {dw_eq_tol}， 止损率： {dw_loss_tol}")
        print(f"涨跌信号【总体】：信号个数: {num_tol}，止盈率：{win_tol}, 平率： {eq_tol}， 止损率： {loss_tol}")
        print(f"涨信号日均：信号个数: {up_num_day}，止盈率：{up_win_day}，平率：{up_eq_day}, 止损率：{up_loss_day}")
        print(f"跌信号日均：信号个数: {dw_num_day}，止盈率：{dw_win_day}，平率：{dw_eq_day}, 止损率：{dw_loss_day}")
        print(f"涨跌信号日均：信号个数: {num_day}，止盈率：{win_day}，平率：{eq_day}, 止损率：{loss_day}")
        print(f"信号质量加权: {(a - 2.5 * c - 0.5 * b) / abc}")
    #     eva_dict = {"涨总信号个数": up_num_tol, "涨总止盈率":up_win_tol, "涨总平率": up_eq_tol, "涨总止损率": up_loss_tol,
    #         "涨信号个数": dw_num_tol,"涨总止盈率":dw_win_tol,"涨总平率": dw_eq_tol, "涨总止损率": dw_loss_tol,
    #         "涨总信号个数": up_num_day,"涨总止盈率":up_win_day,"涨日均平率":up_eq_day, "涨日均止损率":up_loss_day,
    #         "跌日信号个数": dw_num_day,"跌日均止盈率":dw_win_day,"跌日均平率":dw_eq_day, "跌日均止损率":dw_loss_day}
    return agg_df, eva_dict

def winloss_func(symbol_name, source_signal_df, long_pred_th, short_pred_th, start_date="2023-12-06", end_date="2024-02-06", use_self_prob = False,
                 local_mode = False, target_type="mid", t_sta="09:33:00", win_limits=[0.0015, 0.002], loss_limits=[0.002]):
    res_dict = winloss_stop_table_daily(source_signal_df,
                                        long_pred_th=long_pred_th,
                                        short_pred_th=short_pred_th,
                                        target_type = target_type,
                                        win_limits=win_limits,
                                        loss_limits=loss_limits,
                                        t_sta=t_sta,
                                        use_self_prob=use_self_prob,
                                        local_mode = local_mode
                                        )
    # res_df = res_dict[(0.0015, 0.002)]
    res_df = res_dict[(win_limits[0], loss_limits[0])]
    start_date = pd.to_datetime(start_date).strftime("%Y-%m-%d")
    end_date = pd.to_datetime(end_date).strftime("%Y-%m-%d")
    res_df = res_df[(res_df.index >= start_date) & (res_df.index <= end_date)]
    ##################计算每天的总止盈止损和质量加权######################
    res_df["总止盈率"] = (res_df["涨信号止盈个数"] + res_df["跌信号止盈个数"]) / (res_df["涨信号个数"] + res_df["跌信号个数"])
    res_df["总止损率"] = (res_df["涨信号止损个数"] + res_df["跌信号止损个数"]) / (res_df["涨信号个数"] + res_df["跌信号个数"])
    res_df["总平率"] = (res_df["涨信号平个数"] + res_df["跌信号平个数"]) / (res_df["涨信号个数"] + res_df["跌信号个数"])
    res_df["总信号个数"] = (res_df["涨信号个数"] + res_df["跌信号个数"])
#     res_df["信号质量加权"] = (res_df["涨信号止盈个数"]+res_df["跌信号止盈个数"])*1-(res_df["涨信号止损个数"]+res_df["跌信号止盈个数"])*1-0.5*(res_df["涨信号平个数"]+res_df["跌信号平个数"])
    res_df["信号质量加权"] = (res_df["总止盈率"] * 1 - res_df["总止损率"] * 2.5 - res_df["总平率"] * 0.5)
    res_df.insert(0, "跌阈值", short_pred_th)
    res_df.insert(0, "涨阈值", long_pred_th)
    res_df.insert(0, "标的", symbol_name)
    return res_df



def winloss_func_dict(source_signal_df, long_pred_th, short_pred_th, start_date="2023-12-06", end_date="2024-02-06", use_self_prob = False):
    res_dict = winloss_stop_table_daily(source_signal_df,
                                        long_pred_th=long_pred_th,
                                        short_pred_th=short_pred_th,
                                        win_limits=[0.0015, 0.002],
                                        loss_limits=[0.002],
                                        t_sta="09:33:00",
                                        use_self_prob=use_self_prob,
                                        local_mode = True
                                        )
    res_df = res_dict[(0.0015, 0.002)]
    start_date = pd.to_datetime(start_date).strftime("%Y-%m-%d")
    end_date = pd.to_datetime(end_date).strftime("%Y-%m-%d")
    res_df = res_df[(res_df.index >= start_date) & (res_df.index <= end_date)]

    up_win_tol = round(res_df["涨信号止盈个数"].sum() / res_df["涨信号个数"].sum(), 3) if res_df["涨信号个数"].sum() else 0
    up_eq_tol = round(res_df["涨信号平个数"].sum() / res_df["涨信号个数"].sum(), 3) if res_df["涨信号个数"].sum() else 0
    up_loss_tol = round(res_df["涨信号止损个数"].sum() / res_df["涨信号个数"].sum(), 3) if res_df["涨信号个数"].sum() else 0
    up_num_tol = round(res_df["涨信号个数"].sum(), 3)
    up_win_day = round(res_df.mean()["涨信号止盈率"], 3)
    up_loss_day = round(res_df.mean()["涨信号止损率"], 3)
    up_eq_day = round(res_df.mean()["涨信号平率"], 3)
    up_num_day = round(res_df.mean()["涨信号个数"], 3)

    dw_win_tol = round(res_df["跌信号止盈个数"].sum() / res_df["跌信号个数"].sum(), 3) if res_df["跌信号个数"].sum() else 0
    dw_eq_tol = round(res_df["跌信号平个数"].sum() / res_df["跌信号个数"].sum(), 3) if res_df["跌信号个数"].sum() else 0
    dw_loss_tol = round(res_df["跌信号止损个数"].sum() / res_df["跌信号个数"].sum(), 3) if res_df["跌信号个数"].sum() else 0
    dw_num_tol = round(res_df["跌信号个数"].sum(), 3)
    dw_win_day = round(res_df.mean()["跌信号止盈率"], 3)
    dw_loss_day = round(res_df.mean()["跌信号止损率"], 3)
    dw_eq_day = round(res_df.mean()["跌信号平率"], 3)
    dw_num_day = round(res_df.mean()["跌信号个数"], 3)

    print(f"涨信号【总体】：信号个数: {up_num_tol}， 止盈率：{up_win_tol}, 平率： {up_eq_tol}， 止损率： {up_loss_tol}")
    print(f"跌信号【总体】：信号个数: {dw_num_tol}，止盈率：{dw_win_tol}, 平率： {dw_eq_tol}， 止损率： {dw_loss_tol}")
    print(f"涨信号日均：信号个数: {up_num_day}，止盈率：{up_win_day}，平率：{up_eq_day}, 止损率：{up_loss_day}")
    print(f"跌信号日均：信号个数: {dw_num_day}，止盈率：{dw_win_day}，平率：{dw_eq_day}, 止损率：{dw_loss_day}")
    eva_dict = {"涨信号总体": {"信号个数": up_num_tol, "止盈率": up_win_tol, "平率": up_eq_tol, "止损率": up_loss_tol},
                "跌信号总体": {"信号个数": dw_num_tol, "止盈率": dw_win_tol, "平率": dw_eq_tol, "止损率": dw_loss_tol}
                }
    #     eva_dict = {"涨总信号个数": up_num_tol, "涨总止盈率":up_win_tol, "涨总平率": up_eq_tol, "涨总止损率": up_loss_tol,
    #         "涨信号个数": dw_num_tol,"涨总止盈率":dw_win_tol,"涨总平率": dw_eq_tol, "涨总止损率": dw_loss_tol,
    #         "涨总信号个数": up_num_day,"涨总止盈率":up_win_day,"涨日均平率":up_eq_day, "涨日均止损率":up_loss_day,
    #         "跌日信号个数": dw_num_day,"跌日均止盈率":dw_win_day,"跌日均平率":dw_eq_day, "跌日均止损率":dw_loss_day}
    return eva_dict

def find_stop_new(df_res, profit_ratio, loss_ratio, pred_th,
                  model_name, symbol_name, date):
    # TODO df_res为polars.DataFrame
    ###### 3.改变信号阈值
    maxMap = 6
    minMap = -6
    if "cls" in df_res.columns:
        df_res = df_res.drop("cls")
    df_res = df_res.with_columns(pl.when(pl.col("PREDICTED") >= maxMap).then(4)
                                .when(pl.col("PREDICTED") <= minMap).then(0)
                                .when((pl.col("PREDICTED") >= pred_th) & (pl.col("PREDICTED") <= maxMap)).then(3)
                                .when((pl.col("PREDICTED") <= -pred_th) & (pl.col("PREDICTED") >= minMap)).then(1)
                                .otherwise(2)
                                .alias("cls")
                                )

    info_dic = {"up_up": 0,
                "up_0": 0,
                "up_dw": 0,
                "dw_up": 0,
                "dw_0": 0,
                "dw_dw": 0
                }
    # state: 2涨 1平 0跌
    df_res = df_res.with_columns(pl.when((pl.col('cls') > 2) & (pl.col("state") == 2))
                                 .then(True)
                                 .otherwise(False)
                                 .alias("up_up")
                                 )
    df_res = df_res.with_columns(pl.when((pl.col('cls') > 2) & (pl.col("state") == 1))
                                 .then(True)
                                 .otherwise(False)
                                 .alias("up_0")
                                 )
    df_res = df_res.with_columns(pl.when((pl.col('cls') > 2) & (pl.col("state") == 0))
                                 .then(True)
                                 .otherwise(False)
                                 .alias("up_dw")
                                 )
    df_res = df_res.with_columns(pl.when((pl.col('cls') <2) & (pl.col("state") == 0))
                                 .then(True)
                                 .otherwise(False)
                                 .alias("dw_up")
                                 )
    df_res = df_res.with_columns(pl.when((pl.col('cls') < 2) & (pl.col("state") == 1))
                                 .then(True)
                                 .otherwise(False)
                                 .alias("dw_0")
                                 )
    df_res = df_res.with_columns(pl.when((pl.col('cls') < 2) & (pl.col("state") == 2))
                                 .then(True)
                                 .otherwise(False)
                                 .alias("dw_dw")
                                 )

    info_dic["up_up"] = sum(df_res["up_up"])
    info_dic["up_0"] = sum(df_res["up_0"])
    info_dic["up_dw"] = sum(df_res["up_dw"])
    info_dic["dw_up"] = sum(df_res["dw_up"])
    info_dic["dw_0"] = sum(df_res["dw_0"])
    info_dic["dw_dw"] = sum(df_res["dw_dw"])

    up_total = info_dic["up_up"] + info_dic["up_0"] + info_dic["up_dw"]
    dw_total = info_dic["dw_up"] + info_dic["dw_0"] + info_dic["dw_dw"]

    up_zero = False
    dw_zero = False
    try:
        if not up_total:
            up_total = 1
            up_zero = True
        if not dw_total:
            dw_total = 1
            dw_zero = True
        res_up_down = pd.DataFrame(
            {'涨信号个数': up_total, '涨信号止盈个数': info_dic["up_up"], '涨信号平个数': info_dic["up_0"], '涨信号止损个数': info_dic["up_dw"],
             '涨信号止盈率': round(info_dic["up_up"] / up_total, 4) if up_total else 0,
             '涨信号平率': round(info_dic["up_0"] / up_total, 4) if up_total else 0,
             '涨信号止损率': round(info_dic["up_dw"] / up_total, 4) if up_total else 0,
             '跌信号个数': dw_total, '跌信号止盈个数': info_dic["dw_dw"], '跌信号平个数': info_dic["dw_0"], '跌信号止损个数': info_dic["dw_up"],
             '跌信号止盈率': round(info_dic["dw_dw"] / dw_total, 4) if dw_total else 0,
             '跌信号平率': round(info_dic["dw_0"] / dw_total, 4) if dw_total else 0,
             '跌信号止损率': round(info_dic["dw_up"] / dw_total, 4) if dw_total else 0},
            index=[date])
        res_up_down['止盈率'] = profit_ratio
        res_up_down['止损率'] = loss_ratio
        if up_zero:
            res_up_down["涨信号个数"] = 0
        if dw_zero:
            res_up_down["跌信号个数"] = 0

        res_up_down["总止盈率"] = (res_up_down["涨信号止盈个数"] + res_up_down["跌信号止盈个数"]) / (res_up_down["涨信号个数"] + res_up_down["跌信号个数"])
        res_up_down["总止损率"] = (res_up_down["涨信号止损个数"] + res_up_down["跌信号止损个数"]) / (res_up_down["涨信号个数"] + res_up_down["跌信号个数"])
        res_up_down["总平率"] = (res_up_down["涨信号平个数"] + res_up_down["跌信号平个数"]) / (res_up_down["涨信号个数"] + res_up_down["跌信号个数"])
        res_up_down["总信号个数"] = (res_up_down["涨信号个数"] + res_up_down["跌信号个数"])
        res_up_down["信号质量加权"] = (res_up_down["总止盈率"] * 1 - res_up_down["总止损率"] * 2.5 - res_up_down["总平率"] * 0.5)

        res_up_down["模型名称"] = model_name
        res_up_down["标的"] = symbol_name
        res_up_down["预测阈值"] = float(pred_th)
        res_up_down["日期"] = date
        res_up_down["止盈线"] = profit_ratio
        res_up_down["止损线"] = loss_ratio
        res_up_down["跌阈值"] = -pred_th
        res_up_down["涨阈值"] = pred_th
    except Exception as e:
        print(e)
        return pd.DataFrame(columns=['涨信号个数', '涨信号止盈个数', '涨信号平个数', '涨信号止损个数',
                                     '涨信号止盈率', '涨信号平率', '涨信号止损率', '跌信号个数',
                                     '跌信号止盈个数', '跌信号平个数', '跌信号止损个数',
                                     '跌信号止盈率', '跌信号平率', '跌信号止损率', '止盈率', '止损率'])
    return res_up_down

if __name__=="__main__":
    # base_dir = os.path.join("/data/user/quanttest007/013150/exp_result/002594.SZ-002594.SZ_trade_v00")
    # base_dir = os.path.join("/data/user/013150/exp_result/002594.SZ-002594.SZ_trade_v00")
    # TARGET_df_test, T_test, X_train, Y_train, X_valid, Y_valid, X_test, Y_test = pd.read_pickle(
    # os.path.join(base_dir, "dataset/data.pkl"))
    # Y_test_pred, Y_valid_pred = pd.read_pickle(os.path.join(base_dir, "dataset/data1.pkl"))
    #
    # # 计算1：信号个数均值
    # th = 1.0
    # start_date, end_date = str(T_test[0])[:10].replace("-",""), str(T_test[1])[:10].replace("-", "")
    # print("th: ", th, "start_date", start_date, "end_date", end_date)


    # 回测
    import time
    t1 = time.time()
    signal_process_base_dir = "/data/user/016869/exp_result/exp_688012/xgboost_base2/LabelFirstPeak_th10_120s-688012.SH/label_th@1.0-probs_up@0.62-probs_dw@0.62/signal_files_processed"
    res_dict = backtest_oneday(signal_process_base_dir, "2021-01-04")
    print("res_dict:", res_dict, time.time()-t1)
