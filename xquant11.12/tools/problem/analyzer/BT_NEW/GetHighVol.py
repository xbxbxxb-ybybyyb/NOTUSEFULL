#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/3/20 9:09
# 获取股票过去一段时间的活跃度指标和平均成交额
import pandas as pd
import numpy as np
import sklearn.cluster as skclust
from System.TradingDay import getTradingDay, getNDaysOff
from xquant.xqutils.helper import multicore_init
from xquant.factordata import FactorData
from CONFIG import TICK_SUFFIX


def get_tick_volume(lib_name, code, start_date, end_date, lookback, max_query=90):
    """ 获取起止日期之间TICK成交量
    """
    HBASE_COLUMNS = ["{}_{}".format(TICK_SUFFIX, var) for var in ["Date", "Volume"]]

    fd = FactorData()

    tick_volume_list = []

    ### Step 1: 取start_date前lookback个交易日之间的成交额
    start_date_int = int(start_date)
    curr_date_int = start_date_int
    back_count = 0
    query_num = 0
    while(back_count < lookback and query_num <= max_query):
        pre_date_int = getNDaysOff(curr_date_int, 1)
        try:
            tick_df = fd.get_factor_value(lib_name, "{0}_{1}".format(code, TICK_SUFFIX), str(pre_date_int), HBASE_COLUMNS)
        except:
            tick_df = pd.DataFrame(columns=HBASE_COLUMNS)
        tick_df.columns = list(map(lambda x: x.replace("{0}_".format(TICK_SUFFIX), ""), tick_df.columns.to_list()))

        if not tick_df.empty:
            tick_volume_list.append(tick_df)
            back_count += 1

        curr_date_int = pre_date_int
        query_num += 1

    if tick_volume_list:
        tick_volume_list = tick_volume_list[::-1]

    if len(tick_volume_list) < lookback:
        if query_num >= max_query:
            print(" Reach Maximum Query Times, But NOT Enough Trade Dates: {}-{}-{}".format(code, start_date, end_date))

    ### Step 2: 获取start_date-end_date之间的成交额
    trading_day_list = list(map(str, getTradingDay(int(start_date), int(end_date))))
    for mddate in trading_day_list:
        try:
            tick_df = fd.get_factor_value(lib_name, "{0}_{1}".format(code, TICK_SUFFIX), mddate, HBASE_COLUMNS)
        except:
            tick_df = pd.DataFrame(columns=HBASE_COLUMNS)
        tick_df.columns = list(map(lambda x: x.replace("{0}_".format(TICK_SUFFIX), ""), tick_df.columns.to_list()))
        if not tick_df.empty:
            tick_volume_list.append(tick_df)

    if tick_volume_list:
        tick_volume = pd.concat(tick_volume_list, axis=0)
    else:
        tick_volume = pd.DataFrame(columns=["Date", "Volume"])

    return tick_volume


def get_high_vol(lib_name, code_list, start_date, end_date, lookback=20, lag=200, method="Cluster"):
    """"""
    high_vol_dict = {}

    for code in code_list:

        code_high_vol = {}

        ### 获取起止日期之间TICK成交量
        tick_volume = get_tick_volume(lib_name, code, start_date, end_date, lookback)

        if tick_volume.empty:
            print(" TICK Volume Data Not Available, Set Default Value: 0 ")

        else:
            date_list = sorted(list(set(tick_volume["Date"].tolist())))
            volume_holder = {}
            for date in date_list:
                tick_df = tick_volume[tick_volume["Date"] == date]
                ma_volume = np.log(tick_df["Volume"].astype(np.float64) + 100).rolling(lag).mean()[lag:]
                volume_holder.update({date: ma_volume.values[None].T})

            valid_date_list = [date for date in date_list if start_date <= date <= end_date]
            for date in valid_date_list:
                volume_array_list = []
                sub_end_date = getNDaysOff(int(date), 1)
                sub_start_date = getNDaysOff(sub_end_date, lookback)
                sub_date_list = [date_ for date_ in date_list if str(sub_start_date) <= date_ <= str(sub_end_date)]
                if len(sub_date_list) > 0:
                    for date_ in sub_date_list:
                        volume_array_list.append(volume_holder.get(date_))

                    volume_array = np.vstack(volume_array_list)
                    high_vol = calculate_high_vol(volume_array, method)

                else:
                    high_vol = 0.

                code_high_vol.update({date: high_vol})

        high_vol_dict.update({code: code_high_vol})

    return high_vol_dict

def calculate_high_vol(volume_array, method="Cluster"):
    """计算活跃度指标"""
    high_vol = 0.

    if method == "Cluster":
        a = skclust.KMeans(n_clusters=2).fit(volume_array)
        ub = volume_array[a.labels_ == a.cluster_centers_.argmax()].min()
        lb = volume_array[a.labels_ == a.cluster_centers_.argmin()].max()
        high_vol = int((ub + lb) / 2 * 10) / 10

    elif method == "Median":
        median = np.nanmedian(volume_array)
        high_vol = int(median * 10) / 10

    return high_vol


def get_high_vol_speed(lib_name, code_list, start_date, end_date, lookback=20, lag=200, method="Cluster", process_num=20):
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
        result = pool.apply_async(get_high_vol, (lib_name, para_split[ii], start_date, end_date, lookback, lag, method, ))
        multiProcessResult.append(result)
    pool.close()
    pool.join()

    high_vol_dict = {}
    for result in multiProcessResult:
        high_vol_dict.update(result.get())

    return high_vol_dict


if __name__=="__main__":
    lib_name = "XHFDataLib"
    code_list = ["000001.SZ", "000725.SZ"]
    start_date = "20200101"
    end_date = "20200301"
    lookback = 20
    lag = 200
    method = "Cluster"
    # high_vol = get_high_vol(lib_name, code_list, start_date, end_date)
    high_vol = get_high_vol_speed(lib_name, code_list, start_date, end_date)
    print(high_vol)








