# -*- coding: utf-8 -*-

import datetime as dt
import pandas as pd
import os
import numpy as np
from multifactor.IO import IO
from multifactor.IO.IO_enums import *
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import time
import logging
from multifactor.data.utils import *
from check_valid import check_valid, update_by_date
from download_minute import download_minute
from update_30minute_vwap import update_30minute_vwap
from update_30minute_index import update_30minute_index

current_time_fmt = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
log_level='INFO'
log_path = '/data/group/800080/warehouse/prod/LOCAL_DATA/LOG/WIND/MINUTE/'
if not os.path.exists(log_path):
    os.makedirs(log_path)
log_file = log_path + 'wind_minute_update_'+current_time_fmt+'.log'
logger=logging.getLogger('wind_minute_update')
logger.setLevel(eval('logging.'+log_level.upper()))
file_handler=logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.info('start minute data update')

 

def get_minute_data_raw_v2(ticker, date_list, isIndex):
    if isIndex:
        path = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/WIND/MINUTE/XQuant/index/'
    else:
        path = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/WIND/MINUTE/XQuant/stock/'

    df_list = []
    for date in date_list:
        csv_path = path + str(date) + '/' + ticker + '.csv'
        df = pd.read_csv(csv_path)
        df['Ticker'] = int(ticker[:-3])
        df['dt'] = date
        df_list.append(df)
    df = pd.concat(df_list)
    df.set_index(['dt', 'Ticker'], inplace=True)
    return df




def update_minute_pickle(ticker, date_list, destination_path, operation='append'):
    logger.info('ticker:%s,sdate:%d,edate:%d' % (ticker, date_list[0], date_list[-1]))
    if destination_path.find('stock') > 1:
        pickle_file = destination_path + 'UnAdjstedStockMinute_' + ticker[:-3] + '.pkl'
        isIndex = False
    elif destination_path.find('index') > 1:
        pickle_file = destination_path + 'indexMinute_' + ticker[:-3] + '.pkl'
        isIndex = True
    try:
        dat_new_stk = get_minute_data_raw_v2(ticker, date_list, isIndex)
    except:
        print('wind download error')

    if operation == 'create':
        #save_pickle(dat_new_stk, pickle_file)
        dat_new_stk.to_pickle(pickle_file,compression='gzip')
    elif operation == 'append':
        try:
            #dat_exist_stk = read_pickle(pickle_file)
            dat_exist_stk = pd.read_pickle(pickle_file,compression='gzip')
        except:
            logger.error('ticker:%s,error: read existing pickle failed' % (ticker))
            dat_exist_stk = dat_new_stk
        try:
            # check date list
            new_date_list = set(dat_new_stk.index.get_level_values(0))
            date_list = set(dat_exist_stk.index.get_level_values(0))
            
            duplicate_list = list(date_list.intersection(new_date_list))
            if len(duplicate_list) > 0:
                print('date duplicate & drop:', str(duplicate_list))
                dat_exist_stk = dat_exist_stk.drop(duplicate_list, level=0)
            dat_minute_stk = dat_exist_stk.append(dat_new_stk)
            dat_minute_stk = dat_minute_stk.sort_index(level=0)
        except:
            logger.error('ticker:%s,error: append failed' % (ticker))
            # print ('append error')

        if len(dat_minute_stk) >= len(dat_exist_stk):
            #save_pickle(dat_minute_stk, pickle_file)
            dat_minute_stk.to_pickle(pickle_file,compression='gzip')

        else:
            logger.error('ticker:%s,error: data history deleted - dumping not performed' % (ticker))
            # print ('data history deleted - dumping not performed')
    return


def parallel_io(func, ticker_list, *args, date_list, max_workers=5, **kwargs):
    tic = time.time()
    total_job = len(ticker_list)
    print('-' * 20, ' Start ', '-' * 20)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file_list = {executor.submit(func, ticker, *args, date_list = date_list, **kwargs): ticker for
                               ticker in ticker_list}
        for future in concurrent.futures.as_completed(future_to_file_list):
            ticker = future_to_file_list[future]
            try:
                future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (ticker, exc))
            else:
                print('%d/%d - %r' % (ticker_list.index(ticker) + 1, total_job, ticker))
    toc = time.time()
    print(toc - tic)
    print('-' * 20, ' End ', '-' * 20)
    return


def get_stock_list(edate):
    path = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/WIND/MINUTE/XQuant/stock/' + str(edate)
    stock_list = []
    for csv_file in os.listdir(path):
        if not csv_file[:-4] in stock_list:
            stock_list.append(csv_file[:-4])
    return stock_list


def update_wind_minute(sdate=None, edate=None, use_len=20, operation='append'):
    destination_path = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/WIND/MINUTE/'
    tic = time.time()
    # assume update for last week - 5 days
    logger.info('start downloading minute data' + '-' * 10)
    sdate, edate, cdate_list = check_update_date(sdate=sdate, edate=edate)
    logger.info('sdate:%d,edate:%d' % (sdate, edate))
    destination_stk = destination_path + 'stock/'
    destination_index = destination_path + 'index/'
    if not os.path.exists(destination_stk):
        os.makedirs(destination_stk)
    if not os.path.exists(destination_index):
        os.makedirs(destination_index)
    logger.info('destination_stk:%s, destination_index:%s' % (destination_stk, destination_index))
    index_list = ['000300.SH', '000905.SH', '000906.SH', '000016.SH']

    print('get ticker list')
    ticker_list = get_stock_list(edate)

    ticker_list.sort()
    logger.info('stock number:%d' % (len(ticker_list)))

    print('update stock minute')
    parallel_io(update_minute_pickle, ticker_list, date_list=cdate_list, max_workers=5,
                destination_path=destination_stk, operation=operation)
    logger.info('stock download complete')

    print('update index minute')
    parallel_io(update_minute_pickle, index_list, date_list=cdate_list, destination_path=destination_index,
                operation=operation)
    logger.info('index download complete')
    logger.info('all complete') 
    toc = time.time()
    time_spend = round(toc - tic, 2)
    logger.info('total time:%d' % (time_spend))
    return


if __name__ == '__main__':
    sdate,edate,cdate_list = check_update_date()
    
    flag_root = '/data/group/800080/warehouse/prod/LOCAL_DATA/FLAG/' + str(edate) + '/'
    
    if not os.path.exists(flag_root):
        os.makedirs(flag_root)
    
    flag_path_start = flag_root + str(edate) + '_' + 'MINUTE.start'
    if not os.path.exists(flag_path_start):
        f = open(flag_path_start,'w')
        f.close()
    with open(flag_path_start,'w') as file:
        pass 
    
    print(sdate,edate)
    for date in cdate_list:
        download_minute(date)
    update_wind_minute(sdate=sdate, edate=edate, operation='append')
    
   

    finish = False
    print('wait---------------')

    try:
        print('start check valid')
        finish = check_valid(edate)
        print(finish)
    except Exception as e:
        print(e)
    if finish:
        print('start update_by_date')
        update_by_date()
        flag_path1 = flag_root + str(edate) + '_' + 'MINUTE.success'
        if not os.path.exists(flag_path1):
            f = open(flag_path1,'w')
            f.close()
        with open(flag_path1,'w') as file:
            pass   
        print('finish checking valid')
        
        
        update_30minute_index()
        update_30minute_vwap()


