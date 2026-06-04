import os
import pandas as pd
import numpy as np
import scipy.io as spo
from copy import deepcopy
import time
import datetime
import sys
import warnings
warnings.filterwarnings("ignore")
from xquant.marketdata import MarketData
from xquant.factordata import FactorData
import matplotlib.pyplot as plt
from xquant.xqutils.helper import link
from config_path import * 


fa = FactorData()

mdp = MarketData(dfs=None)

universe = spo.loadmat(universe_path + 'universe.mat')['universe']
stock_list = sorted([x[0][0] for x in universe])

date=today
#date = '20201229'
tradingdays = sorted(fa.tradingday('20180101',date))
check_weight300 = fa.hset('INDEX', date, 'HS300')['weight'].sum()
check_weight500 = fa.hset('INDEX', date, 'ZZ500')['weight'].sum()
check_weight1000 = fa.hset('INDEX', date, 'ZZ1000')['weight'].sum()
close = pd.read_pickle(basic_daily_path+'close.pkl')
index_list = ['HS300','ZZ500','ZZ1000']
#index_list = ['HS300',]

stats = {}
weight_diff = {}
if check_weight300 > 99. and check_weight500 > 99. and check_weight1000 > 99.:
    flag = True
    for index in index_list:
        print(index)
        index_weight = fa.hset('INDEX', date, index)
#        index_weight = fa.hset('INDEX', '20201125', index, 1)
        original_data = pd.read_pickle(basic_daily_path+index+'_data.pkl')
        df = original_data.copy()
        if date in df.index:
            print('again')
            df = df[df.index != date]
        ss = set(index_weight['stock'].values)&set(df.columns)
        idxw = index_weight[index_weight['stock'].isin(ss)]
        idxw.index = idxw['stock'].values
        df.loc[pd.to_datetime(date),idxw['stock'].tolist()] = idxw['weight'].values
        df=df.fillna(0)
        print(df.loc[date].sum().sum())
        if df.loc[date].sum().sum() > 95.:
            df.sort_index().to_pickle(basic_daily_path+index+'_data.pkl')
        else:
#            flag = False
            original_data = pd.read_pickle(basic_daily_path+index+'_data.pkl')
            df = original_data.copy()
            if date not in df.index:
                df.loc[pd.to_datetime(date)] = df.loc[tradingdays[-2]]
                df.sort_index().to_pickle(basic_daily_path+index+'_data.pkl')
        stats[index] = df.loc[date].sum().sum()
        weight_diff[index] = df.sort_index().diff().loc[date].abs().max()
else:
    flag = False
    for index in index_list:
        original_data = pd.read_pickle(basic_daily_path+index+'_data.pkl')
        df = original_data.copy()
        if date not in df.index:
            df.loc[pd.to_datetime(date)] = df.loc[tradingdays[-2]]
            df.sort_index().to_pickle(basic_daily_path+index+'_data.pkl')
    print('Today Index data not updated yet.')


lm = link.LinkMessage()
lm.sendMessage("{0} Today Index Data Update Flag: {1}".format(date,flag))
ll = ''
if flag == True:
    for index in ['HS300','ZZ500','ZZ1000']:
        ll+="{0} Weight Sum: {1}".format(index,stats[index])+'\n'
        ll+="{0} Weight Diff Max(<1.5): {1}".format(index,weight_diff[index])+'\n'
lm.sendMessage(ll)
