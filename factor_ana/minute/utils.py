# -*- coding: utf-8 -*-
"""
Created on Tue May 22 17:00:00 2018

@author: 012315  013160
"""

import sys
import datetime as dt
import pandas as pd
import os
import numpy as np
import json
from multifactor.IO import IO
from multifactor.IO.IO_enums import *
import time as time
import statsmodels.api as sm
from functools import reduce
import config_reader
import pickle


# MINUTE ~~~~~~~~~~~~~~~~~~~~~~~~~~
def save_pickle(save_dict,save_path):
    with open(save_path, 'wb') as input:
        pickle.dump(save_dict,input,protocol=pickle.HIGHEST_PROTOCOL)
    return

def read_pickle(save_path):
    with open(save_path, 'rb') as input:
        save_dict = pickle.load(input)
    return save_dict


# WIND ~~~~~~~~~~~~~~~~~~~~~~~~~~

def latest_issue_date(qtr):
    if type(qtr)==int:
        qtr=str(qtr)
    if type(qtr)==pd._libs.tslib.Timestamp:
        qtr = dt.datetime.strftime(qtr,'%Y%m%d')
    year,month = qtr[:4],qtr[4:]
    lookup_dict = {'0331':'0430','0630':'0831','0930':'1031','1231':'0430'}
    #lookup_dict = {'0331':'0505','0630':'0905','0930':'1105','1231':'0505'}
    if month =='1231':
        lastest_int = int(str(int(year)+1)+lookup_dict[month])
    else:
        lastest_int = int(year+lookup_dict[month])
    last_day = dt.datetime.strptime(str(lastest_int),'%Y%m%d')
    return last_day


# STYLE ~~~~~~~~~~~~~~~~~~~~~~~~~~
def MultiIndex2DF(h5_data):
    """
    Input: H5 data: date/stock/[factor list]
    Ouput: Dictionary containing multiple dataframe as matrix format (date*stock)
    """
    data_dict = {}
    index_list = h5_data.columns
    for fac in index_list:
        data_dict[fac]= h5_data[fac].unstack()
    return data_dict

def DF2MultiIndex(df_dict):
    """pass in dict of df, get df with multi_index"""
    df_mi = pd.DataFrame()
    for df in df_dict:
        df_dict[df] = df_dict[df].reset_index()
        if df_dict[df].columns[0]=='index':
            df_dict[df] = df_dict[df].rename(index=str, columns={"index": "dt"})
        df_dict[df]['FactorName'] = df
        df_dict[df] = df_dict[df].set_index(['dt','FactorName'])
        df_mi = df_mi.append(df_dict[df])
    return df_mi

def get_current_date(new_date_time=18):
    """if current date is not pass new_date_time such as 18 (6pm)
       it will return previous trading day
    """
    current_time = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_date = int(current_time[:8])
    current_hour = int(current_time[9:11])
    print ('Current time: ' + str(current_time))
    fdate_list_dt = IO.read_data([20040101,20200101],ftype=FType.CALENDAR).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i,'%Y%m%d')) for i in fdate_list_dt]
    nearest_date = min(fdate_list, key=lambda x:abs(x-current_date) if x<=current_date else 100)
    if current_hour < new_date_time and nearest_date==current_date:
        print ('Not till refresh time '+str(new_date_time)+':00')
        current_date = fdate_list[fdate_list.index(current_date)-1]
        print ('Use previous trading date: '+str(current_date))
    elif nearest_date<current_date:
        current_date = nearest_date
    elif current_hour >= new_date_time and nearest_date==current_date:
        print ('Right on time: '+str(current_date))
    return current_date



def date_period_handler(sdate=None,edate=None):
    last_day = get_current_date()
    if sdate is None and edate is None:
        sdate = last_day
        edate = last_day
        print ('update for one day: '+str(sdate))
    if sdate is not None and edate is None:
        edate = last_day
    else:
        fdate_list_dt = IO.read_data([20040101,20200101],ftype=FType.CALENDAR).index.get_level_values(0)
        fdate_list = [int(dt.datetime.strftime(i,'%Y%m%d')) for i in fdate_list_dt]
        cdate_list = [i for i in fdate_list if i<=min(edate,last_day) and i>=sdate]
        sdate,edate = cdate_list[0],cdate_list[-1]
    return sdate,edate


def check_update_date(sdate=None,edate=None,use_len=None):
    #check_update_date(sdate=None,edate=None)
    use_len = 0 if use_len is None else use_len
    sdate,edate = date_period_handler(sdate,edate)
    fdate_list_dt = IO.read_data([20040101,20200101],ftype=FType.CALENDAR).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i,'%Y%m%d')) for i in fdate_list_dt]
    cdate_list = [i for i in fdate_list if i>=sdate and i<=edate]
    idx = max(0,fdate_list.index(cdate_list[0])-use_len)
    sdate_prev = fdate_list[idx]
    print ('-'*20,'\ndata used: %d - %d '%(sdate_prev,edate))
    print ('factor data: %d - %d \ntotal count: %d'%(sdate_prev,edate,len(cdate_list)))
    print ('-'*20)
    return sdate_prev,edate,cdate_list


def align_data(data_dict):
    i=0
    #dat_type = [type(data_dict[factor])for factor in data_dict]
    # get stock list, date list
    for factor in data_dict:
        if type(data_dict[factor])==pd.DataFrame:
            if i==0:
                stock_list = data_dict[factor].columns.tolist()
                date_list = data_dict[factor].index.tolist()
                i=i+1
            else:
                stock_list = np.intersect1d(stock_list,data_dict[factor].columns.tolist())
                date_list = np.intersect1d(date_list,data_dict[factor].index.tolist())
        elif type(data_dict[factor]) ==pd.Series:
            if i==0:
                date_list = data_dict[factor].index.tolist()
            else:
                date_list = np.intersect1d(date_list,data_dict[factor].index.tolist())

    # align dataframe and series
    data_dict_aligned = {}
    for factor in data_dict:
        #print (factor)
        if type(data_dict[factor])==pd.DataFrame:
            data_dict_aligned[factor] = data_dict[factor][stock_list].loc[date_list]
        elif  type(data_dict[factor]) ==pd.Series:
            data_dict_aligned[factor] = data_dict[factor].loc[date_list]
    return data_dict_aligned

def df_formatter(dataframe,factor_name):
    data_MI = pd.DataFrame(dataframe.stack(),columns=[factor_name])
    data_MI.index.names = ['dt','Ticker']
    return data_MI


#########################################################################################
"""因子数据处理部分"""

def FactorTypeCheck(factor_dict):
    """ 自动判别因子是否为1，0,-1 的标签矩阵"""
    max_min = [factor_dict.max().max(),factor_dict.min().min()]
    factor_type = 'Categorical' if max_min in [[0,-1],[0,1],[-1,1]] else 'Numerical'
    return factor_type


def Standard_Process(factor_dict,nan_ind,stock_industry,FillNaN=False):
    """ nan_ind:  可以根据用户输入决定筛选条件 - 比如VOLUME>0
        True： 1. 去除没有收益的日子
        False: 1. 去除没有收益的日子  2. 标准化
    """
    factor_type = FactorTypeCheck(factor_dict)
    if factor_type =='Categorical':  #不进行任何 因子清洗，填充
        print ('           Factor Type: Categorical --> No Standardization and FillingNA')
    elif factor_type =='Numerical':
        factor_dict[~nan_ind] = np.nan
        factor_dict[~np.isfinite(factor_dict)]=np.nan #将inf,-inf,nan 取代为nan
        #print ('           BoxSkewPlot Processing')
        factor_dict = BoxSkewPlot(factor_dict) #极值处理
        #print ('           Normalizing')
        if FillNaN == True:
            #print ('           Filling NaN with Industry Median...')
            factor_dict = Factor_Fillna(factor_dict,stock_industry,nan_ind)
        else:
            print ('           NaN not Filled')
        factor_dict = factor_dict.subtract(factor_dict.mean(axis=1),axis=0).divide(factor_dict.std(axis=1,ddof=0),axis=0) #handle nan
    return factor_dict

def DataNormalize(factor_dict):
    factor_dict = factor_dict.subtract(factor_dict.mean(axis=1),axis=0).divide(factor_dict.std(axis=1,ddof=0),axis=0)
    return factor_dict


def box_skew_algo(x):
    y = np.array(x)
    x = y[~np.isnan(y)]
    if len(np.unique(x)) < 10:
        return y
    x = np.sort(x)
    md = np.median(x)
    q3 = np.percentile(x,75)
    q1 = np.percentile(x,25)
    iqr = q3 - q1
    rx = np.flip(x, axis=0)
    x, rx = zip(*[(i, j) for i, j in zip(x, rx) if i!=j])
    x = np.split(np.array(x), 2)[1]
    rx = np.split(np.array(rx), 2)[1]
    if len(x) < 5:
        return y
    mc = np.median((x + rx - 2.0 * md) / (x - rx))
    a, b= (3.5, 4) if mc >= 0 else (4, 3.5)
    L = q1 - 1.5 * np.exp(-a * mc) * iqr
    U = q3 + 1.5 * np.exp( b * mc) * iqr
    y[np.array([item < L if not np.isnan(item) else False for item in y])] = L
    y[np.array([item > U if not np.isnan(item) else False for item in y])] = U
    return y

def BoxSkewPlot(pd_raw, axis=1):
    if type(pd_raw) == pd.DataFrame:
        # Return copy instead of original
        pd_process = pd_raw.copy()
        return pd_process.apply(box_skew_algo, axis=axis)
    else:
        raise AssertionError


def Factor_Fillna(factor_dict,stock_industry,nan_ind):
    """ 缺失值处理：
    得到新的因子暴露度序列后，将因子暴露度缺失的地方设为行业中位数。
    # 因子暴露度缺失定义为无法获取此因子 而非该股票不可交易  - 用处理过的因子填充
    # nan_ind 为股票停牌信息  1 为真停牌 或者没上市/ 则不填充

    """
    fill_ind = np.isnan(factor_dict)[~nan_ind] # 所有NAN * 非停牌的NAN = 缺失数据
    industry_median = pd.DataFrame(index=factor_dict.index,columns=[i for i in range(31)])
    for date in stock_industry.index:
        industry_list = stock_industry.loc[date]
        industry_median.loc[date] = [i[0] for i in pd.DataFrame(factor_dict.loc[date]).groupby(industry_list).median().values]
    Fill_median = factor_dict.copy()
    for i in [i for i in range(31)]:    # loop industry
        stock_in_industry  = industry_list[industry_list==i].index.tolist()
        Fill_median[stock_in_industry] = pd.DataFrame([industry_median[i].tolist()]*len(stock_in_industry)).T
    factor_dict[fill_ind==1]  =  Fill_median[fill_ind==1]
    return factor_dict

def Factor_Fillna_TS(factor_dict,holding_peiord):
    """如果数据不齐，则往回看多少天区间 取均值
       用于稀疏的财报数据矩阵
    """
    factor_fill = factor_dict.rolling(window=holding_peiord,min_periods=1).mean()
    return factor_fill



def np_regression_res(x,y):
    res = np.array([np.nan]*len(x))
    mask = np.isfinite(x) & np.isfinite(y.sum(axis=1))
    if len(mask)==0:
        return res
    ols1  = sm.OLS(x[mask],y[mask]).fit()
    res[mask] = ols1.resid
    return res

def factor_neutralize_mat(factor_dict,neutral_dict,neutral_list,Normalize=True):
    """
    Generic Version of Neutralizer - but still assume everything aligned
    data_dict: dictionary of dataframe
    Normalize: Choose to normalize residual cross sectionally

    """
    print ('-'*5+'   Get Factor Neutralized   '+'-'*5)
    tic = time.time()
    date_num, stock_num = factor_dict.shape
    factor_num = len(neutral_list)
    y_mat = np.ones([factor_num+1,date_num,stock_num]) # including intercept
    factor_mat = factor_dict.values
    for i in range(factor_num):
        y_mat[i,:,:] = neutral_dict[neutral_list[i]].values

    res = np.empty([date_num,stock_num])
    res[:] = np.nan
    for date_idx in range(date_num):
        try:
            res[date_idx,:] = np_regression_res(factor_mat[date_idx,:],y_mat[:,date_idx,:].T)
        except:
            continue
    factor_residual = pd.DataFrame(res,columns = factor_dict.columns,index=factor_dict.index)
    factor_residual = DataNormalize(factor_residual) if Normalize==True else factor_residual
    toc = time.time()
    print (str((round((toc-tic),2)))+'s ellapsed')
    print ('-'*20)
    return factor_residual


def weight_decay(half_life,total_len):  #其中n是半衰期，m是序列长度
    return [0.5**((total_len-i)/half_life) for i in range(total_len)]


"""Value"""
def date_checker(data_MI,cdate_list):
    """for MultiIndex"""
    date_check = data_MI.index.get_level_values(0).unique().tolist()
    date_check = [date_check] if type(date_check) != list else date_check
    no_date = list(set(cdate_list) - set(date_check))
    no_date.sort()
    if len(no_date)>0:
        raise Exception('No data for ',str(no_date))
    return no_date



# ~~~~~~~~~~~~~~~~~~~~~~~~~~

# def init_trading_day(h5_path=None):
    # h5_path = 'D:\\Quant\\data\\calendar\\CHINA_STOCK\\DAILY\\HTSC\\CALENDAR_CHINA_STOCK_DAILY_HTSC.h5' if h5_path==None else h5_path
    # forward_date = (dt.datetime.now()+dt.timedelta(days=1000)).strftime("%Y-%m-%d")
    # dat = w.tdays('1991-01-01',forward_date,'')
    # calendar_df = pd.DataFrame([dat.Data[0],len(dat.Data[0])*['CHINA'],[1]*len(dat.Data[0])],index=['dt','Ticker','calendar']).T
    # calendar_df.calendar = calendar_df.calendar.astype(int)
    # calendar_df = calendar_df.set_index(['dt','Ticker'])
    # IO.pd_hdf5_writer(calendar_df,h5_path,'china_stock_tradingDay')
    # IO.pd_hdf5_writer(calendar_df.iloc[:10],h5_path,'china_stock_tradingDay')
    # return None



def get_current_date(new_date_time=18):
    """if current date is not pass new_date_time such as 18 (6pm)
       it will return previous trading day
    """
    current_time = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_date = int(current_time[:8])
    current_hour = int(current_time[9:11])
    print('Current time: ' + str(current_time))
    fdate_list_dt = IO.read_data([20040101,20200101],ftype=FType.CALENDAR).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i,'%Y%m%d')) for i in fdate_list_dt]
    nearest_date = min(fdate_list, key=lambda x:abs(x-current_date) if x<=current_date else 100)
    if current_hour < new_date_time and nearest_date==current_date:
        print('Not till refresh time '+str(new_date_time)+':00')
        current_date = fdate_list[fdate_list.index(current_date)-1]
        print('Use previous trading date: '+str(current_date))
    elif nearest_date<current_date:
        current_date = nearest_date
    elif current_hour >= new_date_time and nearest_date==current_date:
        print('Right on time: '+str(current_date))
    return current_date


def date_period_handler(sdate=None,edate=None):
    last_day = get_current_date()
    if sdate is None and edate is None:
        sdate = last_day
        edate = last_day
        print('update for one day: '+str(sdate))
    if sdate is not None and edate is None:
        edate = last_day
    else:
        fdate_list_dt = IO.read_data([20040101,20200101],ftype=FType.CALENDAR).index.get_level_values(0)
        fdate_list = [int(dt.datetime.strftime(i,'%Y%m%d')) for i in fdate_list_dt]
        cdate_list = [i for i in fdate_list if i<=min(edate,last_day) and i>=sdate]
        sdate,edate = cdate_list[0],cdate_list[-1]
    return sdate,edate






def save_dt_list(cdate_list=None):
    save_name = 'D:\\Quant\\backtest\\local_data\\wind_data\\dt_list1.csv'
    cdate_list = [get_current_date(new_date_time=17)]
    fdate_list_dt = IO.read_data([20040101,20200101],ftype=FType.CALENDAR).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i,'%Y%m%d')) for i in fdate_list_dt]
    dt_list = fdate_list[:fdate_list.index(cdate_list[-1])+1]
    pd.DataFrame(fdate_list).to_csv(save_name)
    return


def int2date(date_int,date_format='%Y%m%d'):
    if np.isfinite(date_int):
        date_time = dt.datetime.strptime(str(int(date_int)),'%Y%m%d')
    else:
        date_time = date_int
    return date_time


