# -*- coding: utf-8 -*-
"""
Created on Mon Jan 15 13:17:25 2018

@author: 012315  013160
"""
import sys
import datetime as dt
import pandas as pd
import os
import numpy as np
from multifactor.IO import IO
from multifactor.IO.IO_enums import *
from utils import *
from concurrent.futures import ProcessPoolExecutor as Pools
from concurrent.futures import as_completed
def ticker_match(ticker_num): # jit slow
    ticker_num = int(ticker_num)
    suffix = '.SH' if ticker_num>=600000 else '.SZ'
    pre_fill = (6 - len(str(ticker_num)))*'0'
    ticker = pre_fill + str(ticker_num) + suffix
    return ticker

def MD_retrieve(date):
    root = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/wind_data/'
    path = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/WIND/MINUTE/stock_perdate/'
    df = pd.read_pickle(path + str(date) + '.pkl',compression='gzip')
    df.reset_index('dt',inplace=True)
    df.drop(['dt'],axis=1,inplace=True)
    df = df[df['minute'] >= 930]
    df.fillna(0,inplace=True)
    tmp_dict = {}
    tmp_df = df[df['minute'] == 1500]
    for ticker in set(tmp_df.index):
        tmp_dict[ticker] = [float(tmp_df.loc[ticker]['amt']), float(tmp_df.loc[ticker]['volume'])]
    df.reset_index(inplace=True)
    def amt_helper(x,tmp_dict):
        m = x['minute']
        t = x['Ticker']
        if m == 1459:
            return x['amt'] + tmp_dict[t][0]
        else:
            return x['amt']
    def volume_helper(x,tmp_dict):
        m = x['minute']
        t = x['Ticker']
        if m == 1459:
            return x['volume'] + tmp_dict[t][1]
        else:
            return x['volume']
    df['amt'] = df.apply(lambda x : amt_helper(x,tmp_dict),axis=1)
    df['volume'] = df.apply(lambda x : volume_helper(x,tmp_dict),axis=1)
    df.set_index('minute',inplace=True)
    a = df.groupby('Ticker')['amt'].rolling(30).sum()
    b = df.groupby('Ticker')['volume'].rolling(30).sum()
    df = pd.concat([a,b],axis=1)
    df['vwap'] = df['amt'] / df['volume']
    minute_list = [959,1029,1059,1129,1329,1359,1429,1459]
    df.reset_index('Ticker',inplace=True)
    for minute in minute_list:
        colume_name = 'vwap_minute30_' + str(minute_list.index(minute)+1)
        csv_path = root + colume_name + '/'
        if not os.path.exists(csv_path):
            os.makedirs(csv_path)
        cur_df = df.loc[minute]
        cur_df.drop(['amt','volume'],axis=1,inplace=True)
        cur_df.reset_index(inplace=True)
        cur_df.drop(['minute'],axis=1,inplace=True)
        cur_df['Ticker'] = cur_df['Ticker'].apply(lambda x : ticker_match(x))
        cur_df.set_index('Ticker',inplace=True)
        cur_df.columns = [colume_name]
        cur_df.to_csv(csv_path + str(date)+'.csv')
    print(str(date) + ' done!')
    return date 



def price_retriever(date):
    root = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/wind_data/'
    path = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/WIND/MINUTE/stock_perdate/'
    df = pd.read_pickle(path + str(date) + '.pkl',compression='gzip')
    df_list = []
    df.reset_index('dt',inplace=True)
    for tik in list(set(df.index)):
        df1 = df.loc[tik]
        df1.fillna(method='ffill',inplace=True)
        df_list.append(df1)
    df = pd.concat(df_list)
    df.drop(['dt'],axis=1,inplace=True)
    df = df[df['minute'] >= 930]
    last_df = df[df['minute'] >= 1430]
    df.reset_index(inplace=True)
    df.set_index('minute',inplace=True)
    minute_list = [959,1029,1059,1129,1329,1359,1429,1500]
    # df.reset_index('Ticker',inplace=True)

    for minute in minute_list:
        colume_name = 'open_minute30_' + str(minute_list.index(minute)+1)
        csv_path = root + colume_name + '/'
        if not os.path.exists(csv_path):
            os.makedirs(csv_path)
        if minute < 1500:
            cur_df = df.loc[minute-29]
        else:         
            cur_df = df.loc[1430]
        cur_df.reset_index(inplace=True)
        cur_df.drop(['minute'],axis=1,inplace=True)
        cur_df['Ticker'] = cur_df['Ticker'].apply(lambda x : ticker_match(x))
        cur_df.set_index('Ticker',inplace=True)
        cur_df = cur_df[['open']]
        cur_df.columns = [colume_name]
        cur_df.to_csv(csv_path + str(date)+'.csv')

    for minute in minute_list:
        colume_name = 'close_minute30_' + str(minute_list.index(minute)+1)
        csv_path = root + colume_name + '/'
        if not os.path.exists(csv_path):
            os.makedirs(csv_path)
        cur_df = df.loc[minute]
        cur_df.reset_index(inplace=True)
        cur_df.drop(['minute'],axis=1,inplace=True)
        cur_df['Ticker'] = cur_df['Ticker'].apply(lambda x : ticker_match(x))
        cur_df.set_index('Ticker',inplace=True)
        cur_df = cur_df[['close']]
        cur_df.columns = [colume_name]
        cur_df.to_csv(csv_path + str(date)+'.csv')


    a = df.groupby('Ticker')['close'].rolling(30, min_periods=5).mean()
    df = pd.DataFrame(a)
    df.reset_index('Ticker',inplace=True)
    minute_list = [959,1029,1059,1129,1329,1359,1429]
    # df.reset_index('Ticker',inplace=True)
    for minute in minute_list:
        colume_name = 'twap_minute30_' + str(minute_list.index(minute)+1)
        csv_path = root + colume_name + '/'
        if not os.path.exists(csv_path):
            os.makedirs(csv_path)
        cur_df = df.loc[minute]
        cur_df.reset_index(inplace=True)
        cur_df.drop(['minute'],axis=1,inplace=True)
        cur_df['Ticker'] = cur_df['Ticker'].apply(lambda x : ticker_match(x))
        cur_df.set_index('Ticker',inplace=True)
        cur_df.columns = [colume_name]
        cur_df.to_csv(csv_path + str(date)+'.csv')
    
    minute = 1459
    last_df.reset_index(inplace=True)
    last_df.set_index('minute',inplace=True)
    a = last_df.groupby('Ticker')['close'].mean()
    df = pd.DataFrame(a)
    df.reset_index('Ticker',inplace=True)
    colume_name = 'twap_minute30_8'
    csv_path = root + colume_name + '/'
    if not os.path.exists(csv_path):
        os.makedirs(csv_path)
    df['Ticker'] = df['Ticker'].apply(lambda x : ticker_match(x))
    df.set_index('Ticker',inplace=True)
    df.columns = [colume_name]
    df.to_csv(csv_path + str(date)+'.csv')
    print(str(date) + ' done!')
    return date 

def halfday_vwap_retriver(date):
    print('--' , date)
    root = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/wind_data/'
    path = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/WIND/MINUTE/stock_perdate/'
    df = pd.read_pickle(path + str(date) + '.pkl', compression='gzip')
    df.reset_index(inplace=True)
    df['Ticker'] = df['Ticker'].apply(lambda x: ticker_match(x))
    df = df[df['minute'] >= 930]
    df = df[df['minute'] <= 1457]
    df_halfday_1 = df[df['minute'] < 1200] # get moring data
    df_halfday_2 = df[df['minute'] > 1200] # get afternoon data

    a1 = df_halfday_1.groupby('Ticker')['volume','amt'].sum()
    a1['vwap_halfday_1'] = a1.amt / a1.volume
    a1 = a1[['vwap_halfday_1']]
    a1.to_csv(root + 'vwap_halfday_1/' + str(date) + '.csv')

    a2 = df_halfday_2.groupby('Ticker')['volume', 'amt'].sum()
    a2['vwap_halfday_2'] = a2.amt / a2.volume
    a2 = a2[['vwap_halfday_2']]
    a2.to_csv(root + 'vwap_halfday_2/' + str(date) + '.csv')

def update_wind_daily_h5(cdate_list,daily_factor,csv_path,h5_path,operation='append'):
    """factor_scale for maintaining consistent level between HTSC and WIND data"""
    fail_list = []
    for factor_name in daily_factor:
        print(factor_name)
        try:
            file_folder = csv_path+factor_name+'/'
            df_list = []
            for date in cdate_list:
                print('--' + str(date))
                fname = file_folder+str(date)+'.csv'
                dat = pd.read_csv(fname)
                dat['dt'] = dt.datetime.strptime(str(date),'%Y%m%d')
                dat.set_index(['dt','Ticker'],inplace=True)
                df_list.append(dat)
            dat = pd.concat(df_list)
            print(len(dat))
            if len(dat)>0:
                if operation=='append':
                    IO.pd_hdf5_writer(dat, h5_path, dataset=factor_name,append=True)
                elif operation =='create':
                    IO.pd_hdf5_writer(dat, h5_path, dataset=factor_name)
        except Exception as e:
            fail_list.append(factor_name)
    return fail_list



def rolling(sdate=None, edate=None):
    '''
    main function of training
    save predict value in training set into .pkl file
    '''
    sdate, edate, cdate_list = check_update_date(sdate,edate)
    for date in cdate_list:
        MD_retrieve(date)
        price_retriever(date)
        halfday_vwap_retriver(date)
    factor_list = ['vwap_halfday_1','vwap_halfday_2','vwap_minute30_1','vwap_minute30_2','vwap_minute30_3','vwap_minute30_4',
                'vwap_minute30_5','vwap_minute30_6','vwap_minute30_7','vwap_minute30_8',
                'twap_minute30_1','twap_minute30_2','twap_minute30_3','twap_minute30_4',
                'twap_minute30_5','twap_minute30_6','twap_minute30_7','twap_minute30_8']
    # factor_list = ['twap_minute30_1','twap_minute30_2','twap_minute30_3','twap_minute30_4',
    #             'twap_minute30_5','twap_minute30_6','twap_minute30_7','twap_minute30_8']
    factor_list2 = ['close_minute30_1','close_minute30_2','close_minute30_3','close_minute30_4',
                'close_minute30_5','close_minute30_6','close_minute30_7','close_minute30_8',
                'open_minute30_1','open_minute30_2','open_minute30_3','open_minute30_4',
                'open_minute30_5','open_minute30_6','open_minute30_7','open_minute30_8']


    csv_path = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/wind_data/'
    h5_path = '/data/group/800080/warehouse/prod/VD/CHINA_STOCK/DAILY/WIND/VD_CHINA_STOCK_DAILY_WIND.h5'

    update_wind_daily_h5(cdate_list,factor_list +factor_list2,csv_path,h5_path,'append')


def flag_check(date):
    path = '/data/group/800080/warehouse/prod/LOCAL_DATA/FLAG/' + str(date) + '/' + str(date) + '_' + 'MINUTE.success'
    return os.path.exists(path)


# rolling(20191021,20191022)

def update_30minute_vwap(a = None, b = None):
    sdate,edate,cdate_list = check_update_date(a,b)
    flag_root = '/data/group/800080/warehouse/prod/LOCAL_DATA/FLAG/' + str(edate) + '/'
    
    flag_path_start = flag_root + str(edate) + '_' + 'VD.start'
    if not os.path.exists(flag_path_start):
        f = open(flag_path_start,'w')
        f.close()
    with open(flag_path_start,'w') as file:
        pass 
    
    
    print('wait---------------')
    
    while True:
        if flag_check(edate):
            break

    rolling(a,b)
    
    flag_path_success = flag_root + str(edate) + '_' + 'VD.success'
    if not os.path.exists(flag_path_success):
        f = open(flag_path_success,'w')
        f.close()
    with open(flag_path_success,'w') as file:
        pass



