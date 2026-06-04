#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/3/20 9:09
# 获取股票非对称开平仓阈值的最优偏移量
import pandas as pd
import numpy as np
import datetime as dt
from System.GetTradingDay import getTradingDay
from xquant.xqutils.helper import multicore_init
from xquant.factordata import FactorData


SIGNAL_HBASE_COLUMNS = ['timestamp', 'ticktime', 'prediction1minLong', 'prediction1minShort', 'prediction2minLong', 'prediction2minShort',
                 'prediction5minLong', 'prediction5minShort']
SIGNAL_CLEAN_COLUMNS = ['timestamp', 'ticktime', 'date', 'prediction1minLong', 'prediction1minShort', 'prediction2minLong',
                        'prediction2minShort', 'prediction5minLong', 'prediction5minShort']
SIGNAL_TARGET_COLUMNS = ['Timestamp', 'Ticktime', 'Date', '1minLong', '1minShort', '2minLong', '2minShort', '5minLong', '5minShort']


def average_special_time(data: pd.DataFrame, time1: dt.time, time2: dt.time, time3: dt.time) -> pd.DataFrame:
    filter1 = (data['Ticktime'] >= time1) & (data['Ticktime'] < time2)
    index1 = data.loc[filter1, 'Ticktime'].index
    ave_long1 = (data.loc[index1, '1minLong'] + data.loc[index1, '2minLong']) / 2
    ave_short1 = (data.loc[index1, '1minShort'] + data.loc[index1, '2minShort']) / 2
    data.loc[index1, 'ave_long'] = ave_long1
    data.loc[index1, 'ave_short'] = ave_short1

    filter2 = (data['Ticktime'] >= time2) & (data['Ticktime'] < time3)
    index2 = data.loc[filter2, 'Ticktime'].index
    ave_long2 = data.loc[index2, '1minLong']
    ave_short2 = data.loc[index2, '1minShort']
    data.loc[index2, 'ave_long'] = ave_long2
    data.loc[index2, 'ave_short'] = ave_short2
    return data

def combine_signal(tick_signal):
    """ 合成1, 2, 5 minute信号值
    """
    if tick_signal.empty:
        signal_df = pd.DataFrame(columns=tick_signal.columns.tolist() + ["ave_long", "ave_short"])

    else:
        trading_day_list = sorted(list(set(tick_signal["Date"].tolist())))
        signal_df_list = []
        for date in trading_day_list:
            signal_df = tick_signal[tick_signal["Date"] == date]

            column_long = signal_df['1minLong'] + signal_df['2minLong'] + signal_df['5minLong']
            column_long /= 3
            signal_df = signal_df.assign(ave_long=column_long)

            column_short = signal_df['1minShort'] + signal_df['2minShort'] + signal_df['5minShort']
            column_short /= 3
            signal_df = signal_df.assign(ave_short=column_short)

            signal_df = average_special_time(signal_df, dt.time(11, 25, 0), dt.time(11, 28, 0), dt.time(11, 30, 0))
            signal_df = average_special_time(signal_df, dt.time(14, 52, 0), dt.time(14, 55, 0), dt.time(14, 57, 0))

            signal_df_list.append(signal_df)

        signal_df = pd.concat(signal_df_list, axis=0)

    return signal_df

def get_inference_signal(lib_name, code, start_date, end_date):
    """ 获取起止日期之间的信号值
    """
    fd = FactorData()
    trading_day_list = list(map(str, getTradingDay(int(start_date), int(end_date))))
    tick_signal_list = []
    for mddate in trading_day_list:
        try:
            tick_df = fd.get_factor_value(lib_name, "{0}".format(code), mddate, SIGNAL_HBASE_COLUMNS)
            tick_df['ticktime'] = tick_df['ticktime'].apply(lambda x: dt.datetime.strptime(x, '%H:%M:%S').time())
            tick_df["date"] = tick_df["timestamp"].apply(lambda x: dt.datetime.fromtimestamp(x).strftime("%Y%m%d %H%M%S%f").split(" ")[0])
            tick_df = tick_df.reindex(columns=SIGNAL_CLEAN_COLUMNS)
            tick_df.columns = SIGNAL_TARGET_COLUMNS
        except:
            tick_df = pd.DataFrame(columns=SIGNAL_TARGET_COLUMNS)
        tick_signal_list.append(tick_df)
    tick_signal = pd.concat(tick_signal_list, axis=0)

    return tick_signal

def moving_average(var, window=3):
    varsum = np.nancumsum(var, dtype=float)
    varsum[window:] = varsum[window:] - varsum[:-window]
    return varsum[window-1:] / window

def compute_signal_diff(threshold, all_bid_signal, all_ask_signal, shift, plot=False):
    """"""
    ask_mean = []
    bid_mean = []

    for ask_signal, bid_signal in zip(all_ask_signal, all_bid_signal):
        ask = moving_average(np.array(ask_signal) < threshold + shift, 200)
        bid = moving_average(np.array(bid_signal) > - threshold, 200)
        ask_mean.append(np.mean(ask))
        bid_mean.append(np.mean(bid))

    ask_mean = np.array(ask_mean)
    bid_mean = np.array(bid_mean)

    if plot is True:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(8, 4))
        plt.plot(ask_mean, color='red', label='ask < %s' % str(threshold + shift) )
        plt.plot(bid_mean, color='blue', label='bid > %s' % str(- threshold) )
        plt.legend()
        plt.ylabel('Proprotion')
        plt.show()

    return np.mean(abs(ask_mean - bid_mean))

def search_opt_shift(code, all_bid_signal, all_ask_signal):
    """"""
    is_success = False
    opt_shift = 0
    try:
        ask_list = []
        bid_list = []
        for ask_date_list, bid_date_list in zip(all_ask_signal, all_bid_signal):
            ask_list.extend(ask_date_list)
            bid_list.extend(bid_date_list)

        th1 = np.percentile(ask_list, 1)
        th2 = np.percentile(bid_list, 99)

        if abs(th1) < abs(th2):
            threshold = th1
        else:
            threshold = - th2

        signal_diff = []
        for shift in range(0, 10):
            signal_diff.append(compute_signal_diff(threshold, all_bid_signal, all_ask_signal, shift / 10))

        opt_shift = signal_diff.index(min(signal_diff)) / 10

        is_success = True

    except:
        print("Search Optimal Signal Fail: {}".format(code))

    return opt_shift, is_success

def get_optimal_shift(lib_name, code_list, start_date, end_date, lookback=None):
    """"""
    opt_shift_dict = {}

    for code in code_list:

        ### 获取原始预测信号
        tick_signal = get_inference_signal(lib_name, code, start_date, end_date)

        ### 信号合成
        signal_df = combine_signal(tick_signal)


        if signal_df.empty:
            print("No Signal Data: {}".format(code))
            continue
        else:
            trading_day_list = sorted(list(set(signal_df["Date"].tolist())))

            if lookback is None:
                valid_date_list = trading_day_list
            else:
                if len(trading_day_list) < lookback:
                    print("Effective Trading Days: {} Less Than LookBack: {}".format(len(trading_day_list), lookback))
                    valid_date_list = trading_day_list
                else:
                    valid_date_list = trading_day_list[-lookback:]

            valid_signal_df = signal_df[signal_df["Date"].isin(valid_date_list)]

            all_bid_signal = []
            all_ask_signal = []
            for date in valid_date_list:
                bid_signal = valid_signal_df[valid_signal_df["Date"]==date]["ave_long"].tolist()
                ask_signal = valid_signal_df[valid_signal_df["Date"]==date]["ave_short"].tolist()
                all_bid_signal.append(bid_signal)
                all_ask_signal.append(ask_signal)

            opt_shift, is_success = search_opt_shift(code, all_bid_signal, all_ask_signal)

        opt_shift_dict.update({code: opt_shift})

    return opt_shift_dict

def get_optimal_shift_speed(lib_name, code_list, start_date, end_date, lookback=None, process_num=20):
    import multiprocessing as mp

    process_num = min(len(code_list), process_num)
    assert multicore_init() == True
    pool = mp.Pool(processes=process_num)

    para_split = []

    for ii in range(process_num):
        para_split.append([])

    count = 0
    for ii in range(len(code_list)):
        para_split[count].append(code_list[ii])
        count = count + 1
        if count >= process_num:
            count = 0

    multiProcessResult = []
    for ii in range(para_split.__len__()):
        result = pool.apply_async(get_optimal_shift, (lib_name, para_split[ii], start_date, end_date, lookback, ))
        multiProcessResult.append(result)
    pool.close()
    pool.join()

    opt_shift_dict = {}
    for result in multiProcessResult:
        opt_shift_dict.update(result.get())

    return opt_shift_dict



if __name__=="__main__":
    lib_name = "SeparateModelSignals"
    code_list = ["000001.SZ"]
    start_date = "20200102"
    end_date = "20200102"
    lookback = None
    opt_shift = get_optimal_shift(lib_name, code_list, start_date, end_date, lookback=lookback)
    # opt_shift = get_optimal_shift_speed(lib_name, code_list, start_date, end_date, lookback=lookback)
    print(opt_shift)