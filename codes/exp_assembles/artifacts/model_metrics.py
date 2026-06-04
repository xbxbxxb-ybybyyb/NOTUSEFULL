import pandas as pd
import numpy as np
import json
from xquant.factordata import FactorData
import os
import datetime
from artifacts import online_model, parse_format
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
    print('预测标签阈值 {:.6f}, 真实标签阈值 {:.6f}: key_symbol_acc {:.3f}, key_class_acc {:.3f}'.format(
        pred_th, true_th, key_symbol_acc, key_class_acc))
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

        print('top_{}_symbol_acc: {:.3f}; bottom_{}_symbol_acc: {:.3f}'.format(
            k, top_k_acc, k, bottom_k_acc))
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