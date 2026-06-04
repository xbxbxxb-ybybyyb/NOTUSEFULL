#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/7/30 13:29
import datetime as dt
import numpy as np
import pandas as pd
from xquant.factordata import FactorData
fa = FactorData()

SIGNAL_HBASE_COLUMNS = ['timestamp', 'ticktime', 'prediction1minLong', 'prediction1minShort', 'prediction2minLong', 'prediction2minShort',
                 'prediction5minLong', 'prediction5minShort']
SIGNAL_CLEAN_COLUMNS = ['timestamp', 'ticktime', 'date', 'prediction1minLong', 'prediction1minShort', 'prediction2minLong',
                        'prediction2minShort', 'prediction5minLong', 'prediction5minShort']
SIGNAL_TARGET_COLUMNS = ['Timestamp', 'Ticktime', 'Date', '1minLong', '1minShort', '2minLong', '2minShort', '5minLong', '5minShort']


def average_special_time(data, time1, time2, time3):
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

def pre_process_single(data):
    column_long = data['1minLong'] + data['2minLong'] + data['5minLong']
    column_long /= 3
    data = data.assign(ave_long=column_long)

    column_short = data['1minShort'] + data['2minShort'] + data['5minShort']
    column_short /= 3
    data = data.assign(ave_short=column_short)

    data['Ticktime'] = data['Ticktime'].apply(lambda x: dt.datetime.strptime(x, '%H:%M:%S').time())
    data = average_special_time(data, dt.time(11, 25, 0), dt.time(11, 28, 0), dt.time(11, 30, 0))
    data = average_special_time(data, dt.time(14, 52, 0), dt.time(14, 55, 0), dt.time(14, 57, 0))
    return data

def get_code_signal(lib_name, code, date):
    """"""
    try:
        tick_df = fa.get_factor_value(lib_name, "{0}".format(code), date, SIGNAL_HBASE_COLUMNS)
        tick_df["date"] = tick_df["timestamp"].apply(
            lambda x: dt.datetime.fromtimestamp(x).strftime("%Y%m%d %H%M%S%f").split(" ")[0])
        tick_df = tick_df.reindex(columns=SIGNAL_CLEAN_COLUMNS)
        tick_df.columns = SIGNAL_TARGET_COLUMNS
    except:
        tick_df = pd.DataFrame(columns=SIGNAL_TARGET_COLUMNS)
    return tick_df

def collect_prediction_signal(lib_name, code, date):
    signal_df = get_code_signal(lib_name, code, date)
    if signal_df.empty:
        print(" Empty Signal : {}-{} ".format(code, date))
        return pd.DataFrame(columns=SIGNAL_TARGET_COLUMNS + ["ave_long", "ave_short"])
    else:
        signal_df = pre_process_single(signal_df)
        return signal_df

def compute_signal_corr(bt_signal, prod_signal):
    common_timestamp = list(set(bt_signal["Timestamp"].tolist()).intersection(prod_signal["Timestamp"].tolist()))
    if len(common_timestamp) == 0:
        return np.nan, np.nan
    bt_signal = bt_signal[bt_signal["Timestamp"].isin(common_timestamp)].reset_index(drop=True)
    prod_signal = prod_signal[prod_signal["Timestamp"].isin(common_timestamp)].reset_index(drop=True)

    bt_signal_m = bt_signal[bt_signal["Ticktime"] <= dt.time(10, 00, 0)]
    bt_signal_a = bt_signal[bt_signal["Ticktime"] > dt.time(10, 00, 0)]
    prod_signal_m = prod_signal[prod_signal["Ticktime"] <= dt.time(10, 00, 0)]
    prod_signal_a = prod_signal[prod_signal["Ticktime"] > dt.time(10, 00, 0)]
    if bt_signal_m.empty or bt_signal_a.empty:
        return np.nan, np.nan
    morning_corr = bt_signal_m[["ave_long", "ave_short"]].corrwith(prod_signal_m[["ave_long", "ave_short"]]).mean()
    afternoon_corr = bt_signal_a[["ave_long", "ave_short"]].corrwith(prod_signal_a[["ave_long", "ave_short"]]).mean()
    return (round(morning_corr, 3), bt_signal_m.shape[0]), (round(afternoon_corr, 3), bt_signal_a.shape[0])

def get_signal_corr(bt_lib, prod_lib, code_list, date):

    corr_dict = {}
    for code in code_list:
        bt_signal = collect_prediction_signal(bt_lib, code, date)
        prod_signal = collect_prediction_signal(prod_lib, code, date)
        morning_corr, afternoon_corr = compute_signal_corr(bt_signal, prod_signal)
        corr_dict.update({code: {"Corr_BeforeTen": morning_corr, "Corr_AfterTen": afternoon_corr}})
    corr_df = pd.DataFrame(corr_dict).T
    return corr_df


if __name__ == "__main__":
    bt_lib = "EasyModelSignals"
    prod_lib =  "ProductionEasySignals"
    code_list = ["600519.SH", "000001.SZ"]
    date = "20200728"
    corr_df = get_signal_corr(bt_lib, prod_lib, code_list, date)
    print(corr_df)






