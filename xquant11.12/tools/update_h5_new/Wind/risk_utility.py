import numpy as np
import pandas as pd
import statsmodels.api as sm
import datetime as dt

from Wind.utils import *
import os
import pickle
import time
from concurrent.futures import ProcessPoolExecutor as Pool
from concurrent.futures import as_completed
from multiprocessing import Process, Manager
from log import Log

logger = Log("risk_utility")


h5_path_listing_delisting = '/app/data/wdb_h5/WIND_TEST/AShareDescription/AShareDescription.h5'

path_dict = {'wind':r'Z:\warehouse\prod\DATABASE\WIND',
             'derived':r'Z:\warehouse\prod\DATABASE',
             'suntime':'Z:\warehouse\prod\DATABASE\SUNTIME'}

xml_path = "./config-h5.xml"
sql_config = get_sql_config(xml_path)

def save_pickle(save_dict,save_path):
    print ('saving data to:\n',save_path)
    if os.path.exists(save_path):
        print ('remove existing one')
        os.remove(save_path)
    with open(save_path, 'wb') as input:
        pickle.dump(save_dict,input,protocol=pickle.HIGHEST_PROTOCOL)
    return 


def read_pickle(save_path=None):
    print('loading data from:  ', save_path)
    with open(save_path, 'rb') as input:
        save_dict = pickle.load(input)
    print('loading done...')
    return save_dict

def union(a, b):
    """ return the union of two lists """
    return list(set(a) | set(b))


def align_data_outer(data_dict):
    # maybe should use dt, Ticker instead
    i = 0
    for factor in data_dict:
        if np.any([isinstance(data_dict[factor], _type) for _type in [pd.DataFrame, pd.Series]]):
            if isinstance(data_dict[factor].index, pd.core.index.MultiIndex):
                if 'dt' in data_dict[factor].index.names:
                    if i == 0:
                        date_list = list(set(data_dict[factor].index.get_level_values(level=0).tolist()))
                        i = i + 1
                    else:
                        new_list = list(set(data_dict[factor].index.get_level_values(level=0).tolist()))
                        date_list = union(date_list, new_list)
            else:
                if type(data_dict[factor]) == pd.DataFrame:
                    if i == 0:
                        stock_list = data_dict[factor].columns.tolist()
                        date_list = data_dict[factor].index.tolist()
                        i = i + 1
                    else:
                        #stock_list = np.intersect1d(stock_list, data_dict[factor].columns.tolist())
                        #date_list = np.intersect1d(date_list, data_dict[factor].index.tolist())
                        stock_list = union(stock_list, data_dict[factor].columns.tolist())
                        date_list = union(date_list, data_dict[factor].index.tolist())
                        
                else:  # Series
                    if i == 0:
                        date_list = data_dict[factor].index.tolist()
                        i = i + 1
                    else:
                        date_list = union(date_list, data_dict[factor].index.tolist())
        elif type(data_dict[factor]) == dict:
            for nested_factor in data_dict[factor]:
                if type(data_dict[factor][nested_factor]) == pd.DataFrame:
                    if i == 0:
                        stock_list = data_dict[factor][nested_factor].columns.tolist()
                        date_list = data_dict[factor][nested_factor].index.tolist()
                        i = i + 1
                    else:
                        stock_list = union(stock_list, data_dict[factor][nested_factor].columns.tolist())
                        date_list = union(date_list, data_dict[factor][nested_factor].index.tolist())
        else:
            continue
    date_list.sort()
    stock_list.sort()
    data_dict_aligned = {}
    for factor in data_dict:
        if np.any([isinstance(data_dict[factor], _type) for _type in [pd.DataFrame, pd.Series]]):
            if isinstance(data_dict[factor].index, pd.core.index.MultiIndex):
                if 'dt' in data_dict[factor].index.names:
                    #data_dict_aligned[factor] = data_dict[factor].loc[date_list]
                    data_dict_aligned[factor] = data_dict[factor].reindex(index = date_list)
                    
            else:
                if type(data_dict[factor]) == pd.DataFrame:
                    #data_dict_aligned[factor] = data_dict[factor].loc[date_list, stock_list]
                    data_dict_aligned[factor] = data_dict[factor].reindex(index=date_list, columns=stock_list)
                else:
                    #data_dict_aligned[factor] = data_dict[factor].loc[date_list]
                    data_dict_aligned[factor] = data_dict[factor].reindex(index=date_list)
        elif type(data_dict[factor]) == dict:
            data_dict_aligned[factor] = {}
            for nested_factor in data_dict[factor]:
                if type(data_dict[factor][nested_factor]) == pd.DataFrame:
                    #data_dict_aligned[factor][nested_factor] = data_dict[factor][nested_factor].loc[date_list, stock_list]
                    data_dict_aligned[factor][nested_factor] = data_dict[factor][nested_factor].reindex(index=date_list, columns=stock_list)
    return data_dict_aligned



def get_growth_rate(y,scale=True):
    num = len(y)
    mask = np.isfinite(y)
    if np.count_nonzero(mask)<num*0.5:
        return np.nan
    x_dummy = np.array([i for i in range(1,num+1)])
    ols1  = sm.OLS(y[mask],x_dummy[mask]).fit()
    growth_rate = ols1.params[0]
    if scale:
        mean_val = np.nanmean(y)
        if mean_val == 0:
            growth_rate = np.nan    
        else:
            growth_rate = growth_rate/mean_val
    return growth_rate

def get_qtr_end_data(data_daily):
    date_list = data_daily.index.tolist()
    start_date,end_date = date_list[0], date_list[-1]
    take_time = [pd.Timestamp(y,m,30+int(np.abs(m-6)>3)) for y in range(2000,2099) for m in [3,6,9,12]]
    take_time = [i for i in take_time if i >= date_list[0] and i <= date_list[-1]]
    take_time.sort()
    full_day_range = pd.date_range(start=start_date, end=end_date, freq='1D')
    data_daily_full = data_daily.reindex(index=full_day_range)
    data_daily_full = data_daily_full.fillna(method='ffill')
    data_qtr_end = data_daily_full.reindex(index=take_time)
    data_qtr_end.index.names = data_daily.index.names
    return data_qtr_end

def get_qtr_list(sdate,edate,num_qtr=None):
    if isinstance(sdate,pd.Timestamp):
        sdate = int(dt.datetime.strftime(sdate,'%Y%m%d'))
    if isinstance(edate,pd.Timestamp):
        edate = int(dt.datetime.strftime(edate,'%Y%m%d'))
    if not isinstance(sdate,int):
        raise Exception
    if not isinstance(edate,int):
        raise Exception
    year_list = [str(i) for i in range(2000,2050)]
    month_date = ['0331','0630','0930','1231']
    date_list_complete = [int(i+j) for i in year_list for j in month_date]
    qtr_list = [i for i in date_list_complete if i<=edate and i>=sdate]
    if len(qtr_list)==0:
        qtr_list = [i for i in date_list_complete if i<=edate][-1:]
    if num_qtr is not None:
        if isinstance(num_qtr,int):
            start_idx = date_list_complete.index(qtr_list[0])
            pre_qtr = date_list_complete[start_idx-num_qtr:start_idx]
            qtr_list = pre_qtr + qtr_list
            qtr_list.sort()
        else:
            logger.info('input error: num_qtr not integer')
            raise Exception
    return qtr_list


def dt_parser(date):
    date_obj = dt.datetime.strptime(str(int(date)),'%Y%m%d')
    return date_obj

def easy_fill(factor_data,start_date,end_date,foward_date,fill_method='ffill'):
    start_date = str_date_parser(start_date)
    end_date = str_date_parser(end_date)
    factor_fill = factor_data.copy().reset_index().sort_values(by='dt').dropna()
    if isinstance(factor_fill[foward_date].values[0],int) or isinstance(factor_fill[foward_date].values[0],float):
        factor_fill[foward_date] = factor_fill[foward_date].apply(dt_parser)
    # aggregate same datewith different ammount
    factor_fill = factor_fill.groupby([foward_date, 'Ticker']).sum()
    #div_dat = div_dat.drop_duplicates(subset=['EX_DT', 'Ticker'], keep='last')
    factor_fill = factor_fill[factor_fill.columns[0]].unstack()
    full_day_range = pd.date_range(start=start_date, end=end_date, freq='1D')
    if fill_method is None:
        factor_fill = factor_fill.reindex(index=full_day_range)
    else:
        factor_fill = factor_fill.reindex(index=full_day_range).fillna(method=fill_method)
    factor_fill = factor_fill.reindex(index=get_trading_date_range(start_date, end_date))
    return factor_fill     

def get_wind_path(wind_db_path=path_dict):
    if isinstance(wind_db_path,dict):
        path_dict = {}
        for k in wind_db_path:
            tmp_dict = {i:os.path.join(wind_db_path[k],i,i+'.h5') for i in os.listdir(wind_db_path[k])}
            path_dict.update(tmp_dict)
    elif isinstance(wind_db_path,str):
        path_dict = {i:os.path.join(wind_db_path,i,i+'.h5') for i in os.listdir(wind_db_path)}
    return path_dict 
        

def factor_tank_date_slice(factor_tank,cdate_list):
    logger.info('slice date range: %s - %s'%(cdate_list[0],cdate_list[-1]))
    if isinstance(cdate_list[0],pd.Timestamp):
        cdate_list_dt = cdate_list
    else:
        cdate_list_dt = [dt.datetime.strptime(str(i),'%Y%m%d') for i in cdate_list]
    factor_tank_sliced = {}
    for fac in factor_tank:
        factor_tank_sliced[fac] = factor_tank[fac].loc[cdate_list_dt]
        factor_tank_sliced[fac] = factor_tank_sliced[fac].dropna(how='all')
        date_diff = list(set(cdate_list_dt) - set(factor_tank_sliced[fac].index.tolist()))
        date_diff.sort()
        lack_num = len(date_diff)
        if lack_num>0:
            logger.info('%s - has no data for %d days: %s - %s '%(fac,lack_num,date_diff[0],date_diff[-1]))
            raise Exception
    return factor_tank_sliced


def dict_slicer(factor_tank,sdate,edate):
    sdate,edate = str_date_parser(sdate),str_date_parser(edate)
    factor_tank_sliced = {}
    for fac in factor_tank:
        if isinstance(factor_tank[fac],pd.DataFrame) or isinstance(factor_tank[fac],pd.Series):
            factor_tank_sliced[fac] = factor_tank[fac].loc[sdate:edate]
        if isinstance(factor_tank[fac],dict):
            factor_tank_sliced[fac] = {}
            for sub in factor_tank[fac]:
                sub_data = factor_tank[fac][sub]
                if isinstance(sub_data,pd.DataFrame) or isinstance(sub_data,pd.Series):
                    factor_tank_sliced[fac][sub] = sub_data.loc[sdate:edate]
                if isinstance(sub_data,list):
                    if not isinstance(sub_data[0],pd.Timestamp):
                        factor_tank_sliced[fac][sub] = [i for i in sub_data
                                                   if pd.Timestamp(str(i))>=sdate and pd.Timestamp(str(i))<=edate]
                    else:
                        factor_tank_sliced[fac][sub] = [i for i in sub_data if i>=sdate and i<=edate]
        if isinstance(factor_tank[fac],list):
            if not isinstance(factor_tank[fac][0],pd.Timestamp):
                factor_tank_sliced[fac] = [i for i in factor_tank[fac] if pd.Timestamp(str(i))>=sdate and pd.Timestamp(str(i))<=edate]
            else:
                factor_tank_sliced[fac] = [i for i in factor_tank[fac] if i>=sdate and i<=edate]
    return factor_tank_sliced


def save_factor_tank(factor_tank,save_path,append,from_scratch,cdate_list=None):
    # h5 = os.path.split(save_path)
    # h5_name = h5[-1][:-3]
    # if h5_name == "RISK_CHINA_STOCK_DAILY_STYLEFACTOR" and cdate_list:
    #     date = max(cdate_list)
    # else:
    #     date = None
    factor_list = list(factor_tank.keys())
    factor_list.sort()
    factor_num = len(factor_list)
    if cdate_list is not None and not from_scratch:
        factor_tank = factor_tank_date_slice(factor_tank,cdate_list)
    for i in range(factor_num):
        factor_name = factor_list[i]
        logger.info('%d/%d - %s'%(i+1,factor_num,factor_name))
        data = pd.DataFrame(factor_tank[factor_name].stack(), columns=[factor_name])
        data.index.names = ['dt', 'Ticker']
        pd_hdf5_writer(data, save_path, factor_name,append=append, from_scratch=from_scratch)
    return

def standard_process(pd_raw, stock_filter=None, stock_industry=None, winsor=True, weight=None,date_complete=False):
    pd_raw = pd_raw.copy()
    pd_raw = pd_raw.reindex(index = stock_filter.index, columns=stock_filter.columns)
    date_lack = list(set(stock_filter.index) - set(pd_raw.dropna(axis=0,how='all').index))
    date_lack.sort()
    lack_num = len(date_lack)
    if lack_num>0:
        logger.info('data empty for %d days: %s - %s'%(lack_num,date_lack[0],date_lack[1]))
        if date_complete:
            raise Exception
    pd_raw[~np.isfinite(pd_raw)] = np.nan
    if stock_filter is not None:
        pd_raw[~stock_filter] = np.nan # stock_filter: true ~ exist
        if stock_industry is not None:
            pd_raw = factor_fillna_industry(pd_raw, stock_filter, stock_industry, inplace=False)
    pd_raw = norm_winsor(pd_raw, winsor=winsor,weight=weight)
    return pd_raw

def norm_winsor(factor_pd, universe=None, bound=5, winsor=False,weight=None):
    # obviously input date should not be altered without notice
    factor_winsor = median_filter(factor_pd, mad=bound, winsor=winsor, inplace=False)
    factor_norm = factor_normilize(factor_winsor, weight)
    return factor_norm

def factor_normilize(factor_pd,weight=None):
    std_ts = factor_pd.std(axis=1, ddof=0)
    std_ts.loc[std_ts == 0] = 1
    if weight is None:
        mean_ts = factor_pd.mean(axis=1)
    else:
        weight_norm = weight.divide(weight.sum(axis=1), axis=0)
        mean_ts = (factor_pd*weight_norm).sum(axis=1)
    return factor_pd.subtract(mean_ts, axis=0).divide(std_ts, axis=0)

def median_filter(factor_pd, mad=5, winsor=False, inplace=False):
    if not inplace:
        factor_pd = factor_pd.copy()
    dm = factor_pd.median(axis=1)
    # caution of symmetric uppper & lower bounds
    dist_pd = factor_pd.subtract(dm, axis=0).abs()
    dist_dm = dist_pd[dist_pd > 0].median(axis=1)
    date_num, stock_num = factor_pd.shape
    fac_ub = pd.DataFrame(np.tile(dm + mad * dist_dm, [stock_num, 1]).T, index=factor_pd.index,
                          columns=factor_pd.columns)
    fac_lb = pd.DataFrame(np.tile(dm - mad * dist_dm, [stock_num, 1]).T, index=factor_pd.index,
                          columns=factor_pd.columns)
    if winsor:
        factor_pd[factor_pd > fac_ub] = np.nan
        factor_pd[factor_pd < fac_lb] = np.nan
    else:
        factor_pd[factor_pd > fac_ub] = fac_ub
        factor_pd[factor_pd < fac_lb] = fac_lb
    if not inplace:
        return factor_pd


def factor_fillna_industry(pd_raw, stock_filter, stock_industry, inplace=False):
    # all inputs are in shape of DataFrame: dates, stocks
    # np.nans in pd_raw which are "True" in stock_filter are filled by industry median
    if not inplace:
        pd_raw = pd_raw.copy()
    fill_indicator = np.isnan(pd_raw) & (stock_filter == True)
    industry_universe = [i + 1 for i in range(int(stock_industry.max().max()))]
    industry_median = pd.DataFrame(index=pd_raw.index, columns=industry_universe, dtype=np.float64)
    for row in stock_industry.itertuples():
        date = row[0]
        industry_list = np.array(row[1:])
        industry_median.loc[date] = pd_raw.loc[date].groupby(industry_list).median()
        # industry_mask = np.isfinite(industry_list)
        # industry_median.loc[date] = pd_raw.loc[date,industry_mask].groupby(industry_list[industry_mask]).median()
    stock_number = pd_raw.shape[1]
    for ind in industry_universe:
        pd_raw[(stock_industry == ind) & fill_indicator] = np.tile(industry_median[ind], (stock_number, 1)).T
    if not inplace:
        return pd_raw


def regression_ols(y, x, weight=None):
    # calculate ols problem given y as DataFrame and x as dictionary with DataFrames of regressors
    assert (isinstance(x, dict))
    date_num, stock_num = y.shape
    x_list = list(x.keys())
    contains_industry = True if 'Industry' in x_list else False
    x_num = len(x_list) - 1 if contains_industry else len(x_list)
    x_mat = np.ones([x_num, date_num, stock_num])
    y_mat = np.array(y)
    r2_mat = np.empty(date_num)
    r2_mat[:] = np.nan
    beta_mat = np.empty([date_num, x_num + 1])
    beta_mat[:] = np.nan
    tstats_mat = beta_mat.copy()
    res_mat = np.full_like(y, np.nan, dtype=np.double)

    if weight is not None:
        w_mat = np.array(weight)

    if contains_industry:
        ind_mat = np.array(x['Industry'])
        x_list.remove('Industry')
    i = 0
    for x_name in x_list:
        x_mat[i, :, :] = np.array(x[x_name])
        i = i + 1

    for date_idx in range(date_num):
        if contains_industry:
            ind_dum = pd.get_dummies(ind_mat[date_idx, :]).values
            _x = np.column_stack([x_mat[:, date_idx, :].T, ind_dum])
        else:
            _x = x_mat[:, date_idx, :].T
        try:
            if weight is None:
                res_mat[date_idx, :], r2_mat[date_idx], beta_mat[date_idx, :], tstats_mat[date_idx, :] = stats_model_ols(y_mat[date_idx, :], _x)
            else:
                res_mat[date_idx, :], r2_mat[date_idx], beta_mat[date_idx, :], tstats_mat[date_idx, :] = stats_model_ols(y_mat[date_idx, :], _x, w_mat[date_idx,:])
        except ValueError:
            pass

    res = pd.DataFrame(res_mat, columns=y.columns, index=y.index)
    r2 = pd.Series(r2_mat, index=y.index)
    beta = pd.DataFrame(beta_mat, columns=['intercept']+x_list, index=y.index)
    tstats = pd.DataFrame(tstats_mat, columns=['intercept']+x_list, index=y.index)
    return res, r2, beta, tstats

def rolling_ts_regression(x, y, look_back_days, half_life=None, x_type='macro', ufunc=np.nanstd,parallel=False):
    # assume x with dimension (n, l) or (n, m)
    # assume y with dimension (n, m)
    # n is date number, m is stock number, l is macro feature number
    # if l == m, assume x, y are two factors for ts regression
    assert isinstance(x, np.ndarray) and isinstance(y, np.ndarray)
    w = weight_decay(half_life, look_back_days) if half_life is not None else 1
    date_num, stock_num = x.shape[0], y.shape[1]
    res_calc = np.full_like(y, np.nan, dtype=np.double)
    rsquared = np.full_like(y, np.nan, dtype=np.double)
    if x_type == 'macro':
        beta = np.full_like(np.empty((date_num, stock_num, x.shape[1]+1)), np.nan, dtype=np.double)
        tvalues = np.full_like(np.empty((date_num, stock_num, x.shape[1]+1)), np.nan, dtype=np.double)
    else:
        beta = np.full_like(np.empty((date_num, stock_num, 2)), np.nan, dtype=np.double)
        tvalues = np.full_like(np.empty((date_num, stock_num, 2)), np.nan, dtype=np.double)
    if date_num < look_back_days:
        raise AssertionError('date number less than required')
    tot_iter = date_num - look_back_days + 1
    if parallel:
        iter_list = [i for i in range(tot_iter)]
        #res = ts_regression_iter(i,x,y,look_back_days)
        res_dict = multiprocess_wrapper(func=ts_regression_iter,iter_list=iter_list,
                                         x=x,y=y,look_back_days=look_back_days,half_life=half_life,
                                         x_type=x_type,ufunc=ufunc,collect_output=True)
        for i in iter_list:
            res_calc[i+look_back_days-1, :] =  res_dict[i][i][0]
            rsquared[i+look_back_days-1, :] = res_dict[i][i][1]
            beta[i+look_back_days-1, :, :] = res_dict[i][i][2]
            tvalues[i+look_back_days-1, :, :] = res_dict[i][i][3]
    else:
        for i in range(tot_iter):
            if tot_iter > 1:
                logger.info('%d/%d' % (i + 1, tot_iter))
            X = x[i:i + look_back_days, :]
            Y = y[i:i + look_back_days, :]
            if half_life is None:
                X_decay = X
                Y_decay = Y
            else:
                X_decay = (X.T * w).T
                Y_decay = (Y.T * w).T
            for j in range(stock_num):
                #if j%100 ==0:
                #    print ('%d/%d'%(j,stock_num))
                if x_type == 'macro':
                    _res, _rsquared, _beta, _tvalues = stats_model_ols(Y_decay[:, j], X_decay)
                else:
                    _res, _rsquared, _beta, _tvalues = stats_model_ols(Y_decay[:, j], X_decay[:, j])
                res_calc[i+look_back_days-1, j] = ufunc(_res)
                rsquared[i+look_back_days-1, j] = _rsquared
                beta[i+look_back_days-1, j, :] = _beta
                tvalues[i+look_back_days-1, j, :] = _tvalues
    return res_calc, rsquared, beta, tvalues

def ts_regression_iter(i,x,y,look_back_days,**kwargs):
    X = x[i:i+look_back_days, :]
    Y = y[i:i+look_back_days, :]
    iter_dict = {i:rolling_ts_regression(X, Y, look_back_days,**kwargs)}
    res = {i:[j[-1] for j in iter_dict[i]]}
    return res
       
def weight_decay(half_life, total_len):
    # return exponential weights with last element the biggest
    res = np.array([0.5 ** ((total_len - i) / half_life) for i in range(total_len)])
    return res / np.sum(res)


def stats_model_ols(y, x, weight=None, min_percentage=10):
    res = np.full_like(y, np.nan, dtype=np.double)
    if weight is None:
        mask = np.isfinite(y + x.sum(axis=1))
    else:
        mask = np.isfinite(y + x.sum(axis=1) + weight)
    if np.count_nonzero(mask) / len(mask) * 100 < min_percentage:
        rsq = np.nan
        reg_params = np.full_like(x.sum(axis=0),np.nan,dtype=np.double)
        reg_tvalues = np.full_like(x.sum(axis=0),np.nan,dtype=np.double)
        return res,rsq,reg_params,reg_tvalues
    if weight is None:        
        reg = resider(x[mask], y[mask], method='sm.OLS', add_const=True, mean_only=False, r_square=False, return_sm=True)
    else:
        reg = resider(x[mask], y[mask], weight[mask], method='sm.WLS', add_const=True, mean_only=False, r_square=False, return_sm=True)
    res[mask] = reg.resid
    return res, reg.rsquared, reg.params, reg.tvalues


def rolling_ewma(pd_raw, window, halflife, ufunc='mean',min_percentage=0.5, fillna=False):
    pd_raw = pd_raw.fillna(0) if fillna else pd_raw
    pd_roll = pd_raw.rolling(window, min_periods=int(window * min_percentage))
    if ufunc == 'mean':
        apply_func = lambda x: pd.DataFrame(x).ewm(halflife=halflife).mean().tail(1).values
    elif ufunc == 'std':
        apply_func = lambda x: pd.DataFrame(x).ewm(halflife=halflife).std().tail(1).values
    elif ufunc == 'sum':
        apply_func = lambda x: pd.DataFrame(x).ewm(halflife=halflife).mean().tail(1).values * window
    else:
        logger.info('ufunc error %s' % (ufunc))
        raise Exception
    return pd_roll.apply(apply_func)


def weight_decay(half_life,total_len):  #其中n是半衰期，m是序列长度
    """last one has highest weight , half life = time to reach 0.5, weight is normalized"""
    weight_list_raw = [0.5**((total_len-i)/half_life) for i in range(total_len)]
    return weight_list_raw/np.sum(weight_list_raw)

def weighted_std(values, weights):
    """ Return the weighted average and standard deviation.
        values, weights -- Numpy ndarrays with the same shape."""
    avg = np.average(values, weights=weights)
    std = np.sqrt(np.average((values-avg)**2, weights=weights))
    return std

def np_std_weighted(value,weight,axis=0,min_pct=0.5):
    row_num,col_num = value.shape
    mask_mat = np.isfinite(value+weight)
    if axis ==1: # agg by horizontal - remain row - date
        mask_row = np.count_nonzero(mask_mat,axis=1) >= col_num * min_pct
        res = np.full_like(value.sum(axis=1),fill_value=np.nan,dtype=np.float)
        for i in range(row_num):
            if mask_row[i]:
                current_mask = mask_mat[i,:]
                res[i] = weighted_std(value[i,current_mask],weight[i,current_mask])
        
    elif axis ==0: # agg by vertial - remain col - stk 
        res = np.full_like(value.sum(axis=0),fill_value=np.nan,dtype=np.float)
        mask_col = np.count_nonzero(mask_mat,axis=0) >= row_num * min_pct
        for j in range(col_num):
            if mask_col[j]:
                current_mask = mask_mat[:,j]
                res[j] = weighted_std(value[current_mask,j],weight[current_mask,j])
    return res

def EWMA(df,roll_num,half_life,ufunc='mean',min_pct=0.5,min_weight=0.5): # 计算A 前n 期样本加权平均值权重为0.9i，(i 表示样本距离当前时点的间隔)
    """ if weight used is less than 0.5, discard
        min_pct check for data count
    """
    if ufunc not in ['mean','sum','std']:
        raise AssertionError
    weight = weight_decay(half_life,roll_num)
    min_size = int(np.ceil(min_pct*roll_num))
    row_num,col_num = df.shape
    x_mat = df.values
    y_mat = np.full_like(df,fill_value=np.nan,dtype=np.float)
    dummy_weight = (np.ones([roll_num,col_num]).T*weight).T
    for i in range(roll_num,row_num+1): # nan block   day*stock
        x_sliced = x_mat[i-roll_num:i,:]
        x_mask = np.isfinite(x_sliced)
        use_ind = np.count_nonzero(x_mask,axis=0)>=min_size
        weight_used = (x_mask*dummy_weight).sum(axis=0)
        weight_ind = weight_used >= min_weight
        x_use = x_sliced*dummy_weight
        mask = use_ind & weight_ind
        #x_use = (x_sliced.T * weight).T
        if ufunc in ['mean','sum']:
            y_mat[i-1,mask] = np.nansum(x_use[:,mask],axis=0)/weight_used[mask]
        elif ufunc == 'std':
            y_mat[i-1,:] = np_std_weighted(x_sliced,dummy_weight,axis=0,min_pct=min_pct)
    res = pd.DataFrame(y_mat,index=df.index,columns=df.columns)
    if ufunc == 'sum':
        res = res * roll_num
    #df_ewma = df.rolling(roll_num,min_periods).apply(lambda x: pd.Series(x).ewm(halflife=half_life).mean().values[-1])
    return res              


def resider(x, y, weight=None, method='lstsq', add_const=True, mean_only=False, r_square=False, return_sm=False):
    # Two step regression
    # 1: Determine dummy columns in matrix and use them to remove mean
    # 2: Regular ols: OLS or least square to calculate residual
    # Direct OLS or least square may have problems with dummy columns with few 1s
    # Less computation and more robustness
    # x -> axis0: stocks, axis1: factors
    y = y.flatten()  # 1-D array
    dummy_cols = np.apply_along_axis(is_dummy, 0, x)
    d_array = x[:, dummy_cols]
    s_array = x[:, ~dummy_cols]
    r2 = np.nan
    if d_array.shape[1] != 0:
        d_mean_array = np.array([i / j if j != 0 else 0 for i, j in
                                 zip(np.dot(d_array.T, y).flatten(), d_array.sum(axis=0))])
        y = y - np.dot(d_array, d_mean_array)
    if not mean_only and s_array.shape[1] != 0:
        if method == 'lstsq':
            if add_const:
                # Prepend constant in accordance with sm.OLS
                x = np.concatenate((np.ones((s_array.shape[0], 1)), s_array), axis=1)
            else:
                x = s_array
            try:
                coeff, residual_sum = np.linalg.lstsq(x, y, rcond=None)[0:2]
                resid = y - np.dot(x, coeff)
                if r_square:
                    r2 = 1 - residual_sum[0] / (y.size * y.var())
            except:
                resid = np.full_like(y, np.nan, dtype=np.double)
        elif method in ['sm.OLS','sm.WLS']:
            x = sm.add_constant(s_array) if add_const else s_array
            try:
                if method == 'sm.OLS':
                    ols_problem = sm.OLS(y, x).fit()
                elif method == 'sm.WLS':
                    ols_problem = sm.WLS(y, x).fit()
                if return_sm:
                    return ols_problem
                resid = ols_problem.resid
                if r_square:
                    r2 = ols_problem.rsquared
            except:
                resid = np.full_like(y, np.nan, dtype=np.double)
        else:
            raise AssertionError
    else:
        resid = y
    if r_square:
        return resid, r2
    else:
        return resid


def is_dummy(x):
    x = np.array(x) if not isinstance(x, np.ndarray) else x
    one_num = np.count_nonzero(x == 1)
    zero_num = np.count_nonzero(x == 0)
    if one_num + zero_num == x.size:
        return True
    else:
        return False
    



####################################################################################################################
""" backfill """

def issuing_date_checker(issuing_date_ps):
    # remove issuing dates not in the ascending order
    # eg: annual report later than 1st quarter report, remove annual report issuing date
    # caution: DataFrame & timedelta comparison is buggy
    lookup_dict = {3: pd.Timestamp(1900, 4, 30) - pd.Timestamp(1900, 3, 31),
                   6: pd.Timestamp(1900, 8, 31) - pd.Timestamp(1900, 6, 30),
                   9: pd.Timestamp(1900, 10, 31) - pd.Timestamp(1900, 9, 30),
                   12: pd.Timestamp(1901, 4, 30) - pd.Timestamp(1900, 12, 31)}
    if not isinstance(issuing_date_ps.iloc[0], pd.Timestamp):
        issuing_date_ps = pd.to_datetime(issuing_date_ps)
    data = issuing_date_ps.unstack()
    report_dead_line = pd.DataFrame(data.index, index=data.index)
    report_dead_line['dead_line'] = [i+lookup_dict[i.month] for i in report_dead_line['dt']]
    # check for non-ascending issuing date
    _days = (data - data.shift(-1)).apply(lambda x: x.dt.days)
    _mask_1 =  (_days > 0) & (_days < 1000)
    # check for issuing date later than dead line
    _mask_2 = (data.subtract(report_dead_line['dead_line'], axis=0)).apply(lambda x: x.dt.days) >= 30
    # check for wrong issuing date
    _mask_3 = (data.subtract(report_dead_line['dt'], axis=0)).apply(lambda x: x.dt.days) <= -1
    _mask = _mask_1 | _mask_2 | _mask_3
    data[_mask] = np.nan
    return data.stack()

def create_listing_delisting_filter(start_date, end_date, merged_mask=True,
                                    h5_path=h5_path_listing_delisting):
    
    start_date = str_date_parser(start_date)
    end_date = str_date_parser(end_date)
    full_day_range = pd.date_range(start=start_date, end=end_date, freq='1D')
    trading_dates = get_trading_date_range(start_date, end_date)

    # with pd.HDFStore(h5_path,mode='r') as hdf_store:
    #     delist_date = hdf_store.SecDate.delist_date
    #     list_date = hdf_store.SecDate.ipo_date
    delist_date = read_data([20090101,20990101],columns=['S_INFO_DELISTDATE'],alt=h5_path)
    list_date = read_data([20090101,20990101],columns=['S_INFO_LISTDATE'],alt=h5_path)
    delist_date.rename(columns={'S_INFO_DELISTDATE':'delist_date'},inplace=True)
    list_date.rename(columns={'S_INFO_LISTDATE': 'ipo_date'}, inplace=True)
    # process delisting date filter
    delist_date = delist_date.reset_index()
    delist_date.drop('dt',axis=1,inplace=True)
    delist_date['Filter'] = True
    delist_date_pd = delist_date.set_index(['delist_date', 'Ticker'])['Filter'].unstack().reindex(index=full_day_range)
    delist_date_pd = delist_date_pd.fillna(method='ffill')
    delist_date_pd = delist_date_pd.reindex(index=trading_dates)
    #delist_date_pd = delist_date_pd.fillna(False).astype('bool')
    delist_date_pd = delist_date_pd.replace([np.nan], False).astype('bool')
    # process listing date filter
    list_date = list_date.reset_index()
    list_date.drop('dt', axis=1, inplace=True)
    list_date['Filter'] = True
    list_date_pd = list_date.set_index(['ipo_date', 'Ticker'])['Filter'].unstack().reindex(index=full_day_range)
    list_date_pd = list_date_pd.fillna(method='bfill')
    list_date_pd = list_date_pd.reindex(index=trading_dates)
    #list_date_pd = list_date_pd.fillna(False).astype('bool')
    list_date_pd = list_date_pd.replace([np.nan], False).astype('bool')

    if merged_mask:
        return delist_date_pd | list_date_pd
    else:
        return delist_date_pd, list_date_pd
    

def backfill(start_date, end_date, factor_qtr_pd, issuing_date_ps=None, trading_date_list=None,
             issue_date_reformed=False, listing_delisting_filter=None):
    assert len(factor_qtr_pd.columns) == 1
    start_date = str_date_parser(start_date)
    end_date = str_date_parser(end_date)
    if issuing_date_ps is None:
        qtr_list = get_qtr_list(start_date,end_date,num_qtr=3)
        issuing_date_ps = read_data([qtr_list[0], qtr_list[-1]], ftype=FType.FDD, dsource=DSource.WIND,
                                        dfreq=DFreq.QUARTERLY, columns=['stm_issuingdate'])['stm_issuingdate']
        issuing_date_ps = issuing_date_checker(issuing_date_ps)
    else:
        if not issue_date_reformed:
            issuing_date_ps = issuing_date_checker(issuing_date_ps)
    data = factor_qtr_pd.copy()
    data['issuing_date'] = issuing_date_ps

    data = data.reset_index().sort_values(by='dt').dropna()
    data = data.drop_duplicates(subset=['issuing_date', 'Ticker'], keep='last')
    data = data.set_index(['issuing_date', 'Ticker'])
    data = data[factor_qtr_pd.columns[0]].unstack()
    _start_date = start_date - pd.Timedelta('365d')
    full_day_range = pd.date_range(start=_start_date, end=end_date, freq='1D')
    data = data.reindex(index=full_day_range).fillna(method='ffill',limit=210)
    if trading_date_list is None:
        data = data.reindex(index=get_trading_date_range(start_date, end_date))
    else:
        data = data.reindex(index=trading_date_list)
    if listing_delisting_filter is None:
        listing_delisting_filter = create_listing_delisting_filter(start_date, end_date)
    listing_delisting_filter = listing_delisting_filter.reindex(columns=data.columns).fillna(False).astype('bool')
    data[listing_delisting_filter] = np.nan


    res = pd.DataFrame(data.stack(), columns=factor_qtr_pd.columns)
    res.index.names = ['dt', 'Ticker']
    return res

def ticker_filter(stk_list):
    stk_list_filter = [i for i in stk_list if not i[0].isalpha()]
    return stk_list_filter

def get_backfill_prep(sdate,edate,announce_date=None):
    prep_data = {}
    qtr_list = get_qtr_list(sdate,edate,num_qtr=3)
    listing_delisting_filter = create_listing_delisting_filter(sdate,edate)
    if announce_date is not None:
        issuing_date_ps = announce_date
    else:
        alt_QUARTERLY = "/app/data/wdb_h5/WIND_TEST/FDD_CHINA_STOCK_QUARTERLY_WIND/FDD_CHINA_STOCK_QUARTERLY_WIND.h5"
        issuing_date_ps = read_data([qtr_list[0], qtr_list[-1]],  columns=['stm_issuingdate'],alt=alt_QUARTERLY)['stm_issuingdate']

        issuing_date_ps = issuing_date_checker(issuing_date_ps)
    trading_date_list = get_trading_date_range(sdate,edate)
    prep_data['qtr_list'], prep_data['listing_delisting_filter'] = qtr_list,listing_delisting_filter
    prep_data['issuing_date_ps'], prep_data['trading_date_list'] = issuing_date_ps,trading_date_list
    return prep_data


def backfill_master(fac_qtr,sdate,edate,prep_data=None):
    fac_daily_dict = {}
    fac_qtr_mi = fac_qtr.copy()
    if len(fac_qtr_mi.columns)>300:
        fac_qtr_mi = pd.DataFrame(fac_qtr_mi.stack(),columns=['anonymous'])
    fac_list = list(fac_qtr_mi.columns)
    if prep_data is None:
        logger.info('getting prep_data')
        qtr_list = get_qtr_list(sdate,edate,num_qtr=3)
        listing_delisting_filter = create_listing_delisting_filter(sdate,edate)
        issuing_date_ps = read_data([qtr_list[0], qtr_list[-1]], ftype=FType.FDD, dsource=DSource.WIND, dfreq=DFreq.QUARTERLY, columns=['stm_issuingdate'])['stm_issuingdate']
        issuing_date_ps = issuing_date_checker(issuing_date_ps)
        trading_date_list = get_trading_date_range(sdate,edate)
    elif prep_data is not None:
        qtr_list,listing_delisting_filter = prep_data['qtr_list'], prep_data['listing_delisting_filter']
        issuing_date_ps,trading_date_list = prep_data['issuing_date_ps'], prep_data['trading_date_list']
        
    for fac in fac_list:
        #print (fac)
        fac_daily_mi = backfill(sdate,edate,fac_qtr_mi[[fac]],issuing_date_ps,trading_date_list,True,listing_delisting_filter)
        fac_daily_dict[fac] = fac_daily_mi.unstack()[fac]
    if fac_list == ['anonymous']:
        return fac_daily_dict[fac]
    else:
        return fac_daily_dict


def get_current_date(new_date_time=18):
    """if current date is not pass new_date_time such as 18 (6pm)
       it will return previous trading day
    """
    current_time = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_date = int(current_time[:8])
    current_hour = int(current_time[9:11])
    logger.info('Current time: %s' % str(current_time))
    fdate_list_dt = read_data([20090101, 20300101], ftype=FType.CALENDAR).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
    nearest_date = min(fdate_list, key=lambda x: abs(x - current_date) if x <= current_date else 100)
    if current_hour < new_date_time and nearest_date == current_date:
        logger.info('Not till refresh time: %s' % (str(new_date_time) + ':00'))
        current_date = fdate_list[fdate_list.index(current_date) - 1]
        logger.info('Use previous trading date: %s' % str(current_date))
    elif nearest_date < current_date:
        current_date = nearest_date
    elif current_hour >= new_date_time and nearest_date == current_date:
        logger.info('Right on time: %s' % str(current_date))
    return current_date


def date_period_handler(sdate=None, edate=None,new_date_time=18):
    last_day = get_current_date(new_date_time)
    if sdate is None and edate is None:
        sdate = last_day
        edate = last_day
        logger.info('update for one day: %s' % str(sdate))
    if sdate is not None and edate is None:
        edate = last_day
    else:
        fdate_list_dt = read_data([20090101, 20300101], ftype=FType.CALENDAR).index.get_level_values(0)
        fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
        cdate_list = [i for i in fdate_list if i <= min(edate, last_day) and i >= sdate]
        sdate, edate = cdate_list[0], cdate_list[-1]
    return sdate, edate


def check_update_date(sdate=None, edate=None, use_len=None,new_date_time=18):
    # check_update_date(sdate=None,edate=None)
    use_len = 0 if use_len is None else use_len
    sdate, edate = date_period_handler(sdate, edate,new_date_time)
    fdate_list_dt = read_data([20090101, 20300101], ftype=FType.CALENDAR).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
    cdate_list = [i for i in fdate_list if i >= sdate and i <= edate]
    idx = max(0, fdate_list.index(cdate_list[0]) - use_len)
    sdate_prev = fdate_list[idx]
    logger.info('data used: %d - %d ' % (sdate_prev, edate))
    logger.info('factor data: %d - %d \ntotal count: %d' % (sdate_prev, edate, len(cdate_list)))
    return sdate_prev, edate, cdate_list

####################################################################################################################
        

############### multiprocess ############################

#"""

#"""
def multiprocess_wrapper(func,iter_list=None,logger=None,max_process=None,collect_output=False,**kwargs):
    """ func: list of function
        iter_list: list, dict(input inside)
    """
    max_process = os.cpu_count() if max_process==None else max_process
    iter_input = False
    if iter_list is not None:
        if isinstance(iter_list,dict):
            task_number = len(list(iter_list.keys()))
            iter_input = True
        if isinstance(iter_list,list):
            task_number = len(iter_list)            
    else:
        task_number = len(func)
    #task_number = len(iter_list) if iter_list is not None else len(func)
    tic1 = time.time()
    print_func_info = print if logger is None else logger.info
    print_func_warning = print if logger is None else logger.warning
    
    print_func_info('*'*20)
    start_info = 'start multiprocess -  max process number: %d - task number: %d'%(max_process,task_number)
    print_func_info(start_info)
    if collect_output:
        manager_dict = Manager().dict()
        if iter_list is None:
            if len(func) - len(set(func)) != 0:
                print_func_warning('not unique func input for collecting output')
                raise Exception
        else:
            if len(iter_list) - len(set(iter_list)) != 0:
                print_func_warning('not unique iter list input for collecting output')
                raise Exception
    else:
        manager_dict = None
    with Pool(max_process) as executor:
        print_func_info('*** task initialization ***')
        future_tasks = {}
        init_idx,ex_idx = 0,0
        if iter_list is not None:
            for itr in iter_list:
                init_idx = init_idx + 1
                try:
                    print_func_info('* init %d/%d : %s *'%(init_idx,task_number,itr))
                    if iter_input:
                        future_tasks[executor.submit(func,iter_list[itr],**kwargs)] = itr
                    else:
                        future_tasks[executor.submit(func,itr,**kwargs)] = itr
                except Exception as e:
                    print_func_warning('iter task initialization failed: %s - %s'%(itr,e))
        elif iter_list is None:
            for fc in func:
                init_idx = init_idx+1
                try:
                    print_func_info('* init %d/%d : %s'%(init_idx,task_number,fc))
                    future_tasks[executor.submit(fc,**kwargs)] = fc
                except Exception as e:
                    print_func_warning('func task init failed: %s - %s'%(fc,e))
        print_func_info('*** task execution ***')
        key_list = []
        for f in as_completed(future_tasks):
            key = future_tasks[f]
            key_list.append(key)
            ex_idx = ex_idx + 1
            try:
                done_ind = f.done()
            except Exception as e:
                print_func_warning('task execution failed - %s'%(e))
                f.cancel()
            if done_ind:
                try:
                    ts = f.result()
                    if manager_dict is not None:
                        manager_dict[key] = ts
                except Exception as e:
                    print_func_warning('%s'%(e))												
                    ts = None
                    done_ind = None
            else:
                ts = None
            if isinstance(ts,np.float) or isinstance(ts,np.int) :
                print_str = str((round((ts),2)))+'s'
            elif isinstance(ts,str):
                print_str = ts
            else:
                print_str = ''
            done_str = 'done' if done_ind == True else 'fail'
            itr_info = '* %d/%d - %s -%s  %s *'%(ex_idx,task_number,done_str,key,print_str)
            if done_ind:
                print_func_info(itr_info) 
            else:
                print_func_warning(itr_info)
            done_ind = None
                
    toc1 = time.time()
    time_str1 = str((round((toc1-tic1)/60,2)))+'minutes'
    end_info = '***** multiprocess end - %s ***'%(time_str1) + '\n' + '*'*20
    print_func_info(end_info)
    if collect_output:
        return dict(zip(key_list, manager_dict.values()))
    else:
        return 

def print_time(toc,tic):
    time_diff = toc-tic
    if time_diff>60:
        time_spent = (str((round((toc-tic)/60,2)))+' minutes')
    else:
        time_spent = (str((round(toc-tic,2)))+' s')
    return '(used %s)'%(time_spent)

############ dividend ####################
    
# update dividend use 
def calc_by_count(num_array,count_array,ufunc=np.sum):
    if isinstance(count_array,np.ndarray):
        count_num = int(count_array[-1])
    elif isinstance(count_array,int):
        count_num = count_array
    elif isinstance(count_array,np.float):
        count_num = np.int(count_array)
    if count_num not in [np.nan,None,0]:
        mask = np.isfinite(num_array)
        if np.count_nonzero(mask) >= count_num:
            return ufunc(num_array[mask][-count_num:])
        else:
            return np.nan
    else:
        return np.nan


def calc_dividend_yield(sdate, edate, dividend_data, alpha_universe, mkt_cap_ard):
    logger.info('calc dividend yield: %d - %d' % (sdate, edate))
    start_date = str_date_parser(sdate)
    end_date = str_date_parser(edate)
    # calculate dividend
    div_widow = 400
    div_cnt_window = 252
    maks_fill_limit = 600
    min_pct = 1/div_widow
    min_window = div_cnt_window + div_widow
    # sdate_prev = get_trading_day_offset(sdate, -1 * min_window)[0]
    # from Wind.mysql_tradingdays import get_prev_sdate
    sdate_prev = get_prev_sdate(sdate, min_window,sql_config)

    logger.info('calc dividend ex')
    div_dat_ex = easy_fill(dividend_data[['dividend_amount', 'EX_DT']], sdate_prev, edate, foward_date='EX_DT',
                           fill_method=None)
    dividend_count_ex = div_dat_ex.rolling(div_cnt_window).count()
    dividend_count_guess_ex = dividend_count_ex.rolling(div_cnt_window).mean().applymap(lambda x:np.round(x))
    dividend_payout_ex = calc_df_ts_roll(calc_by_count,div_widow,div_dat_ex,dividend_count_guess_ex,min_pct,verbose=True,handle_nan=False)
    
    print ('calc dividend pa')
    div_dat_pa = easy_fill(dividend_data[['dividend_amount','S_DIV_PRELANDATE']], sdate_prev, edate,foward_date='S_DIV_PRELANDATE',fill_method=None)
    dividend_count_pa = div_dat_pa.rolling(div_cnt_window).count()
    dividend_count_guess_pa = dividend_count_pa.rolling(div_cnt_window).mean().applymap(lambda x:np.round(x))
    dividend_payout_pa = calc_df_ts_roll(calc_by_count,div_widow,div_dat_pa,dividend_count_guess_pa,min_pct,verbose=True,handle_nan=False)
    
    ##########################
    # overlay pa on ex : pa first then with ex till next pa
    logger.info('overlay pa on ex')
    sdate_pa = dividend_data['S_DIV_PRELANDATE'].dropna().apply(dt_parser)
    edate_ex = dividend_data['EX_DT'].dropna().apply(dt_parser)

    logger.info('get fill mask')
    fill_mask_dividend_pa_ex = get_fill_mask(sdate_prev, edate, sdate_pa, edate_ex, maks_fill_limit)
    dividend_payout = dividend_payout_ex.copy()
    dividend_payout[fill_mask_dividend_pa_ex] = dividend_payout_pa
    
    dividendyield_raw = dividend_payout / mkt_cap_ard * 100
    dividendyield_raw = dividendyield_raw.reindex(index=alpha_universe.index,columns=alpha_universe.columns)
    raw_mask = alpha_universe & np.isnan(dividendyield_raw)
    raw_mask = align_df(raw_mask,raw_mask,fill_value=False)
    dividendyield_raw[raw_mask] = 0
    # dividendyield = NormWinsor(dividendyield_raw)
    # dividendyield_nis = factor_neutralize_mat(dividendyield_raw,style_data,neutral_list=['Size','Industry']) # use raw is better
    logger.info('calc dividend done')
    return dividendyield_raw.loc[start_date:end_date]
    
def align_df(df,df_template,fill_value=None):
    df_align = df.reindex(index=df_template.index,columns=df_template.columns)
    if fill_value is not None:
        df_align = df_align.fillna(value=fill_value)
    return df_align

def get_fill_mask(sdate,edate,start_date_df,end_date_df,limit=210):
    """  (sdate_prev,edate,start_date_df=announce_date,end_date_df=issuing_date_ps)
    # matrix of sdate and edate 
    # with start_date_df as announce_date
    # edate_date_df as stm_issuing date 
    # to get a mask for filtering before and end     
    """
    start_date = str_date_parser(sdate)
    end_date = str_date_parser(edate)
    _start_date = start_date - pd.Timedelta('365d')
    full_day_range = pd.date_range(start=_start_date, end=end_date, freq='1D')
    trading_dates = get_trading_date_range(start_date, end_date)


    start_date_df = start_date_df.reset_index().sort_values(by='dt').dropna()
    start_date_df.columns = ['dt','Ticker','start_date']
    start_date_df = start_date_df.drop_duplicates(subset=['start_date', 'Ticker'], keep='last')
    start_date_df = start_date_df.set_index(['start_date', 'Ticker'])
    start_date_df['dt'] = start_date_df['dt'].apply(lambda x: int(dt.datetime.strftime(x,'%Y%m%d')))
    start_date_df = start_date_df['dt'].unstack()
    start_date_df = start_date_df.reindex(index=full_day_range).fillna(method='ffill',limit=limit)

    end_date_df = end_date_df.reset_index().sort_values(by='dt').dropna()
    end_date_df.columns = ['dt','Ticker','end_date']
    end_date_df = end_date_df.drop_duplicates(subset=['end_date', 'Ticker'], keep='last')
    end_date_df = end_date_df.set_index(['end_date', 'Ticker'])
    end_date_df['dt'] = end_date_df['dt'].apply(lambda x: int(dt.datetime.strftime(x,'%Y%m%d')))
    end_date_df = end_date_df['dt'].unstack()
    end_date_df = end_date_df.reindex(index=full_day_range).fillna(method='ffill',limit=limit)

    stk_list = list(set(start_date_df.columns).union(set(end_date_df)))
    stk_list.sort()
    
    end_date_df = end_date_df.reindex(columns=stk_list,index=trading_dates)
    start_date_df = start_date_df.reindex(columns=stk_list,index=trading_dates)

    start_mask = np.isfinite(start_date_df)
    fill_mask = (start_date_df > end_date_df) & start_mask
    return fill_mask


##############################################

def calc_ps_ts_roll(func,roll_num,y_pd,x_pd=None,min_pct=0.5,handle_nan=True):
    """ remove nan already for unit calc func"""
    if x_pd is not None:
        x = x_pd.values
    y= y_pd.values
    stk_name = y_pd.name
    date_list = y_pd.index.tolist()
    date_num = len(y)
    min_size = int(roll_num*min_pct)
    collector_mat = np.ones(date_num)
    collector_mat[:] = np.nan
    iter_num = date_num - roll_num + 1
    for iter_start in range(iter_num):
        iter_end = iter_start + roll_num
        yt = y[iter_start:iter_end]
        if x_pd is None:
            mask = np.isfinite(yt)
        else:
            xt = x[iter_start:iter_end,:]
            mask = np.isfinite(yt + xt.sum(axis=1))
        if np.count_nonzero(mask) >= min_size:
            yt = yt.flatten()
            if handle_nan:
                yt = yt[mask]
                if x_pd is not None:
                    xt = xt[mask]
            if x_pd is not None:
                if xt.shape[1]==1:
                    xt = xt.flatten()
                collector_mat[iter_end-1] = func(yt,xt) 
            else:
                collector_mat[iter_end-1] = func(yt)
    res_stk = pd.DataFrame(collector_mat,columns=[stk_name],index=date_list)
    return res_stk

def calc_df_ts_roll(func,roll_num,y_df,x_df=None,min_pct=0.5,verbose=False,handle_nan=True):
    """ handle x_df: date*stock , date*variable, None"""
    if x_df is not None:
        if isinstance(x_df,pd.DataFrame) or isinstance(x_df,pd.Series):
            if x_df.shape == y_df.shape:
                x_type='stk'
            else:
                x_type='macro'
                x_df = pd.DataFrame(x_df)
    else:
        x_type='nan'
    result_list = []
    stk_list,date_list = list(y_df.columns),list(y_df.index)
    stk_num,date_num = len(stk_list), len(date_list)
    tic = time.time()
    for stk_name in stk_list:
        if verbose:
            idx = stk_list.index(stk_name)+1
            if idx%100==0:
                toc = time.time()
                logger.info('%d/%d - %fs' % (idx, stk_num, round((toc - tic), 2)))
        y_pd = y_df[stk_name]
        if x_type=='stk':
            x_pd = x_df[[stk_name]]
        elif x_type=='macro':
            x_pd = x_df
        elif x_type=='nan':
            x_pd = None
        res_stk = calc_ps_ts_roll(func,roll_num,y_pd,x_pd,min_pct,handle_nan)
        result_list.append(res_stk)
    result = pd.concat(result_list,axis=1)
    if verbose:
        logger.info('calc function: %s \nstk_num: %d \ndate_num: %d' % (str(func), stk_num, date_num))
    return result

