#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/3/20 9:09
# 获取股票的市场活跃度指标
import pandas as pd
import numpy as np
import sklearn.cluster as skclust
from System.TradingDay import getTradingDay
from xquant.xqutils.helper import multicore_init
from xquant.factordata import FactorData
from HFDataLoader.Config import TICK_SUFFIX
from Constants.CBOND_LIST import CBOND_LIST

def get_tick_volume(lib_name, code, start_date, end_date):
    """ 获取起止日期之间TICK成交量
    """
    fd = FactorData()

    trading_day_list = list(map(str, getTradingDay(int(start_date), int(end_date))))
    tick_volume_list = []
    HBASE_COLUMNS = ["{}_{}".format(TICK_SUFFIX, var) for var in ["Date", "Volume"]]
    for mddate in trading_day_list:
        try:
            tick_df = fd.get_factor_value(lib_name, "{0}_{1}".format(code, TICK_SUFFIX), mddate, HBASE_COLUMNS)
        except:
            tick_df = pd.DataFrame(columns=HBASE_COLUMNS)
        tick_df.columns = list(map(lambda x: x.replace("{0}_".format(TICK_SUFFIX), ""), tick_df.columns.to_list()))
        tick_volume_list.append(tick_df)
    tick_volume = pd.concat(tick_volume_list, axis=0)
    return tick_volume


def get_high_vol_threshold(lib_name, code_list, start_date, end_date, lookback=None, lag=200, method="Cluster"):
    """"""
    high_vol_dict = {}

    for code in code_list:

        high_vol = 0.

        ### 获取起止日期之间TICK成交量
        tick_volume = get_tick_volume(lib_name, code, start_date, end_date)

        if tick_volume.empty:
            print(" TICK Volume Data Not Available, Set Default Value: 0 ")

        else:
            trading_day_list = sorted(list(set(tick_volume["Date"].tolist())))
            if lookback is None:
                valid_date_list = trading_day_list
            else:
                if len(trading_day_list) < lookback:
                    print("Effective Trading Days: {} Less Than LookBack: {}".format(len(trading_day_list), lookback))
                    valid_date_list = trading_day_list
                else:
                    valid_date_list = trading_day_list[-lookback:]

            volume_holder = []
            for date in valid_date_list:
                tick_df = tick_volume[tick_volume["Date"] == date]
                ma_volume = np.log(tick_df['Volume'].astype(np.float64) + 10).rolling(lag).mean()[lag:]
                volume_holder.append(ma_volume.values[None].T)

            volume_array = np.vstack(volume_holder)

            if method == "Cluster":
                a = skclust.KMeans(n_clusters=2).fit(volume_array)
                ub = volume_array[a.labels_ == a.cluster_centers_.argmax()].min()
                lb = volume_array[a.labels_ == a.cluster_centers_.argmin()].max()
                high_vol = int((ub + lb) / 2 * 10) / 10

            elif method == "Median":
                median = np.nanmedian(volume_array)
                high_vol = int(median * 10) / 10

            print("{}-{}-{} High Vol Threshold: {} ".format(code, valid_date_list[0], valid_date_list[-1], high_vol))

        high_vol_dict.update({code: high_vol})

    return high_vol_dict


def get_high_vol_speed(lib_name, code_list, start_date, end_date, lookback=None, lag=200, method="Cluster", process_num=20):
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
        result = pool.apply_async(get_high_vol_threshold, (lib_name, para_split[ii], start_date, end_date, lookback, lag, method, ))
        multiProcessResult.append(result)
    pool.close()
    pool.join()

    high_vol_dict = {}
    for result in multiProcessResult:
        high_vol_dict.update(result.get())

    return high_vol_dict


if __name__=="__main__":
    lib_name = "CBDataLib"
    code_list = CBOND_LIST
    start_date = "20190101"
    end_date = "20191031"
    lookback = None
    lag = 200
    method = "Cluster"
    # high_vol = get_high_vol_threshold(lib_name, code_list, start_date, end_date)
    high_vol = get_high_vol_speed(lib_name, code_list, start_date, end_date)
    print(high_vol)








