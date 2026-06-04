#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/6/2 16:48
import os
import datetime as dt
import numpy as np
from Utils.TradingDay import getTradingDay
from xquant.compute.sparkmr import remote_print


def get_code_type(code):
    if is_cbond_code(code):
        return "CBOND"
    else:
        return "STOCK"

def is_cbond_code(code):
    if code.endswith(".SH"):
        if code.startswith("100") or code.startswith("110") or code.startswith("113") or code.startswith("118") or code.startswith("111"):
            return True
    elif code.endswith(".SZ"):
        if code.startswith("12") or code == "117103.SZ":
            return True
    return False

def get_trading_day(start_date, end_date):
    if not isinstance(start_date, int):
        start_date = int(start_date)
    if not isinstance(end_date, int):
        end_date = int(end_date)
    trade_dates = getTradingDay(start_date, end_date)
    if len(trade_dates) == 0:
        return []
    else:
        trade_dates = sorted(list(map(lambda date_int: str(date_int), trade_dates)))
    return trade_dates

def split_calc_date_into_group(calc_date_list, max_date_num_per_task=20):
    # 按照天数将需要计算的时间段进行分组，例如，每20个交易日分一组
    group = []
    size = len(calc_date_list)
    from_index = 0
    while from_index < size:
        group.append(calc_date_list[from_index: min(size, from_index + max_date_num_per_task)])
        from_index += max_date_num_per_task
    return group

def MyPrint(x_str):
    return remote_print(x_str) if "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ else print(x_str)

def generate_divide_indexes(timestamp_values):
    time_list = [dt.datetime.fromtimestamp(x).strftime("%Y%m%d%H%M%S") for x in timestamp_values]
    date, hour, div_indexes = time_list[0][:8], int(time_list[0][8:10]), []
    for index, time in enumerate(time_list):
        cur_date, cur_hour = time[:8], int(time[8:10])
        if cur_date != date:
            div_indexes.append(index)
        elif (hour < 12) and (cur_hour > 12):
            div_indexes.append(index)
        date = cur_date
        hour = cur_hour

    div_indexes.append(len(time_list) - 1) # Append Last One Index

    return np.array(div_indexes)

def split_calc_index_into_group(index_list, split_num):
    avg = len(index_list) / float(split_num)
    group = []
    last = 0
    while last < len(index_list):
        group.append(index_list[int(last):int(last + avg)])
        last += avg
    return group





