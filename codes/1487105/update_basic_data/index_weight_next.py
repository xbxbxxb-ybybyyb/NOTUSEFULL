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
#date = '20201126'
tradingdays = sorted(fa.tradingday('20180101',date))
pre_day = tradingdays[tradingdays.index(date)-1]
check_weight300 = fa.hset('INDEX', date, 'HS300',1)['weight'].sum()
check_weight500 = fa.hset('INDEX', date, 'ZZ500',1)['weight'].sum()
close = pd.read_pickle(basic_daily_path+'close.pkl')
index_list = ['HS300','ZZ500',]


stats = {}
weight_diff = {}
if check_weight300 > 99. and check_weight500 > 99.:
    flag = True
    for index in index_list:
        print(index)
        index_weight = fa.hset('INDEX', date, index, 1)
#        index_weight = fa.hset('INDEX', '20201125', index, 1)
        original_data = pd.read_pickle(basic_daily_path+index+'_data_estimate.pkl')
        df = original_data.copy()
        if pre_day in df.index:
            print('again')
            df = df[df.index != pre_day]
        ss = set(index_weight['stock'].values)&set(df.columns)
        idxw = index_weight[index_weight['stock'].isin(ss)]
        idxw.index = idxw['stock'].values
        df.loc[pd.to_datetime(pre_day),idxw['stock'].tolist()] = idxw['weight'].values
        df=df.fillna(0)
        print(df.loc[pre_day].sum().sum())
        if df.loc[pre_day].sum().sum() > 95.:
            stats[index] = df.loc[pre_day].sum().sum()
            weight_diff[index] = df.sort_index().diff().loc[pre_day].abs().max()        
            df.sort_index().to_pickle(basic_daily_path+index+'_data_estimate.pkl')
        else:
            flag = False
            original_data = pd.read_pickle(basic_daily_path+index+'_data_estimate.pkl')
            df = original_data.copy()
            if pre_day not in df.index:
                df.loc[pd.to_datetime(pre_day)] = df.loc[tradingdays[tradingdays.index(pre_day)-1]]
                df.sort_index().to_pickle(basic_daily_path+index+'_data_estimate.pkl')

else:
    flag = False
    for index in index_list:
        original_data = pd.read_pickle(basic_daily_path+index+'_data_estimate.pkl')
        df = original_data.copy()
        if pre_day not in df.index:
            df.loc[pd.to_datetime(pre_day)] = df.loc[tradingdays[tradingdays.index(pre_day)-1]]
            df.sort_index().to_pickle(basic_daily_path+index+'_data_estimate.pkl')
    print('Today Index data not updated yet.')


lm = link.LinkMessage()
ll=''
ll+="{0} Today Expected Index Data Update Flag: {1}".format(date,flag)+'\n'

if flag == True:
    for index in ['HS300','ZZ500',]:
        ll+="{0} Weight Sum: {1}".format(index,stats[index])+'\n'
        ll+="{0} Weight Diff Max(<1.5): {1}".format(index,weight_diff[index])+'\n'
else:
    ll+='Today Index data not updated yet.'
lm.sendMessage(ll)