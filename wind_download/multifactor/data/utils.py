# -*- coding: utf-8 -*-


import datetime as dt
import pandas as pd
import os
import numpy as np
from multifactor.IO import IO
from multifactor.IO.IO_enums import *
import time as time
import statsmodels.api as sm
import datetime as dt
from loguru import logger


def get_current_date(new_date_time=18):
    """if current date is not pass new_date_time such as 18 (6pm)
       it will return previous trading day
    """
    current_time = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_date = int(current_time[:8])
    current_hour = int(current_time[9:11])
    fdate_list_dt = IO.read_data([19980101, 20300101], ftype=FType.CALENDAR).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
    nearest_date = min(fdate_list, key=lambda x: abs(x - current_date) if x <= current_date else 100)
    if current_hour < new_date_time and nearest_date == current_date:
        current_date = fdate_list[fdate_list.index(current_date) - 1]
    elif nearest_date < current_date:
        current_date = nearest_date
    elif current_hour >= new_date_time and nearest_date == current_date:
        pass
    return current_date


def date_period_handler(sdate=None, edate=None):
    last_day = get_current_date()
    if sdate is None and edate is None:
        sdate = last_day
        edate = last_day
    if sdate is not None and edate is None:
        edate = last_day
    else:
        fdate_list_dt = IO.read_data([19980101, 20300101], ftype=FType.CALENDAR).index.get_level_values(0)
        fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
        cdate_list = [i for i in fdate_list if i <= min(edate, last_day) and i >= sdate]
        sdate, edate = cdate_list[0], cdate_list[-1]
    return sdate, edate


def check_update_date(sdate=None, edate=None, use_len=None):
    # check_update_date(sdate=None,edate=None)
    use_len = 0 if use_len is None else use_len
    sdate, edate = date_period_handler(sdate, edate)
    fdate_list_dt = IO.read_data([19980101, 20300101], ftype=FType.CALENDAR).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
    cdate_list = [i for i in fdate_list if i >= sdate and i <= edate]
    idx = max(0, fdate_list.index(cdate_list[0]) - use_len)
    sdate_prev = fdate_list[idx]
    return sdate_prev, edate, cdate_list


def get_qtr_list(sdate, edate, num_qtr=None):
    year_list = [str(i) for i in range(2000, 2050)]
    month_date = ['0331', '0630', '0930', '1231']
    date_list_complete = [int(i + j) for i in year_list for j in month_date]
    qtr_list = [i for i in date_list_complete if i <= edate and i >= sdate]
    if len(qtr_list) == 0:
        qtr_list = [i for i in date_list_complete if i <= edate][-1:]
    if num_qtr is not None:
        if isinstance(num_qtr, int):
            start_idx = date_list_complete.index(qtr_list[0])
            pre_qtr = date_list_complete[start_idx - num_qtr:start_idx]
            qtr_list = pre_qtr + qtr_list
            qtr_list.sort()
        else:
            print('input error: num_qtr not integer')
            raise Exception
    return qtr_list


def data_reformat(dat, dat_fig):
    # dat = dat.sort_values([dat_fig['dt']])
    dat[dat_fig['dt']] = dat[dat_fig['dt']].apply(lambda x: dt.datetime.strptime(str(x), '%Y%m%d'))
    if 'Ticker' in dat_fig:
        dat[dat_fig['Ticker']] = dat[dat_fig['Ticker']].astype('str')
        dat = dat.sort_values([dat_fig['dt'], dat_fig['Ticker']])
        dat = dat.set_index([dat_fig['dt'], dat_fig['Ticker']])
        dat.index.names = ['dt', 'Ticker']
    else:
        dat = dat.sort_values(dat_fig['dt'])
        dat = dat.set_index([dat_fig['dt'], 'OBJECT_ID'])
        dat.index.names = ['dt', 'OBJECT_ID']
    format_list = dat.dtypes
    num_list = [i != np.dtype('object') for i in format_list]
    col_list = dat.columns.values
    for i in range(len(num_list)):
        if num_list[i]:
            dat[col_list[i]] = dat[col_list[i]].astype('float64')
    format_list = [type(i) for i in dat.iloc[0, :]]
    return dat
