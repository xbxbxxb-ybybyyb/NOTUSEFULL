# -*- coding: utf-8 -*-
"""
BARRA STYLE FACTOR
Barra China Equity Model (CNE5) Empirical Notes - July 2012
SIZE/Beta/Momentum/Residual Volatility/Non-linear Size/Book-to-Price
Liquidity/Earnings Yield/Growth/Leverage

"""


import matplotlib.pyplot as plt  
import numpy as np
import pandas as pd
import statsmodels.api as sm
from multifactor.IO import IO
from multifactor.IO.IO_enums import *
import datetime as dt
from functools import reduce
import time as time
import json
import os


def median_filter(factor_df,mad=3,winsor=False):
    factor_dict = factor_df.copy()
    factor_mat = factor_dict.values
    #dm = np.nanmedian(factor_mat,axis=1)
    dm = factor_dict.median(axis=1)
    dm1 = (factor_dict.subtract(dm,axis=0)).abs().median(axis=1).values
    #dm1 = np.nanmedian(abs((factor_mat.T - dm).T),axis=1)
    date_num,stock_num = factor_mat.shape
    fac_ub = pd.DataFrame(np.tile(dm + mad * dm1,[stock_num,1]).T,index=factor_dict.index,columns=factor_dict.columns)
    fac_lb = pd.DataFrame(np.tile(dm - mad * dm1,[stock_num,1]).T,index=factor_dict.index,columns=factor_dict.columns)
    if winsor:
        factor_dict[factor_dict>fac_ub] = np.nan
        factor_dict[factor_dict<fac_lb] = np.nan
    else:
        factor_dict[factor_dict>fac_ub] = fac_ub
        factor_dict[factor_dict<fac_lb] = fac_lb
    return factor_dict

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
    fdate_list_dt = IO.read_data([20090101,20300101],ftype=FType.CALENDAR).index.get_level_values(0)
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
        fdate_list_dt = IO.read_data([20090101,20300101],ftype=FType.CALENDAR).index.get_level_values(0)
        fdate_list = [int(dt.datetime.strftime(i,'%Y%m%d')) for i in fdate_list_dt]
        cdate_list = [i for i in fdate_list if i<=min(edate,last_day) and i>=sdate]
        sdate,edate = cdate_list[0],cdate_list[-1]
    return sdate,edate


def check_update_date(sdate=None,edate=None,use_len=None):
    #check_update_date(sdate=None,edate=None)
    use_len = 0 if use_len is None else use_len
    sdate,edate = date_period_handler(sdate,edate)
    fdate_list_dt = IO.read_data([20090101,20300101],ftype=FType.CALENDAR).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i,'%Y%m%d')) for i in fdate_list_dt]
    cdate_list = [i for i in fdate_list if i>=sdate and i<=edate]
    idx = max(0,fdate_list.index(cdate_list[0])-use_len)
    sdate_prev = fdate_list[idx]
    print ('-'*20,'\ndata used: %d - %d '%(sdate_prev,edate))
    print ('factor data: %d - %d \ntotal count: %d'%(sdate_prev,edate,len(cdate_list)))
    print ('-'*20)
    return sdate_prev,edate,cdate_list


def load_md_data(cdate_list,data_length=600, align=True):
    end_date = cdate_list[-1]
    fdate_list_dt = IO.read_data([20090101,20300101],ftype=FType.CALENDAR).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i,'%Y%m%d')) for i in fdate_list_dt]
    data_length = data_length + len(cdate_list) 
    start_date = fdate_list[fdate_list.index(cdate_list[0])-min(data_length,len(fdate_list))]
    print ('-'*40,'\n Loading basic data for risk factor: ',str(start_date),'-',str(end_date))   
    dat = {}
    print ('Getting market data')
    index_list =['close','adjfactor','volume','turn']
    h5_data = IO.read_data([start_date,end_date],columns=index_list,ftype=FType.MD,dsource=DSource.WIND,max_workers=1)
    h5_data['close_adj'] = h5_data['close']*h5_data['adjfactor']
    dat['turn'] = h5_data['turn'].unstack()    
    dat['close_adj'] = h5_data['close_adj'].unstack()    
    dat['stock_return'] = dat['close_adj']/dat['close_adj'].shift(1)-1
    
    # get risk_universe
    print ('Getting risk universe data')
    #risk_ind = cu.get_stock_pool(start_date,end_date,universe_type='risk_universe',output_type='dataframe')
    risk_ind = IO.read_data([start_date,end_date],ftype=FType.UNIV,dsource=DSource.OPTM,columns=['risk_universe'])
    dat['risk_ind'] = risk_ind.unstack()['risk_universe']
    dat['risk_ind'] = dat['risk_ind'].fillna(False)
    
    print ('Getting benchmark data')
    benchmark_index = 'zz500'
    h5_index = IO.read_data([start_date,end_date],['close'],ftype=FType.MD,dtype=DType.INDEX,dsource=DSource.WIND,max_workers=1)
    index_lookup = {'zz500': '000905.SH', 'zz800': '000906.SH', 'sz50': '000016.SH', 'hs300': '000300.SH'}
    bmk_price =  (h5_index.unstack()['close'])[index_lookup[benchmark_index]]
    dat['benchmark_ret'] = bmk_price/bmk_price.shift(1)-1
    
    print ('Getting industry data')
    # 'industry_citiccode'
    h5_ind = IO.read_data([start_date,end_date],ftype=FType.INDUSTRY,dsource=DSource.WIND,columns=['CITIC_I'],max_workers=1) #CITIC Level 1 = Industry 3
    dat['industry'] = h5_ind[h5_ind.columns[0]].unstack()#['industry3']
    #h5_ind = IO.read_data([start_date,end_date],ftype=FType.INDUSTRY,dsource=DSource.WIND,columns=['industry_citiccode'],max_workers=1) #CITIC Level 1 = Industry 3
    #dat['industry'] = h5_ind.unstack()['industry_citiccode']    
    if align==True:
        print ('Align dataframe')
        dat = align_data(dat)
    print ('-'*40)
    return dat

def load_mkt_return(sdate,edate,data_length=600):
  
    #benchmark_index = 'zz500'
    h5_index = IO.read_data([sdate,edate],['close'],ftype=FType.MD,dtype=DType.INDEX,dsource=DSource.WIND,max_workers=1)
    index_lookup = {'zz500': '000905.SH', 'zz800': '000906.SH', 'sz50': '000016.SH', 'hs300': '000300.SH'}
    bmk_price =  (h5_index.unstack()['close'])[index_lookup[benchmark_index]]
    dat['benchmark_ret'] = bmk_price/bmk_price.shift(1)-1
    
    return     
    
    


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



"""数据清理过"""

def weight_decay(half_life,total_len):  #其中n是半衰期，m是序列长度
    return [0.5**((total_len-i)/half_life) for i in range(total_len)]


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
        #return pd_process.apply(box_skew_algo, axis=axis)
        return pd_raw.apply(lambda x: pd.Series(box_skew_algo(x), index=pd_raw.columns), axis=1)
    else:
        raise AssertionError 
        

def Factor_Fillna(factor_dict,stock_industry,nan_ind):
    """ 缺失值处理：
    得到新的因子暴露度序列后，将因子暴露度缺失的地方设为行业中位数。
    # 因子暴露度缺失定义为无法获取此因子 而非该股票不可交易  - 用处理过的因子填充
    # nan_ind 为股票停牌信息  1 为真停牌 或者没上市/ 则不填充
    
    """
    factor_dict = factor_dict.copy().astype(np.float64)
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



####################################################################################################

"""Risk Factor"""

"""Size"""
def risk_size_date(cdate_list,dat): 
    # out df format for later use
   
    cdate_list = [cdate_list] if type(cdate_list)!=list else cdate_list
    cdate_list.sort()
    print ('Risk Factor: Size  _','Total days:',len(cdate_list))
    date_take = [cdate_list[0],cdate_list[-1]] if len(cdate_list)>1 else cdate_list
    mkt_cap = IO.read_data(date_take,columns=['mkt_cap_ard'],ftype=FType.MD,dsource=DSource.WIND,max_workers=1)
    lncap = np.log(mkt_cap)['mkt_cap_ard'].unstack()
    dat_std = {**dat,**{'size':lncap}}
    dat_std = align_data(dat_std)
    print ('Standardizing')
    print(dat_std['industry'])
    size_std = Standard_Process(dat_std['size'],dat_std['risk_ind'],dat_std['industry'],FillNaN=True)
    return size_std
def NormWinsor(factor_df,bound=3,winsor=False):
    factor_dict = factor_df.copy()
    factor_dict = median_filter(factor_dict,mad=bound,winsor=winsor)
    std_ts = factor_dict.std(axis=1,ddof=0)
    std_ts[std_ts==0]=1
    factor_dict = factor_dict.subtract(factor_dict.mean(axis=1),axis=0).divide(std_ts,axis=0)
    return factor_dict


"""NonLinearSize"""
def risk_nlsize_date(cdate_list,size_std):
    """Non-linear Size
    # Cube of Szie 
    # First, the standardized Size exposure (i.e., log of market cap) is cubed. 
    # The resulting factor is then orthogonalized with respect to the Size factor on a regression-weighted basis. 
    # Finally, the factor is winsorized and standardized
    """
    print ('Risk Factor: NonLinearSize  _','Total days:',len(cdate_list))
    cut_list = [dt.datetime.strptime(str(i),'%Y%m%d') for i in cdate_list] if type(cdate_list)==list else str(cdate_list)
    size_cube = size_std.loc[cut_list]**3
    # size_cube_std = DataNormalize(size_cube)
    size_cube_std = NormWinsor(size_cube)
    # normailization in place / fillna already done by size_std
    size_cube_neu = factor_neutralize_mat(size_cube_std,{'size':size_std},['size'],Normalize=True)
    return size_cube_neu




"""Beta and Hsigma"""
def reg_beta_resvol(y,x,min_size=0):
    """assume y has constant term at the last column"""
    #res = np.array([np.nan]*len(x))   
    mask = np.isfinite(y) & np.isfinite(x.sum(axis=1))
    #mask = np.isfinite(x) & np.isfinite(y.sum(axis=1)) & nan_list
    if np.count_nonzero(mask) <= min_size:
        return np.nan,np.nan
    ols1  = sm.OLS(y[mask],x[mask]).fit()
    beta = ols1.params[0]
    res_vol = np.std(ols1.resid)
    #res[mask] = ols1.resid
    return beta,res_vol




def risk_RegMktBeta_date(cdate_list,dat,half_life=None,reg_period=None,min_size=None):
    print ('Risk Factor: Market Beta & Residual Volatility')
    half_life =63 if half_life==None else half_life
    reg_period =252 if reg_period==None else reg_period
    min_size = reg_period/4 if min_size==None else min_size
    ret_dataframe = dat['stock_return']
    benchmark_ret = dat['benchmark_ret']
    stock_list, date_list = ret_dataframe.columns.tolist(),ret_dataframe.index.tolist()
    date_num,stock_num = ret_dataframe.shape
    # cut for regression data based on date
    if type(cdate_list)!=list:
        cdate_list = [cdate_list]
    cdate_list = [dt.datetime.strptime(str(i),'%Y%m%d') for i in cdate_list]
    iter_num= len(cdate_list)
    beta_mat,resvol_mat = np.zeros([iter_num,stock_num]),np.zeros([iter_num,stock_num])
    beta_mat[:],resvol_mat[:] = np.nan, np.nan
    w = np.array([0.5**((reg_period-i)/half_life) for i in range(reg_period)]).T
    fail_list = []
    ret_mat = ret_dataframe.values
    bmk_dummy = np.vstack((benchmark_ret.values,np.ones(len(benchmark_ret)))).T
    for iter_n in range(iter_num):
        try:
            date_idx = date_list.index(cdate_list[iter_n])
            print (cdate_list[iter_n])
            Y = ret_mat[date_idx-reg_period+1:date_idx+1,:]
            X = bmk_dummy[date_idx-reg_period+1:date_idx+1,:]
            X_decay = (X.T*w).T
            Y_decay = (Y.T*w).T
            for i in range(stock_num):
                beta_mat[iter_n,i],resvol_mat[iter_n,i] = reg_beta_resvol(Y_decay[:,i],X_decay,min_size)
        except:
            print ('Not enough data')
            fail_list.append(cdate_list[iter_n])
    mkt_beta = pd.DataFrame(beta_mat,index=cdate_list,columns=stock_list)#.dropna(axis=0,how='all')
    hsigma = pd.DataFrame(resvol_mat,index=cdate_list,columns=stock_list)#.dropna(axis=0,how='all')  
    dat_std = {**dat,**{'mkt_beta':mkt_beta,'hsigma':hsigma}}
    dat_std = align_data(dat_std)
    print ('Normalizing')
    mkt_beta_std = Standard_Process(dat_std['mkt_beta'],dat_std['risk_ind'],dat_std['industry'],FillNaN=True)
    hsigma_std = Standard_Process(dat_std['hsigma'],dat_std['risk_ind'],dat_std['industry'],FillNaN=True)
    return mkt_beta_std,hsigma_std 



""" 4 # Volatility """

def dastd_date(cdate_list,dat,half_life,total_len): # 对 A 序列计算移动平均加权，其中权重对应 d,d-1,…,1（权重和为 1）
    """#DASTD
    # volatility of daily excess returns over the past 252 trading days with a half-life of 42 trading days.
    """    
    print ('DASTD')
    min_size = 10
    stock_list, date_list = dat['stock_return'].columns.tolist(),dat['stock_return'].index.tolist()
    date_num,stock_num = dat['stock_return'].shape
    # cut for regression data based on date
    if type(cdate_list)!=list:
        cdate_list = [cdate_list]
    iter_num= len(cdate_list)
    dastd_mat = np.zeros([iter_num,stock_num])
    dastd_mat[:] = np.nan
    w = np.array(weight_decay(half_life,total_len))
    cdate_list = [dt.datetime.strptime(str(i),'%Y%m%d') for i in cdate_list]
    for iter_n in range(iter_num):
        try:
            date_idx = date_list.index(cdate_list[iter_n])
            if date_idx >= total_len-1:
                print (cdate_list[iter_n])
                X = dat['stock_return'].iloc[date_idx-total_len+1:date_idx+1,:].values
                X_decay = (X.T*w).T
                take_ind = np.isfinite(X_decay).sum(axis=0) > min_size
                dastd_mat[iter_n,take_ind] = np.nanstd(X_decay[:,take_ind],axis=0)
        except:
            print ('Fail...')
    dastd_df = pd.DataFrame(dastd_mat,index=cdate_list,columns=stock_list).dropna(axis=0,how='all')
    dat_std = {**dat,**{'dastd':dastd_df}}
    dat_std = align_data(dat_std)
    print ('Normalize')
    dastd_std = Standard_Process(dat_std['dastd'],dat_std['risk_ind'],dat_std['industry'],FillNaN=True)        
    return dastd_std


def cmra_calc(X,cmra_period):
    #CMRA   - note use 12 month in rsch paper
    def MAX(A,B):
        C = A[A>=B]
        C[A<B] = B
        return C

    def MIN(A,B):
        C = A[A<=B]
        C[A>B] = B
        return C   
    logret = np.log(1+X)
   
    CMRA_MAX = logret.rolling(window=21).sum()
    CMRA_MIN = logret.rolling(window=21).sum()
    for i in range(1,cmra_period+1):
        print ('lag '+str(i)+' month')
        CMRA_MAX = MAX(logret.rolling(window=21*i).sum(),CMRA_MAX)
        CMRA_MIN = MIN(logret.rolling(window=21*i).sum(),CMRA_MIN)    
    CMRA_df = np.log(CMRA_MAX+1)-np.log(CMRA_MIN+1) # '600680.SH'
    return CMRA_df

def cmra_date(cdate_list,dat,cmra_period):
    print ('CMRA')
    min_date_num = 12*21
    stock_list, date_list = dat['stock_return'].columns.tolist(),dat['stock_return'].index.tolist()
    date_num,stock_num = dat['stock_return'].shape
    # cut for regression data based on date
    if type(cdate_list)!=list:
        cdate_list = [cdate_list]
    cdate_list = [dt.datetime.strptime(str(i),'%Y%m%d') for i in cdate_list]
    try:
        date_start_idx = date_list.index(cdate_list[0])
        date_start_idx = max(date_start_idx,min_date_num-1)
        date_end_idx = date_list.index(cdate_list[-1])
        iter_num = date_end_idx - date_start_idx + 1
        print ('Block compute for '+str(iter_num)+' days')
        if date_start_idx >= min_date_num-1:
            print ('Last day: '+str(cdate_list[-1]))
            X = dat['stock_return'].iloc[date_start_idx-min_date_num+1:date_end_idx+1,:]
            cmra_df = cmra_calc(X,cmra_period)
    except:
            print ('Fail...')
    cmra_df = cmra_df.iloc[-iter_num:,:]
    dat_std = {**dat,**{'cmra':cmra_df}}
    dat_std = align_data(dat_std)
    print ('Normalize')
    cmra_std = Standard_Process(dat_std['cmra'],dat_std['risk_ind'],dat_std['industry'],FillNaN=True)  
    return cmra_std



def risk_resid_vol_date(cdate_list,dat,hsigma_std,mkt_beta_std,size_std):
    print ('Risk Factor: Residual Volatility (0.74·DASTD + 0.16·CMRA + 0.10·HSIGMA)')
    cdate_list_dt = [dt.datetime.strptime(str(i),'%Y%m%d') for i in cdate_list]
    weight_resvol = [0.74,0.16,0.10]
    
    dastd_std = dastd_date(cdate_list,dat,half_life=42,total_len=252)
    cmra_std = cmra_date(cdate_list,dat,cmra_period=12)
    
    dat_std = {**dat,**{'dastd':dastd_std,'cmra':cmra_std,'hsigma':hsigma_std,'beta':mkt_beta_std,'size':size_std}}
    dat_std = align_data(dat_std)
    
    resid_vol = dat_std['dastd']*weight_resvol[0] + dat_std['cmra']*weight_resvol[1] + dat_std['hsigma']*weight_resvol[2]
    resid_vol_std = DataNormalize(resid_vol)
    
    neutral_list = ['size','beta']
    print ('Neutralize wrs to Size and Beta')
    resid_vol_neu_std = factor_neutralize_mat(resid_vol_std,dat_std,neutral_list,Normalize=True)
    resid_vol_neu_std = resid_vol_neu_std.loc[cdate_list_dt]
    return resid_vol_neu_std



""" Momentum - RSTR"""
# sum of excess log returns
def risk_momentum_date(cdate_list,dat,T,L,half_life): # 对 A 序列计算移动求和加权，其中权重对应 d,d-1,…,1（权重和为 1）
    """RSTR = sum{w*ln(1+rt)}(L,T+L) T=504,L=21,half_life=126"""
    # T,L,half_life = 504,21,126
    print ('Risk Factor: Momentum (1*RSTR)')
    stock_list, date_list = dat['stock_return'].columns.tolist(),dat['stock_return'].index.tolist()
    date_num,stock_num = dat['stock_return'].shape
    # cut for regression data based on date
    if type(cdate_list)!=list:
        cdate_list = [cdate_list]
    iter_num= len(cdate_list)
    rstr_mat = np.zeros([iter_num,stock_num])
    rstr_mat[:] = np.nan
    w = np.array(weight_decay(half_life,T-L))
    cdate_list = [dt.datetime.strptime(str(i),'%Y%m%d') for i in cdate_list]
    for iter_n in range(iter_num):
        try:
            
            date_idx = date_list.index(cdate_list[iter_n])
            if date_idx >= T:
                print (cdate_list[iter_n])
                X = dat['stock_return'].iloc[date_idx-T+1:date_idx-L+1,:].values
            #X_decay = (X.T*w).T
                rstr_mat[iter_n,:] = (((np.log(1+X)).T*w).T).sum(axis=0)
        except:
            print ('Fail...')
    rstr_df = pd.DataFrame(rstr_mat,index=cdate_list,columns=stock_list).dropna(axis=0,how='all')  
    dat_std = {**dat,**{'rstr':rstr_df}}
    dat_std = align_data(dat_std)
    rstr_std = Standard_Process(dat_std['rstr'],dat_std['risk_ind'],dat_std['industry'],FillNaN=True)             
    return rstr_std



"""Liquidity"""
def risk_liquidity_date(cdate_list,dat,size_std):
    """The Liquidity factor is orthogonalized with respect to Size to reduce collinearity"""
    print ('Risk Factor: Liquidity (0.35·STOM + 0.35·STOQ + 0.30·STOA)')
    min_date_num = 12*21
    turnover = dat['turn']
    stock_list, date_list = turnover.columns.tolist(),turnover.index.tolist()
    date_num,stock_num = turnover.shape
    # cut for regression data based on date
    if type(cdate_list)!=list:
        cdate_list = [cdate_list]
    cdate_list = [dt.datetime.strptime(str(i),'%Y%m%d') for i in cdate_list]
    try:
        date_start_idx = date_list.index(cdate_list[0])
        date_start_idx = max(date_start_idx,min_date_num-1)
        date_end_idx = date_list.index(cdate_list[-1])
        iter_num = date_end_idx - date_start_idx+1
        print ('Block compute for '+str(iter_num)+' days')
        if date_start_idx >= min_date_num-1:
            print ('Last day: '+str(cdate_list[-1]))
            X = turnover.iloc[date_start_idx-min_date_num+1:date_end_idx+1,:]
            weight_liq = [0.35,0.35,0.3]
            STOM_tmp = X.rolling(window=21,center=False).sum()
            STOQ_tmp = X.rolling(window=21*3,center=False).mean()*21
            STOA_tmp = X.rolling(window=21*12,center=False).mean()*21
            # remove inf, -inf for taking log
            STOM = np.log(STOM_tmp[STOM_tmp>0])
            STOQ = np.log(STOQ_tmp[STOQ_tmp>0])
            STOA = np.log(STOA_tmp[STOA_tmp>0])
            liquidity_df = weight_liq[0]*STOM + weight_liq[1]*STOQ + weight_liq[2]*STOA    
    except:
            print ('Fail...')
    liquidity_df  = liquidity_df.iloc[-iter_num:,:]
    liquidity_std = DataNormalize(liquidity_df)
    dat_std = {**dat,**{'size':size_std,'liquidity':liquidity_std}}
    dat_std = align_data(dat_std)
    print ('Neutralized wrs to size')
    liquidity_neu = factor_neutralize_mat(dat_std['liquidity'],dat_std,['size'],Normalize=False)
    print ('Normalization')
    liquidity_neu_std = Standard_Process(liquidity_neu,dat_std['risk_ind'],dat_std['industry'],FillNaN=True)
    return liquidity_neu_std




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



def risk_value_date(cdate_list,risk_source_data,dat):
    """note: use directly MI format input
    book_to_price = (tot_assets-tot_liab)/mkt_cap_ard"""
    print ('Risk Factor: Value')
    if type(cdate_list)!=list:
        cdate_list = [cdate_list]
    iter_num = len(cdate_list)    
    cdate_list = [dt.datetime.strptime(str(i),'%Y%m%d') for i in cdate_list]
    try:
        print ('Block compute for '+str(iter_num)+' days')
        print ('Last day: '+str(cdate_list[-1]))
        btop_MI = (risk_source_data['tot_assets']-risk_source_data['tot_liab'])/risk_source_data['mkt_cap_ard']/10000
        btop_df = btop_MI.unstack()
        #btop_MI = pd.DataFrame(btop_MI,columns=['btop']).dropna()
        dat_std = {**dat,**{'btop':btop_df}}
        dat_std = align_data(dat_std)
        print ('Normalize')
        btop_std = Standard_Process(dat_std['btop'],dat_std['risk_ind'],dat_std['industry'],FillNaN=True)
        btop_std = btop_std.loc[cdate_list]
    except:
            print ('Fail...')
    #date_checker(btop_MI,cdate_list)            
    return btop_std



def risk_leverage_date(cdate_list,risk_source_data,dat):
    
    """Leverage  = 0.38 · MLEV + 0.35 · DTOA + 0.27 · BLEV
    Note: 没有找到优先股账面价值 - 优先股 PE 不用 因为中国较少 - book value of preferred equity
    """
    """MLEV  = (ME+LD)/ME
    其中ME表示企业当前总市值，LD表示企业长期负债"""
    """note: use directly MI format input
    0.38 · MLEV + 0.35 · DTOA + 0.27 · BLEV
    MLEV(Market Leverage) = (ME+PE+LD)/ME = (mkt_cap_ard+tot_non_cur_liab/10000)/mkt_cap_ard
    DTOA(Debt-to-Assets) = tot_liab/tot_assets
    BLEV = (BE+PE+LD)/BE = (tot_equity+tot_non_cur_liab)/tot_equity
    
    note: BE could be tot_shrhldr_eqy_excl_min_int from wind
    # BE is the most recent book value of common equity 
    # PE is the most recent book value of preferred equity (NO DATA)
    # LD is the most recent book value of long-term debt
    """
    print ('Risk Factor: Leverage')
    leverage_weight = [0.38,0.35,0.27]
    if type(cdate_list)!=list:
        cdate_list = [cdate_list]
    iter_num = len(cdate_list)    
    cdate_list = [dt.datetime.strptime(str(i),'%Y%m%d') for i in cdate_list]
    try:
        print ('Block compute for '+str(iter_num)+' days')
        print ('Last day: '+str(cdate_list[-1]))
        MLEV = (risk_source_data['mkt_cap_ard']+risk_source_data['tot_non_cur_liab']/10000)/risk_source_data['mkt_cap_ard']
        DTOA = risk_source_data['tot_liab']/risk_source_data['tot_assets']
        BLEV = (risk_source_data['tot_equity']+risk_source_data['tot_non_cur_liab'])/risk_source_data['tot_equity'] 
        leverage_MI = MLEV*leverage_weight[0]+DTOA*leverage_weight[1]+BLEV*leverage_weight[2]
        leverage_df = leverage_MI.unstack()
        dat_std = {**dat,**{'leverage':leverage_df}}
        dat_std = align_data(dat_std)
        print ('Normalize')
        leverage_std = Standard_Process(dat_std['leverage'],dat_std['risk_ind'],dat_std['industry'],FillNaN=True)
        leverage_std = leverage_std.loc[cdate_list]
    except:
            print ('Fail...')
    #date_checker(leverage_MI,cdate_list)
    return leverage_std



def risk_growth_date(cdate_list,risk_source_data,dat):
    
    """Growth 
    # SGRO - Sales growth (trailing five years)     # yoy_tr 营业总收入(同比增长率)
    # EGRSF - Short-term predicted earnings growth  # 
    # EGRO - Earnings growth (trailing five years)  # yoynetprofit  
    # EGRLF - Long-term predicted earnings growth - Use 1-2 year predicted earning growth instead # CFS_c3
    # EGRSF - Short-term predicted earnings growth
    """
    print ('Risk Factor: Growth')
    weight_growth = [0.18,0.11,0.24,0.47]
    if type(cdate_list)!=list:
        cdate_list = [cdate_list]
    iter_num = len(cdate_list)    
    cdate_list = [dt.datetime.strptime(str(i),'%Y%m%d') for i in cdate_list]
    try:
        print ('Block compute for '+str(iter_num)+' days')
        print ('Last day: '+str(cdate_list[-1]))
        SGRO = risk_source_data['yoy_tr']
        EGRO = risk_source_data['yoynetprofit']
        # need for forecast growth
        # EGRLF - Long-term predicted earnings growth - Use 1-2 year predicted earning growth instead
        #EGRLF = pd.read_csv(data_path+'StyleFactor_Original\\Factors.CFS_c3.csv',header=-1)
        # EGRSF - Short-term predicted earnings growth
        growth_MI = (EGRO*weight_growth[2] + SGRO*weight_growth[3])/(1-weight_growth[2]-weight_growth[3])
        growth_df = growth_MI.unstack()
        dat_std = {**dat,**{'growth':growth_df}}
        dat_std = align_data(dat_std)
        print ('Normalize')
        growth_std = Standard_Process(dat_std['growth'],dat_std['risk_ind'],dat_std['industry'],FillNaN=True)
        growth_std = growth_std.loc[cdate_list]
    except:
            print ('Fail...')
    #date_checker(growth_MI,cdate_list)    
    return growth_std

def risk_earnings_yield_date(cdate_list,risk_source_data,dat):
    """Earnings Yield: 0.68 · EPFWD + 0.21 · CETOP + 0.11 · ETOP
   EPFWD: CFS_c1 一致预期EPS
   CETOP - Cash earnings-to-price ratio - wind      # dividendyield2
   ETOP: Trailing earnings-to-price ratio - wind    # pe_ttm
    """
    weight_ey = [0.68,0.21,0.11]
    if type(cdate_list)!=list:
        cdate_list = [cdate_list]
    iter_num = len(cdate_list)  
    cdate_list = [dt.datetime.strptime(str(i),'%Y%m%d') for i in cdate_list]
    try:
        print ('Block compute for '+str(iter_num)+' days')
        print ('Last day: '+str(cdate_list[-1]))
        #EPFWD = 
        CETOP = risk_source_data['dividendyield2']
        ETOP = 1/risk_source_data['pe_ttm']
        # need for forecast growth
        # EGRLF - Long-term predicted earnings growth - Use 1-2 year predicted earning growth instead
        #EGRLF = pd.read_csv(data_path+'StyleFactor_Original\\Factors.CFS_c3.csv',header=-1)
        # EGRSF - Short-term predicted earnings growth
        ey_MI= (CETOP*weight_ey[1] + ETOP*weight_ey[2])/(weight_ey[1]+weight_ey[2])  #(EPFWD*weight_ey[0] + 
        ey_df = ey_MI.unstack()
        dat_std = {**dat,**{'earnings_yield':ey_df}}
        dat_std = align_data(dat_std)
        print ('Normalize')
        ey_std = Standard_Process(dat_std['earnings_yield'],dat_std['risk_ind'],dat_std['industry'],FillNaN=True)
        ey_std = ey_std.loc[cdate_list]
    except:
        print ('Fail...')
    #date_checker(growth_MI,cdate_list)    
    return ey_std

def risk_industry_date(cdate_list,dat):
    cdate_list_dt = [dt.datetime.strptime(str(i),'%Y%m%d') for i in cdate_list]
    industry_MI = dat['industry'].loc[cdate_list_dt].stack()
    industry_MI = pd.DataFrame(industry_MI,columns=['Industry'])
    industry_MI = industry_MI.dropna()
    industry_MI.Industry = industry_MI.Industry.astype('int64')
    return industry_MI




def update_risk_factor_md(cdate_list=None):
    if cdate_list == None:
        cdate_list = [get_current_date(new_date_time=18)]
    else:
        cdate_list = [int(cdate_list)] if type(cdate_list) !=list else cdate_list
        
    h5_risk_std =  'S:\\Quant\\data\\risk\\CHINA_STOCK\\DAILY\\STYLEFACTOR\\risk_CHINA_STOCK_DAILY_STYLEFACTOR.h5'
    operation = 'append'
    op_type = None if operation=='create' else True
    
    IO.get_available_cols(alt=h5_risk_std)
        
    ####################################################################################################
    """Step 1. Load Basic data"""
    #fdate_list = tradingDay(20090101,last_day)
    cdate_list.sort()
    dat = load_md_data(cdate_list)

    
    ####################################################################################################
    """Step 2. Compute risk data"""

    """ Industry """
    industry_MI = risk_industry_date(cdate_list,dat)
    
    """ Size """
    size_std = risk_size_date(cdate_list,dat)
    size_std_MI = df_formatter(size_std,'Size')
    
    """ NonLinearSize"""
    NonLinearSize_df = risk_nlsize_date(cdate_list,size_std)
    NonLinearSize_MI = df_formatter(NonLinearSize_df,'NonLinearSize')
    
    """ Momentum """
    momentum_std = risk_momentum_date(cdate_list,dat,T=504,L=21,half_life=126)
    momentum_MI = df_formatter(momentum_std,'Momentum')
    
    """ Liquidity"""
    liquidity_neu_std = risk_liquidity_date(cdate_list,dat,size_std)
    liquidity_MI = df_formatter(liquidity_neu_std,factor_name='Liquidity')
    
    """ Beta """
    mkt_beta_std,hsigma_std  = risk_RegMktBeta_date(cdate_list,dat)
    mkt_beta_MI = df_formatter(mkt_beta_std,'Beta')
    
    """ ResidualVolatility """
    resid_vol_neu_std = risk_resid_vol_date(cdate_list,dat,hsigma_std,mkt_beta_std,size_std)
    resid_vol_MI = df_formatter(resid_vol_neu_std,'ResidualVolatility')
    
    """ Saving to H5 """
    IO.pd_hdf5_writer(industry_MI,h5_risk_std,'Industry',append=op_type)
    IO.pd_hdf5_writer(size_std_MI,h5_risk_std,'Size',append=op_type)
    IO.pd_hdf5_writer(NonLinearSize_MI,h5_risk_std,'NonLinearSize',append=op_type)
    IO.pd_hdf5_writer(momentum_MI,h5_risk_std,'Momentum',append=op_type)
    IO.pd_hdf5_writer(liquidity_MI,h5_risk_std,'Liquidity',append=op_type) 
    IO.pd_hdf5_writer(mkt_beta_MI,h5_risk_std,'Beta',append=op_type)    
    IO.pd_hdf5_writer(resid_vol_MI,h5_risk_std,'ResidualVolatility',append=op_type)    
    return 


def update_risk_factor_fdd(cdate_list=None):
    if cdate_list == None:
        cdate_list = [get_current_date(new_date_time=18)]
    else:
        cdate_list = [int(cdate_list)] if type(cdate_list) !=list else cdate_list
        
    h5_risk_std =  'S:\\Quant\\data\\risk\\CHINA_STOCK\\DAILY\\STYLEFACTOR\\risk_CHINA_STOCK_DAILY_STYLEFACTOR.h5'
    operation = 'append'
    op_type = None if operation=='create' else True
    
    IO.get_available_cols(alt=h5_risk_std)
        
    ####################################################################################################
    """Step 1. Load Basic data"""
    #fdate_list = tradingDay(20090101,last_day)
    cdate_list.sort()
    dat = load_md_data(cdate_list)
    ####################################################################################################
        
    """ Get risk fundamental data"""
    # daily data 
    print ('Getting risk fundamental data')
    start_date,end_date = cdate_list[0],cdate_list[-1]
    risk_source_list = ['tot_assets','tot_liab','tot_non_cur_liab','tot_equity','yoy_tr','yoynetprofit']
    risk_source = IO.read_data([start_date,end_date],risk_source_list,ftype=FType.FDD,dfreq=DFreq.DAILY,dsource=DSource.WIND,max_workers=1)
    
    mkt_cap_ard_MI = IO.read_data([start_date,end_date],columns=['mkt_cap_ard'],ftype=FType.MD,dsource=DSource.WIND,max_workers=1)
    risk_source_data = pd.concat([risk_source,mkt_cap_ard_MI],axis=1)
    
    risk_list2 = ['pe_ttm','dividendyield2']
    risk_source2 = IO.read_data([start_date,end_date],risk_list2,ftype=FType.FDD,dfreq=DFreq.DAILY,dsource=DSource.WIND,max_workers=1)
    
    #test_dat = IO.read_data([20090101,20180308],alt=h5_risk_std,columns=['Value'],max_workers=1)
    #np.isfinite(test_dat.unstack()).sum(axis=1).plot()

    """ Value """
    value_std = risk_value_date(cdate_list,risk_source_data,dat)
    value_MI = df_formatter(value_std,'Value')
    IO.pd_hdf5_writer(value_MI,h5_risk_std,'Value',append=op_type)

    #IO.hdf5_node_remover(h5_risk_std,'Value')
    #IO.pd_hdf5_writer(value_MI,h5_risk_std,'Value')
    
    
    """ Leverage """
    leverage_std = risk_leverage_date(cdate_list,risk_source_data,dat)
    leverage_MI = df_formatter(leverage_std,'Leverage')
    IO.pd_hdf5_writer(leverage_MI,h5_risk_std,'Leverage',append=op_type)
    
    #IO.hdf5_node_remover(h5_risk_std,'Leverage')
    #IO.pd_hdf5_writer(leverage_MI,h5_risk_std,'Leverage')

    
    """ Growth """
    growth_std = risk_growth_date(cdate_list,risk_source_data,dat)
    growth_MI = df_formatter(growth_std,'Growth')
    IO.pd_hdf5_writer(growth_MI,h5_risk_std,'Growth',append=op_type)

    #IO.hdf5_node_remover(h5_risk_std,'Growth')
    #IO.pd_hdf5_writer(growth_MI,h5_risk_std,'Growth')    
    
    """Earnings Yield"""
    ey_std = risk_earnings_yield_date(cdate_list,risk_source2,dat)
    ey_MI = df_formatter(ey_std,'EarningsYield')
    IO.pd_hdf5_writer(ey_MI,h5_risk_std,'EarningsYield',append=op_type)
    ####################################################################################################    
    return 

#sdate,edate = 20181101,20181106

def update_risk_factor_daily(sdate,edate,operation='append',
                             h5root = '/data/group/800080/warehouse/prod'):
    op_type = None if operation=='create' else True
    sdate_prev,edate,cdate_list = check_update_date(sdate,edate)
        
    h5_risk = os.path.join(h5root,'RISK','CHINA_STOCK','DAILY','STYLEFACTOR','RISK_CHINA_STOCK_DAILY_STYLEFACTOR.h5')
        
    ####################################################################################################
    """Step 1. Load Basic data"""
    dat = load_md_data(cdate_list,data_length=10)

    ####################################################################################################
    """Step 2. Compute risk data"""

    """ Industry """
    industry_MI = risk_industry_date(cdate_list,dat)
    
    """ Size """
    size_std = risk_size_date(cdate_list,dat)
    size_std_MI = df_formatter(size_std,'Size')
    
    """ Saving to H5 """
    IO.pd_hdf5_writer(industry_MI,h5_risk,'Industry',append=op_type)
    IO.pd_hdf5_writer(size_std_MI,h5_risk,'Size',append=op_type)
    return 

# update_risk_factor_daily(20200101,20200107)
