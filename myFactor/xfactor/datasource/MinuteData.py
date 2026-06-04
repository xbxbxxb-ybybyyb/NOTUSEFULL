import os

import pandas as pd
from loguru import logger

import settings


# 读取历史分钟数据文件
def get_history_data(col, begin_date, last_date, stock_list, cache=None):
    month_list = list(__get_month_list(begin_date, last_date))
    if "-index" in col:
        data_category = "index"
        col_name = col.split("-")[0]
    else:
        data_category = "stock"
        col_name = col[:-7]
    minute_data_path = os.path.join(settings.MINUTE_DATA_PATH, data_category, col_name)
    res_list = []
    for month in month_list:
        file_name = "{}_{}.pkl".format(month, col_name)
        pickle_file = os.path.join(minute_data_path, file_name)
        if cache and pickle_file in cache:
            try:
                df = pd.read_pickle(cache[pickle_file])
            except Exception as e:
                logger.error("缓存文件读取失败： source_file={}, target_file={}".format(pickle_file, cache[pickle_file]))
                df = pd.read_pickle(pickle_file)
        else:
            df = pd.read_pickle(pickle_file)
        res_list.append(df)
    minute_data = pd.concat(res_list, axis=0, sort=False)
    minute_data = minute_data.loc[begin_date: last_date]
    # if data_category == "stock":
    #     minute_data = minute_data.reindex(columns=stock_list)
    return minute_data


# 读取实时分钟数据文件
def get_realtime_data(col, realtime_minute_path, stock_list):
    if "-index" in col:
        data_category = "index"
        col_name = col.split("-")[0]
    else:
        data_category = "stock"
        col_name = col[:-7]
    minute_data_path = os.path.join(realtime_minute_path, data_category)
    file_name = "{}.pkl".format(col_name)
    minute_data = pd.read_pickle(os.path.join(minute_data_path, file_name))
    # if data_category == "stock":
    #     minute_data = minute_data.reindex(columns=stock_list)
    return minute_data


# 分钟线是按月存的pickle，读取分钟线需要获取所需月份
def __get_month_list(begin_date, last_date):
    begin_month = begin_date[:6]
    last_month = last_date[:6]
    while begin_month <= last_month:
        yield begin_month
        if int(begin_month[-2:]) >= 12:
            begin_month = str(int(begin_month[:4]) + 1) + str("01")
        else:
            begin_month = str(int(begin_month) + 1)


def filter_data_type(depend_data_type_list):
    return list(
        filter(lambda x: "Basic_factor." in x and "_minute" in x, depend_data_type_list))
