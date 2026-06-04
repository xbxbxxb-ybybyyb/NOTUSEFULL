import datetime as dt
import pandas as pd
import os
import numpy as np
import json
from Wind.utils import *
from log import Log
logger = Log("get_dividend")

def get_old_day_helper(date, offset):
    fdate_list_dt = read_data([19980101, 20200101], ftype=FType.CALENDAR).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt] 
    while date not in fdate_list:
        date -= 1
    index = fdate_list.index(date)
    sdate = fdate_list[index - 250]
    return sdate

def dt_parser(date):
    date_obj = dt.datetime.strptime(str(int(date)),'%Y%m%d')
    return date_obj

def easy_fill(factor_data,start_date,end_date,foward_date,fill_method='ffill'):
    sdate = str_date_parser(start_date)
    edate = str_date_parser(end_date)
    factor_fill = factor_data.copy().reset_index().sort_values(by='dt').dropna()
    if isinstance(factor_fill[foward_date].values[0],int) or isinstance(factor_fill[foward_date].values[0],float) or isinstance(factor_fill[foward_date].values[0],str):
        factor_fill[foward_date] = factor_fill[foward_date].apply(dt_parser)
    # aggregate same datewith different ammount
    factor_fill = factor_fill.groupby([foward_date, 'Ticker']).sum()
    factor_fill = factor_fill[factor_fill.columns[0]].unstack()
    full_day_range = pd.date_range(start=sdate, end=edate, freq='1D')
    if fill_method is None:
        factor_fill = factor_fill.reindex(index=full_day_range)
    else:
        factor_fill = factor_fill.reindex(index=full_day_range).fillna(method=fill_method)
    factor_fill = factor_fill.reindex(index=get_trading_date_range(start_date, end_date))
    return factor_fill



def man(start_date, end_date,sql_config):
    logger.info("calc factor dividendyield2")
    universe_folder = "/app/data/wdb_h5/WIND_TEST/universe_complete/stocklst/"
    sdate_dummy,edate_dummy = 20040101,20990101
    # dividend_data = read_data([sdate_dummy,edate_dummy],alt=r'Z:\warehouse\prod\DATABASE\WIND\AShareDividend\AShareDividend.h5')
    # factor_list = ["S_INFO_WINDCODE","ANN_DT","S_DIV_PROGRESS","CASH_DVD_PER_SH_PRE_TAX","EX_DT"]
    table = "Wind.AShareDividend"
    # dividend_data = get_wind_data(table,factor_list)
    sql_use = "select S_INFO_WINDCODE,ANN_DT,S_DIV_PROGRESS,CASH_DVD_PER_SH_PRE_TAX,EX_DT from %s where ANN_DT >= %s and ANN_DT <= %s"%(table,sdate_dummy,edate_dummy)
    dividend_data = sql_parser(queryUserTableData(sql_use,sql_config))
    dividend_data.rename(columns={"S_INFO_WINDCODE":"Ticker","ANN_DT":"dt"},inplace=True)
    dividend_data.set_index(['dt','Ticker'],inplace=True)
    if dividend_data['S_DIV_PROGRESS'].dtype == 'object':
        dividend_data["S_DIV_PROGRESS"] = dividend_data["S_DIV_PROGRESS"].apply(pd.to_numeric)
    dividend_data = dividend_data[dividend_data['S_DIV_PROGRESS']==3]
    start_date_old= get_old_day_helper(start_date,250)
    dat_uni = read_data([start_date_old, end_date], columns=['mkt_cap_ard', 'total_shares'], alt = '/app/data/wdb_h5/WIND_TEST/MD_CHINA_STOCK_DAILY_WIND/MD_CHINA_STOCK_DAILY_WIND.h5')
    mkt_cap_ard = dat_uni['mkt_cap_ard'].unstack()
    total_shares = dat_uni['total_shares'].unstack()
    div_dat = easy_fill(dividend_data[['CASH_DVD_PER_SH_PRE_TAX','EX_DT']],start_date_old,end_date,foward_date='EX_DT',fill_method=None)
    dividend_payout = (div_dat * total_shares.shift(1) ).fillna(0).rolling(240).sum()
    dividendyield_raw = dividend_payout / mkt_cap_ard * 100
    rst = dividendyield_raw.stack()
    rst = pd.DataFrame(rst)
    rst.reset_index(inplace=True)
    rst.columns=['dt','Ticker','dividendyield2']
    date_list = list(set(rst['dt']))
    date_list.sort()

    dt = date_list[-1]
    date = int(str(dt).replace('-','')[:8])
    if not os.path.exists(universe_folder + str(date) + '.csv'):
        get_stock_list(date,sql_config)
    stock_list = pd.read_csv(universe_folder + str(date) + '.csv', header=0)['Ticker'].values.tolist()
    df = rst[rst['dt'] == dt]
    df.set_index('Ticker', inplace=True)
    df = df[['dt','dividendyield2']]
    exist_stock = df.index.values.tolist()
    stock_list1 = list(set(exist_stock) & set(stock_list))
    stock_list2 = list(set(stock_list) - set(stock_list1))
    df = df.loc[stock_list1]
    data = []
    for stock in stock_list2:
        data.append(np.nan)
    df2 = pd.DataFrame(data, index=stock_list2, columns=['dividendyield2'])
    df2.index.name = 'Ticker'
    df2['dt'] = dt
    df2 = df2[['dt','dividendyield2']]
    df = df.append(df2)
    df.reset_index('Ticker',inplace=True)
    # df.set_index(['dt','Ticker'],inplace=True)
    return df


def get_divid(sql_config,cdate_list,date,factor_name):
    start_date = min(cdate_list)
    end_date = max(cdate_list)
    return man(start_date,end_date,sql_config)

# print(get_divid([20131111,20131115]))
