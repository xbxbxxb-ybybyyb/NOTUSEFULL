# coding:utf-8
from tquant.strategy.day_factor_backtest_new.IO.IO import *
import datetime as dt
import pandas as pd
from tquant import BasicData

bd = BasicData()

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
