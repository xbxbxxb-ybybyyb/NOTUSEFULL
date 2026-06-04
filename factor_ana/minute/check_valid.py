# -*- coding: utf-8 -*-

import datetime as dt
import pandas as pd
import os
import numpy as np
from multifactor.IO import IO
from multifactor.IO.IO_enums import *
import time
import logging
from multifactor.data.utils import *
# import xquant.quant as xq
from xquant.factordata import FactorData
s = FactorData()

def univ_flag_check(date):
    path = '/data/group/800080/warehouse/prod/LOCAL_DATA/FLAG/' + str(date) + '/' + str(date) + '_' + 'UNIV.success'
    return os.path.exists(path)


# def get_stock_list(edate):
    # path = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/Xquant_minute/stock/' + str(edate)
    # stock_list = []
    # for csv_file in os.listdir(path):
        # if not csv_file[:-4] in stock_list:
            # stock_list.append(csv_file[:-4])
    # return stock_list


def ticker_match(ticker_num): # jit slow
    ticker_num = int(ticker_num)
    suffix = '.SH' if ticker_num>=600000 else '.SZ'
    pre_fill = (6 - len(str(ticker_num)))*'0'
    ticker = pre_fill + str(ticker_num) + suffix
    return ticker

def check_valid(date):
    root_path = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/WIND/MINUTE/'
    # root_path = 'Z:\\warehouse\\test\\minute_XQuant\\'
    index_path = root_path + 'index/'
    rst = {}
    rst[date] = {}
    for file in os.listdir(index_path):
        if '399001' in file or '399006' in file or '000001' in file:
            continue
        pickle_file = index_path + file
        df = pd.read_pickle(pickle_file,compression='gzip')
        df.reset_index('Ticker', inplace= True)
        df.drop('Ticker', axis=1, inplace=True)
        # print(df)
        df1 = df.loc[int(date)]
        count = df1['close'].isnull().sum()
        rst[date][file] = count
    for date in rst:
        index_list = []
        rst_list = []
        for index in rst[date]:
            index_list.append(index)
            rst_list.append(rst[date][index])
        df_index = pd.DataFrame(rst_list, index = index_list, columns = ['count'])
        df_index.to_csv('/data/group/800080/warehouse/prod/LOG/index_minute/' + str(date) + '.csv')
    
    stock_path = root_path + 'stock/'
    # stock_list = xq.hset(xq.PlateType.MARKET,date,xq.MarketType.ALLA)[0]
    result1 = s.hset('MARKET', str(date), 'ALLA')
    stock_list = list(result1['stock'])
    rst = {}
    rst[date] = {}
    for stock in stock_list:
        file = 'UnAdjstedStockMinute_' + stock[:-3] + '.pkl'
        pickle_file = stock_path + file
        df = pd.read_pickle(pickle_file,compression='gzip')
        df.reset_index('Ticker', inplace= True)
        df.drop('Ticker', axis=1, inplace=True)
        # print(df)
        try:
            df1 = df.loc[int(date)]
        except Exception as e:
            print(e)
            rst[date][file] = -1

        count = df1['close'].isnull().sum()
        if count > 240 or count < 0:
            rst[date][file] = count

    print('------wait univ')
    while True:
        if univ_flag_check(date):
            break

    for date in rst:
        df_suspend = IO.read_data(date, columns=['SUSPEND'], alt = r'/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/stock_universe/universe_complete.h5')
        df_suspend.reset_index('dt', inplace=True)
        df_suspend.drop('dt', axis=1, inplace=True)
        total_list = list(df_suspend.index)
        df_suspend = df_suspend[df_suspend['SUSPEND'] == 0]
        suspend_list = list(df_suspend.index)
        index_list = []
        rst_list = []
        for index in rst[date]:
            stock = ticker_match(index[-10:-4])
            # if stock in ['000693.SZ', '002070.SZ', '600401.SH', '600680.SH','002680.SZ']:
                # continue
            if stock in suspend_list:
                continue
            if not stock in total_list:
                continue
            index_list.append(stock)
            rst_list.append(rst[date][index])
        df = pd.DataFrame(rst_list, index = index_list, columns = ['count'])
        print(df)
        df.to_csv('/data/group/800080/warehouse/prod/LOG/stock_minute/' + str(date) + '_new.csv')
        flag_path = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/WIND/MINUTE/flag/' + str(date) + '_' + 'minute_stock.success'
        # flag_path = '/data/group/800080/warehouse/prod/LOCAL_DATA/FLAG/' + str(date) + '/' + str(date) + '_' + 'MINUTE.success'
        if len(df) == 0:
            if not os.path.exists('/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/WIND/MINUTE/flag/'):
                os.makedirs(flag_path)
            with open(flag_path,'w') as file:
                pass
            return True
        else:
            return False
                # file.write('minute data update sucess')


def update_by_date(sdate=None, edate=None):
    '''
    after minute data update sucessfully,
    make the data by date
    '''
    sdate, edate, date_list = check_update_date(sdate = sdate, edate = edate)
    print(date_list)
    root_path = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/WIND/MINUTE/'
    index_path = root_path + 'index/'
    index_dest = root_path + 'index_perdate/'
    for date in date_list:
        index_df_list = []
        for file in os.listdir(index_path):
            if '399001' in file or '399006' in file or '000001' in file:
                continue
            pickle_file = index_path + file
            df = pd.read_pickle(pickle_file,compression='gzip')
            df.reset_index('Ticker', inplace= True)
            df = df.loc[int(date)]
            df.reset_index('dt',inplace=True)
            df.set_index(['dt','Ticker'],inplace=True)
            index_df_list.append(df)
        index_df = pd.concat(index_df_list)
        pickle_file = index_dest + str(date) + '.pkl'
        index_df.to_pickle(pickle_file,compression='gzip')
        print(index_df)

    stock_path = root_path + 'stock/'
    stock_dest = root_path + 'stock_perdate/'
    for date in date_list:
        stk_df = pd.DataFrame()
        for file in os.listdir(stock_path):
            pickle_file = stock_path + file
            df = pd.read_pickle(pickle_file,compression='gzip')
            df.reset_index('Ticker', inplace= True)
            try:
                df = df.loc[int(date)]
                df.reset_index('dt',inplace=True)
                df.set_index(['dt','Ticker'],inplace=True)
                if len(stk_df) == 0:
                    stk_df = df
                else:
                    stk_df = pd.concat([stk_df,df])
                print(stk_df)
                # stk_df_list.append(df)
            except Exception as e:
                print(e)
                continue
        pickle_file = stock_dest + str(date) + '.pkl'
        stk_df.to_pickle(pickle_file,compression='gzip')
        print(stk_df)


