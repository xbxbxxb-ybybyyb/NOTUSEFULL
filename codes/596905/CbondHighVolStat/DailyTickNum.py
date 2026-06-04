#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/4/13 11:18
from Constants.CBOND_LIST import CBOND_LIST
from HFDataLoader.Config import TICK_SUFFIX
import json
import numpy as np
import pandas as pd
from xquant.factordata import FactorData
from xquant.bonddata import BondData
from xquant.xqutils.helper import multicore_init
from System.TradingDay import getTradingDay
import sklearn.cluster as skclust


def get_tick_volume(lib_name, code, start_date, end_date):
    """ 获取起止日期之间每日TICK成交量和TICK数目
    """
    fd = FactorData()

    tick_info = pd.DataFrame()
    volume_list = []
    trading_day_list = list(map(str, getTradingDay(int(start_date), int(end_date))))
    HBASE_COLUMNS = ["{}_{}".format(TICK_SUFFIX, var) for var in ["Date", "Time", "Volume", "IsMock"]]
    for mddate in trading_day_list:
        try:
            tick_df = fd.get_factor_value(lib_name, "{0}_{1}".format(code, TICK_SUFFIX), mddate, HBASE_COLUMNS)
        except:
            tick_df = pd.DataFrame(columns=HBASE_COLUMNS)
        tick_df.columns = list(map(lambda x: x.replace("{0}_".format(TICK_SUFFIX), ""), tick_df.columns.to_list()))
        tick_df = tick_df[tick_df["IsMock"]==0]
        if tick_df.empty:
            continue
        volume_list.append(tick_df[["Date", "Volume"]])
        tick_volume = tick_df["Volume"].sum()
        tick_num = tick_df.shape[0]

        daily_df = pd.DataFrame([tick_volume, tick_num]).T
        daily_df.columns = ["Volume", "TickNum"]
        daily_df.index = [mddate]
        tick_info = pd.concat([tick_info, daily_df], axis=0)

    if len(volume_list) == 0:
        volume_df = pd.DataFrame(columns=["Date", "Volume"])
    else:
        volume_df = pd.concat(volume_list, axis=0)

    return volume_df, tick_info

def get_high_vol(code, tick_volume, lookback=None, lag=200, method="Cluster"):
    volume_holder = []
    trading_day_list = sorted(list(set(tick_volume["Date"].tolist())))
    for date in trading_day_list:
        tick_df = tick_volume[tick_volume["Date"] == date]
        smooth = min(lag, tick_df.shape[0])
        ma_volume = np.log(tick_df['Volume'].astype(np.float64) + 10).rolling(smooth).mean()[smooth:]
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

    print("{}-{}-{} High Vol Threshold: {} ".format(code, trading_day_list[0], trading_day_list[-1], high_vol))

    return high_vol


def get_volume_stat(lib_name, code_list, start_date, end_date, lookback=None, lag=200, method="Cluster"):
    local_path = "/data/user/015629/CBondLogDecipher/VolumeStat/"

    high_vol_dict = {}

    for code in code_list:
        volume_df, tick_info = get_tick_volume(lib_name, code, start_date, end_date)
        if volume_df.empty:
            high_vol = None
        else:
            high_vol = get_high_vol(code, volume_df, lookback=lookback, lag=lag, method=method)

            file_name = "{}_{}_{}.pkl".format(code, start_date, end_date)
            tick_info.to_pickle(local_path + file_name)

        high_vol_dict.update({code: high_vol})

    return high_vol_dict

def get_volume_stat_speed(lib_name, code_list, start_date, end_date, lookback=None, lag=50, method="Cluster", process_num=20):
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
        result = pool.apply_async(get_volume_stat, (lib_name, para_split[ii], start_date, end_date, lookback, lag, method, ))
        multiProcessResult.append(result)
    pool.close()
    pool.join()

    high_vol_dict = {}
    for result in multiProcessResult:
        high_vol_dict.update(result.get())

    local_path = "/data/user/015629/CBondLogDecipher/VolumeStat/"
    with open(local_path + "HighVol.json", "w") as f:
        json.dump(high_vol_dict, f)

    high_vol_df = pd.Series(high_vol_dict).to_frame()
    high_vol_df.columns = ["HighVol"]
    high_vol_df.to_csv(local_path + "HighVol_Lag{}.csv".format(lag))

    return high_vol_dict

def get_cbond_list(date):
    bd = BondData()
    cbond_list = bd.get_bond_set(date, "kzz")
    return cbond_list


if __name__ == "__main__":
    lib_name = "CBDataLib"
    #cbond_list = get_cbond_list("20200410")
    cbond_list = CBOND_LIST
    code_list = cbond_list
    start_date = "20190101"
    end_date = "20191030"
    high_vol_dict = get_volume_stat_speed(lib_name, code_list, start_date, end_date)
    print(high_vol_dict)

