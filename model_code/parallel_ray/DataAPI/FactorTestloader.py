# -*- coding: utf-8 -*-
# @Time    : 2018/12/10 19:27
# @Author  : 011673
# @File    : FactorTestloader.py
import datetime
from typing import List
import pandas as pd
import os
import numpy as np
import DataAPI.DataToolkit as Dtk
import pickle


def load_con_min_factor(factor_name: str = ..., stock_list: List[str] = ..., start_date: datetime = None,
                end_date: datetime = None, path: str = "S:\\Apollo\\AlphaFactors\\") -> pd.DataFrame:
    """
    获取单个因子数据的矩阵， 要求数据存储为一个因子一个文件，
    命名方式为因子名.h5, 文件中行为时间，列为股票
    :param factor_name: 因子名
    :param stock_list: 股票列表
    :param start_date: 开始日期 类型 datetime
    :param end_date:  结束日期 类型 datetime
    :return: 返回值为DataFrame
    """
    print(path)
    file_name = "{}/{}.pkl".format(path, factor_name)
    if not os.path.isfile(file_name):
        print("could not find Factor file: {}".format(factor_name))
        #  因子不存在
        return np.nan
    with open(file_name, 'rb') as f:
        result = pickle.load(f)
    result = result.loc[start_date.timestamp(): end_date.timestamp()]
    result2 = result.reindex(columns=stock_list)
    return result2


def load_factor(factor_name: str = ..., stock_list: List[str] = ..., start_date: datetime = None,
                end_date: datetime = None, path: str = "S:\\Apollo\\AlphaFactors\\") -> pd.DataFrame:
    """
    获取单个因子数据的矩阵， 要求数据存储为一个因子一个文件，
    命名方式为因子名.h5, 文件中行为时间，列为股票
    :param factor_name: 因子名
    :param stock_list: 股票列表
    :param start_date: 开始日期 类型 datetime
    :param end_date:  结束日期 类型 datetime
    :return: 返回值为DataFrame
    """
    # print(path)
    file_name = "{}/{}.h5".format(path, factor_name)
    if not os.path.isfile(file_name):
        print("could not find Factor file: {}".format(factor_name))
        #  因子不存在
        return np.nan
    data = pd.HDFStore(file_name, mode='r')
    # 存的因子文件是以timestamp为index的，所以直接以index来筛选；这里result获得的是因子文件中所有股票指定时间内的数据
    result = data.select("/factor")
    result = result.loc[start_date.timestamp(): end_date.timestamp()]
    result2 = result.reindex(columns=stock_list)
    data.close()
    return result2


def load_csv_factor(factor_name: str = ..., stock_list: List[str] = ..., start_date: datetime = None,
                    end_date: datetime = None, path: str = "S:\\Apollo\\AlphaFactors\\"):
    file_name = "{}/{}.csv".format(path, factor_name)
    if not os.path.isfile(file_name):
        print("could not find Factor file: {}".format(factor_name))
        #  因子不存在
        return np.nan
    data = pd.read_csv(file_name, index_col=0)
    # 存的因子文件是以timestamp为index的，所以直接以index来筛选；这里result获得的是因子文件中所有股票指定时间内的数据
    result = data.loc[start_date.timestamp(): end_date.timestamp()]
    result2 = result.reindex(columns=stock_list)
    return result2

def load_allgroup_factor(factor_name: str = ..., stock_list: List[str] = ..., start_date: datetime = None,
                    end_date: datetime = None, path: str = "/data/user/666889/Apollo/ThreeGroupFactors/"):
    '''
    load部门所有团队的因子，返回时间戳格式的因子值
    '''
    file_name = "{}/{}.pkl".format(path, factor_name)
    if not os.path.isfile(file_name):
        print("could not find Factor file: {}".format(factor_name))
        #  因子不存在
        return np.nan
    data = pd.read_pickle(file_name)
    result = data.loc[start_date: end_date]
    result2 = result.reindex(columns=stock_list)
    #index为datetime型的Timestamp,将它转为数字型时间戳
    result3 = Dtk.convert_df_index_type(result2, 'timestamp2', 'date_int')
    result4 = Dtk.convert_df_index_type(result3, 'date_int', 'timestamp')
    return result4
