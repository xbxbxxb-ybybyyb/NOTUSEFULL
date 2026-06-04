import pickle
from xquant.pyfile import Pyfile
from xquant.factor import FactorData
from xquant.thirdpartydata.marketdata import MarketData
import pickle
import gzip
import pandas as pd
import numpy as np
import xquant.quant as xq
from xquant.pyfile.ftp import pyfileFTP
import os
import datetime as dt
import zipfile
from xquant.xqutils.xqfile import HDFSFile

def download_minute(date):
    root = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/WIND/MINUTE/XQuant/'
    ma = MarketData()
    stock_root_path = 'stock/' + str(date)
    start_date = str(date) + '090000'
    end_date = str(date) + '153000'
    stock_list = xq.hset(xq.PlateType.MARKET,date,xq.MarketType.ALLA)
    stock_root_path = root +'/stock/'+str(date)

    if not os.path.exists(stock_root_path):
        os.makedirs(stock_root_path)

    for stock in stock_list[0]:
        print(stock)
        df = ma.getKLine4ZTDataFrame(stock, start_date, end_date, 10, 20, True)
        df_xquant = df[['MDTime','OpenPx','HighPx','LowPx','ClosePx','TotalVolumeTrade','TotalValueTrade']]
        df_xquant.columns = ['minute','open','high','low','close','volume','amt']
        df_xquant['minute'] = df_xquant['minute'].apply(lambda x : int(x[:4]))
        df_xquant['Ticker'] = stock
        df_xquant.set_index('minute',inplace=True)
        df_xquant.to_csv(stock_root_path+'/' + stock + '.csv')

    index_root_path = root  + '/index/' + str(date)

    if not os.path.exists(index_root_path):
        os.makedirs(index_root_path)
    index_list = ['000001.SH','000016.SH', '000300.SH', '000905.SH', '000906.SH']
    for stock in index_list:
        print(stock)
        df = ma.getKLine4ZTDataFrame(stock, start_date, end_date, 10, 20,True)
        df_xquant = df[['MDTime','OpenPx','HighPx','LowPx','ClosePx','TotalVolumeTrade','TotalValueTrade']]
        df_xquant.columns = ['minute','open','high','low','close','volume','amt']
        df_xquant['minute'] = df_xquant['minute'].apply(lambda x : int(x[:4]))
        df_xquant['Ticker'] = stock
        df_xquant.set_index('minute',inplace=True)
        df_xquant.to_csv(index_root_path+'/' + stock + '.csv')


    