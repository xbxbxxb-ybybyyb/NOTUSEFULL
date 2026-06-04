import datetime as dt
import pandas as pd
import os
import numpy as np
from multifactor.IO import IO
from multifactor.IO.IO_enums import *
import multifactor.utility.dt as tdt
import settings


def get_old_day_helper(date):
    fdate_list_dt = IO.read_data([19980101, 20300101], ftype=FType.CALENDAR).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
    while date not in fdate_list:
        date -= 1
    index = fdate_list.index(date)
    sdate = fdate_list[index - 250]
    return sdate


def dt_parser(date):
    date_obj = dt.datetime.strptime(str(int(date)), '%Y%m%d')
    return date_obj


def easy_fill(factor_data, start_date, end_date, foward_date, fill_method='ffill'):
    start_date = IO.str_date_parser(start_date)
    end_date = IO.str_date_parser(end_date)
    factor_fill = factor_data.copy().reset_index().sort_values(by='dt').dropna()
    if isinstance(factor_fill[foward_date].values[0], int) or isinstance(factor_fill[foward_date].values[0], float):
        factor_fill[foward_date] = factor_fill[foward_date].apply(dt_parser)
    # aggregate same datewith different ammount
    factor_fill = factor_fill.groupby([foward_date, 'Ticker']).sum()
    factor_fill = factor_fill[factor_fill.columns[0]].unstack()
    full_day_range = pd.date_range(start=start_date, end=end_date, freq='1D')
    if fill_method is None:
        factor_fill = factor_fill.reindex(index=full_day_range)
    else:
        factor_fill = factor_fill.reindex(index=full_day_range).fillna(method=fill_method)
    factor_fill = factor_fill.reindex(index=tdt.get_trading_date_range(start_date, end_date))
    return factor_fill


def man(start_date, end_date):
    save_folder = os.path.join(settings.BASE_DIR, 'LOCAL_DATA/CSV/wind_data/dividendyield2/')
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    universe_folder = os.path.join(settings.BASE_DIR, "LOCAL_DATA/CSV/wind_data/wind_stock_list/")
    sdate_dummy, edate_dummy = 20040101, 20990101
    dividend_data = IO.read_data([sdate_dummy, edate_dummy],
                                 alt=os.path.join(settings.BASE_DIR, 'DATABASE/WIND/AShareDividend/AShareDividend.h5'))
    dividend_data = dividend_data[dividend_data['S_DIV_PROGRESS'] == 3]
    start_date_old = get_old_day_helper(start_date)
    dat_uni = IO.read_data([start_date_old, end_date], columns=['mkt_cap_ard', 'total_shares'],
                           alt=os.path.join(settings.BASE_DIR,
                                            'MD/CHINA_STOCK/DAILY/WIND/MD_CHINA_STOCK_DAILY_WIND.h5'))
    mkt_cap_ard = dat_uni['mkt_cap_ard'].unstack()
    total_shares = dat_uni['total_shares'].unstack()
    div_dat = easy_fill(dividend_data[['CASH_DVD_PER_SH_PRE_TAX', 'EX_DT']], start_date_old, end_date,
                        foward_date='EX_DT', fill_method=None)
    dividend_payout = (div_dat * total_shares.shift(1)).fillna(0).rolling(240).sum()
    dividendyield_raw = dividend_payout / mkt_cap_ard * 100
    rst = dividendyield_raw.stack()
    rst = pd.DataFrame(rst)
    rst.reset_index(inplace=True)
    rst.columns = ['dt', 'Ticker', 'dividendyield2']
    date_list = list(set(rst['dt']))
    date_list.sort()

    for p_dt in date_list:
        date = int(str(p_dt).replace('-', '')[:8])
        if start_date <= date <= end_date:
            date = int(str(date).replace('-', '')[:8])
            stock_list = pd.read_csv(universe_folder + str(date) + '.csv', header=0)['Ticker'].values.tolist()
            df = rst[rst['dt'] == p_dt]
            df.drop('dt', axis=1, inplace=True)
            df.set_index('Ticker', inplace=True)
            exist_stock = df.index.values.tolist()
            stock_list1 = list(set(exist_stock) & set(stock_list))
            stock_list2 = list(set(stock_list) - set(stock_list1))
            df = df.loc[stock_list1]
            data = []
            for _ in stock_list2:
                data.append(np.nan)
            df2 = pd.DataFrame(data, index=stock_list2, columns=['dividendyield2'])
            df2.index.name = 'Ticker'
            df = df.append(df2)
            df = df.sort_index()
            df.to_csv(save_folder + str(date) + '.csv')


def main(cdate_list):
    start_date = int(cdate_list[0])
    end_date = int(cdate_list[-1])
    man(start_date, end_date)
