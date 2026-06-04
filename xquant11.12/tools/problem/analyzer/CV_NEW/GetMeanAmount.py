#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/3/20 9:09
# 获取股票过去一段时间的活跃度指标和平均成交额
import pandas as pd
from System.TradingDay import getTradingDay, getNDaysOff
from xquant.xqutils.helper import multicore_init
from xquant.factordata import FactorData
from CONFIG import TICK_SUFFIX


def get_tick_amount(lib_name, code, start_date, end_date, lookback, max_query=60):
    """ 获取起止日期之间TICK成交量
    """
    HBASE_COLUMNS = ["{}_{}".format(TICK_SUFFIX, var) for var in ["Date", "Amount"]]

    fd = FactorData()

    tick_amount_list = []

    ### 取start_date前lookback个交易日之间的成交额
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
            tick_amount_list.append(tick_df)
            back_count += 1

        curr_date_int = pre_date_int
        query_num += 1

    if tick_amount_list:
        tick_amount_list = tick_amount_list[::-1]

    if len(tick_amount_list) < lookback:
        if query_num >= max_query:
            print(" Reach Maximum Query Times, But NOT Enough Trade Dates: {}-{}-{} ".format(code, start_date, end_date))

    ### 获取start_date-end_date之间的成交额
    trading_day_list = list(map(str, getTradingDay(int(start_date), int(end_date))))
    for mddate in trading_day_list:
        try:
            tick_df = fd.get_factor_value(lib_name, "{0}_{1}".format(code, TICK_SUFFIX), mddate, HBASE_COLUMNS)
        except:
            tick_df = pd.DataFrame(columns=HBASE_COLUMNS)
        tick_df.columns = list(map(lambda x: x.replace("{0}_".format(TICK_SUFFIX), ""), tick_df.columns.to_list()))
        if not tick_df.empty:
            tick_amount_list.append(tick_df)

    if tick_amount_list:
        tick_amount = pd.concat(tick_amount_list, axis=0)
    else:
        tick_amount = pd.DataFrame(columns=["Date", "Amount"])

    return tick_amount

def get_mean_amount(lib_name, code_list, start_date, end_date, lookback=20):
    """"""
    mean_amount_dict = {}

    for code in code_list:

        code_amount = {}

        ### 获取起止日期之间TICK成交量
        tick_amount = get_tick_amount(lib_name, code, start_date, end_date, lookback)

        if tick_amount.empty:
            print(" Tick Amount Data Not Available, Set Default Value: 0 ")

        else:
            daily_amount = tick_amount.groupby("Date").sum()
            ma_amount = daily_amount.rolling(lookback).mean()
            ma_amount = ma_amount.shift().loc[start_date:end_date]
            code_amount = ma_amount.to_dict()["Amount"]

        mean_amount_dict.update({code: code_amount})

    return mean_amount_dict


def get_mean_amount_speed(lib_name, code_list, start_date, end_date, lookback=20, process_num=20):
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
        result = pool.apply_async(get_mean_amount, (lib_name, para_split[ii], start_date, end_date, lookback, ))
        multiProcessResult.append(result)
    pool.close()
    pool.join()

    mean_amount_dict = {}
    for result in multiProcessResult:
        mean_amount_dict.update(result.get())

    return mean_amount_dict


if __name__=="__main__":
    lib_name = "XHFDataLib"
    code_list = ["000001.SZ", "000725.SZ"]
    start_date = "20200101"
    end_date = "20200301"
    lookback = None
    amount_stat = get_mean_amount_speed(lib_name, code_list, start_date, end_date)
    amount_stat = get_mean_amount(lib_name, code_list, start_date, end_date)
    print(amount_stat)








