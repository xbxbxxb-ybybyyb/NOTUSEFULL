# coding:utf-8
from tquant.strategy.day_factor_backtest_new.IO.IO import *
import tquant.strategy.day_factor_backtest_new.util.dt as tdt
import pickle
import datetime as dt
import pandas as pd
import numpy as np
from tquant import BasicData

bd = BasicData()


def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func

    return decorate


@static_vars(tic=dt.datetime.now())
def pprint(*args, **kwargs):
    print(('%.3fs <- prev msg: ' % (dt.datetime.now() - pprint.tic).total_seconds()).rjust(22), *args, **kwargs)
    pprint.tic = dt.datetime.now()


def get_trading_date_range_old(start_date, end_date, dfreq=DFreq.DAILY, dtype=DType.STOCK, mkttype=MktType.CHINA,
                               dsource=DSource.HTSC, alt=None):
    pd_trading_dates = read_data([start_date, end_date], dfreq=dfreq, dtype=dtype, mkttype=mkttype, dsource=dsource,
                                 ftype=FType.CALENDAR, alt=alt)
    return pd_trading_dates.index.get_level_values('dt').tolist()


# bie
def get_trading_date_range(start_date, end_date):
    """
    获取交易日期列表
    :param start_date: str类型
    :param end_date: str类型
    :return:
    """
    if isinstance(start_date, dt.datetime):
        start_date = dt.datetime.strftime(start_date, '%Y%m%d')
    else:
        assert len(str(start_date)) == 8
    if isinstance(end_date, dt.datetime):
        end_date = dt.datetime.strftime(end_date, '%Y%m%d')
    else:
        assert len(str(end_date)) == 8
    trading_dates = bd.get_trading_day(start_date, end_date)
    pd_trading_dates = [pd.to_datetime(i) for i in trading_dates]
    return pd_trading_dates


def get_trading_day_offset_old(start_date, offset_list, dfreq=DFreq.DAILY, dtype=DType.STOCK, mkttype=MktType.CHINA,
                               dsource=DSource.HTSC, alt=None):
    if type(offset_list) is not list:
        offset_list = [offset_list]
    try:
        offset_list = [int(item) for item in offset_list]
    except:
        print('Illegal offsets found, aborting...')
    start_date = str_date_parser(start_date)
    if dfreq == DFreq.DAILY:
        temp_data = read_data([start_date + pd.tseries.offsets.DateOffset(days=min(int(min(offset_list) * 5), -20)),
                               start_date + pd.tseries.offsets.DateOffset(days=max(int(max(offset_list) * 5), 20))],
                              dfreq=dfreq, dtype=dtype, mkttype=mkttype, dsource=dsource, ftype=FType.CALENDAR, alt=alt)
    elif dfreq == DFreq.WEEKLY:
        temp_data = read_data(
            [start_date + pd.tseries.offsets.DateOffset(days=min(int(min(offset_list) * 7 - 10), -20)),
             start_date + pd.tseries.offsets.DateOffset(days=max(int(max(offset_list) * 7 + 10), 20))], dfreq=dfreq,
            dtype=dtype, mkttype=mkttype, dsource=dsource, ftype=FType.CALENDAR, alt=alt)
    elif dfreq == DFreq.MONTHLY:
        temp_data = read_data([start_date + pd.tseries.offsets.DateOffset(months=min(int(min(offset_list) - 2), -2)),
                               start_date + pd.tseries.offsets.DateOffset(months=max(int(max(offset_list) + 2), 2))],
                              dfreq=dfreq, dtype=dtype, mkttype=mkttype, dsource=dsource, ftype=FType.CALENDAR, alt=alt)
    elif dfreq == DFreq.YEARLY:
        temp_data = read_data([start_date + pd.tseries.offsets.DateOffset(years=min(int(min(offset_list) - 2), -2)),
                               start_date + pd.tseries.offsets.DateOffset(years=max(int(max(offset_list) + 2), 2))],
                              dfreq=dfreq, dtype=dtype, mkttype=mkttype, dsource=dsource, ftype=FType.CALENDAR, alt=alt)
    else:
        raise ValueError
    start_date = temp_data.loc[:start_date].tail(1).index.get_level_values('dt')[0]
    temp_data_lst = temp_data.index.get_level_values('dt').tolist()
    sd_idx = temp_data_lst.index(start_date)
    return [temp_data_lst[sd_idx + item] for item in offset_list]


# bie
def get_trading_day_offset(start_date, offset_list, dfreq=DFreq.DAILY):
    if type(offset_list) is not list:
        offset_list = [offset_list]
    try:
        offset_list = [int(item) for item in offset_list]
    except:
        print('Illegal offsets found, aborting...')
    start_date = str_date_parser(start_date)
    if dfreq == DFreq.DAILY:
        frequency = 'DAY'
        sdate = start_date + pd.tseries.offsets.DateOffset(days=min(int(min(offset_list) * 5), -20))
        edate = start_date + pd.tseries.offsets.DateOffset(days=max(int(max(offset_list) * 5), 20))
    elif dfreq == DFreq.WEEKLY:
        frequency = 'WEEK'
        sdate = start_date + pd.tseries.offsets.DateOffset(days=min(int(min(offset_list) * 7 - 10), -20))
        edate = start_date + pd.tseries.offsets.DateOffset(days=max(int(max(offset_list) * 7 + 10), 20))
    elif dfreq == DFreq.MONTHLY:
        frequency = 'MONTH'
        sdate = start_date + pd.tseries.offsets.DateOffset(months=min(int(min(offset_list) - 2), -2))
        edate = start_date + pd.tseries.offsets.DateOffset(months=max(int(max(offset_list) + 2), 2))
    elif dfreq == DFreq.YEARLY:
        frequency = 'YEAR'
        sdate = start_date + pd.tseries.offsets.DateOffset(years=min(int(min(offset_list) - 2), -2))
        edate = start_date + pd.tseries.offsets.DateOffset(years=max(int(max(offset_list) + 2), 2))
    else:
        raise ValueError
    sdate = dt.datetime.strftime(sdate, '%Y%m%d')
    edate = dt.datetime.strftime(edate, '%Y%m%d')
    date_list = bd.get_trading_day(sdate, edate, frequency)
    date_list = [pd.to_datetime(i) for i in date_list]
    start_date = [i for i in date_list if i <= start_date][-1]
    sd_idx = date_list.index(start_date)
    return [date_list[sd_idx + item] for item in offset_list]


def get_financial_date(start_date, offset=0, mkttype=MktType.CHINA, dtype=DType.STOCK):
    start_date = str_date_parser(start_date)
    if mkttype == MktType.CHINA and dtype == DType.STOCK:
        if type(offset) is not int or offset < 0:
            raise ValueError
        if offset == 0:
            y, m, d = start_date.year, start_date.month, start_date.day
            if m * 100 + d > 930:
                m, d = 9, 30
            elif m * 100 + d > 630:
                m, d = 6, 30
            elif m * 100 + d > 331:
                m, d = 3, 31
            else:
                y, m, d = y - 1, 12, 31
            return pd.Timestamp(y, m, d)
        else:
            financial_date = get_financial_date(start_date, offset=0)
            for counter in range(offset):
                financial_date = financial_date - pd.Timedelta('1day')
                financial_date = get_financial_date(financial_date, offset=0)
            return financial_date


def get_financial_date_range(start_date, end_date, mkttype=MktType.CHINA, dtype=DType.STOCK):
    start_date = str_date_parser(start_date)
    end_date = str_date_parser(end_date)
    if mkttype == MktType.CHINA and dtype == DType.STOCK:
        financial_dates = list(set([get_financial_date(item) for item in pd.date_range(start_date, end_date)]))
        financial_dates.sort()
        return [item for item in financial_dates if item >= start_date]


def calc_year_date_num(ps_raw):
    predefined_num = 252
    if isinstance(ps_raw, np.ndarray):
        return predefined_num
    year_list = list(ps_raw.index.year.unique())
    date_num_list = list()
    try:
        for year in year_list:
            year_date_num = len(tdt.get_trading_date_range(dt.datetime(year=int(year), month=1, day=1),
                                                           dt.datetime(year=int(year), month=12, day=31)))
            date_num_list.append(year_date_num)
    except OSError:
        print('Cannot Retrieve Calendar Data')
        return predefined_num
    return np.mean(date_num_list)


def calc_filter_correlation_helper(xy, filter_x_middle=0.4, min_pct=0.8):
    #？
    # xy = np.stack([x, y], axis=1)
    xy_sorted = xy[xy[:, 0].argsort()]  # sort by factor score - small to large
    xy_mask = np.isfinite(xy_sorted.sum(axis=1))
    valid_cnt = np.count_nonzero(xy_mask)
    total_cnt = len(xy_sorted)
    cut = (1 - filter_x_middle) / 2
    if valid_cnt < int(min_pct * total_cnt):
        filter_corr = np.nan
    else:
        xy_valid = xy_sorted[xy_mask]
        idx_0, idx_1 = int(valid_cnt * cut), int((1 - cut) * valid_cnt)
        mid_mask = np.array([True for i in range(valid_cnt)])
        mid_mask[idx_0:idx_1] = False
        filter_corr = np.corrcoef(xy_valid[mid_mask], rowvar=False)[0, 1]
    return filter_corr


def calc_filter_correlation(xy_df, corr_win=240, filter_x_middle=0.4, min_pct=0.8):
    xy_mat = xy_df.values
    row_num, col_num = xy_df.shape
    filter_corr_mat = np.zeros(row_num)
    filter_corr_mat[:] = np.nan
    for i in range(corr_win, row_num):
        filter_corr_mat[i] = calc_filter_correlation_helper(xy_mat[i - corr_win + 1:i + 1], filter_x_middle, min_pct)
    filter_corr_ts = pd.Series(filter_corr_mat, index=xy_df.index)
    return filter_corr_ts

def excel_saver(output_dict, excel_name):
    writer = pd.ExcelWriter(excel_name, engine='xlsxwriter')
    for key in output_dict:
        output_dict[key].to_excel(writer, sheet_name=key)
    writer.save()
    return


def save_pickle(save_dict, save_path):
    with open(save_path, 'wb') as input:
        pickle.dump(save_dict, input, protocol=pickle.HIGHEST_PROTOCOL)
    return


def read_pickle(save_path):
    with open(save_path, 'rb') as input:
        save_dict = pickle.load(input)
    return save_dict
