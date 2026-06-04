# -*- coding: utf-8 -*-


import datetime as dt
import datetime
import pandas as pd
import os
import numpy as np
from multifactor.IO import IO
from multifactor.IO.IO_enums import *
import time as time
import statsmodels.api as sm
from functools import reduce
#import config_reader
import pickle
import multifactor.utility.dt as tdt
import urllib
#import winreg
import re
#modify python 连接Oracle数据库
import cx_Oracle

# MIN RAW2MID~~~~~~~~~~~~~~~~~~~~~~~~~~

# MINUTE ~~~~~~~~~~~~~~~~~~~~~~~~~~
def save_pickle(save_dict, save_path):
    with open(save_path, 'wb') as input:
        pickle.dump(save_dict, input, protocol=pickle.HIGHEST_PROTOCOL)
    return


def read_pickle(save_path):
    with open(save_path, 'rb') as input:
        save_dict = pickle.load(input)
    return save_dict


# WIND ~~~~~~~~~~~~~~~~~~~~~~~~~~

def latest_issue_date(qtr):
    if type(qtr) == int:
        qtr = str(qtr)
    if type(qtr) == pd._libs.tslib.Timestamp:
        qtr = dt.datetime.strftime(qtr, '%Y%m%d')
    year, month = qtr[:4], qtr[4:]
    lookup_dict = {'0331': '0430', '0630': '0831', '0930': '1031', '1231': '0430'}
    # lookup_dict = {'0331':'0505','0630':'0905','0930':'1105','1231':'0505'}
    if month == '1231':
        lastest_int = int(str(int(year) + 1) + lookup_dict[month])
    else:
        lastest_int = int(year + lookup_dict[month])
    last_day = dt.datetime.strptime(str(lastest_int), '%Y%m%d')
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
        data_dict[fac] = h5_data[fac].unstack()
    return data_dict


def DF2MultiIndex(df_dict):
    """pass in dict of df, get df with multi_index"""
    df_mi = pd.DataFrame()
    for df in df_dict:
        df_dict[df] = df_dict[df].reset_index()
        if df_dict[df].columns[0] == 'index':
            df_dict[df] = df_dict[df].rename(index=str, columns={"index": "dt"})
        df_dict[df]['FactorName'] = df
        df_dict[df] = df_dict[df].set_index(['dt', 'FactorName'])
        df_mi = df_mi.append(df_dict[df])
    return df_mi


def get_current_date(new_date_time=18):
    """if current date is not pass new_date_time such as 18 (6pm)
       it will return previous trading day
    """
    current_time = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_date = int(current_time[:8])
    current_hour = int(current_time[9:11])
    print('Current time: ' + str(current_time))
    fdate_list_dt = IO.read_data([19980101, 20200101], ftype=FType.CALENDAR).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
    nearest_date = min(fdate_list, key=lambda x: abs(x - current_date) if x <= current_date else 100)
    if current_hour < new_date_time and nearest_date == current_date:
        print('Not till refresh time ' + str(new_date_time) + ':00')
        current_date = fdate_list[fdate_list.index(current_date) - 1]
        print('Use previous trading date: ' + str(current_date))
    elif nearest_date < current_date:
        current_date = nearest_date
    elif current_hour >= new_date_time and nearest_date == current_date:
        print('Right on time: ' + str(current_date))
    return current_date


def date_period_handler(sdate=None, edate=None):
    last_day = get_current_date()
    if sdate is None and edate is None:
        sdate = last_day
        edate = last_day
        print('update for one day: ' + str(sdate))
    if sdate is not None and edate is None:
        edate = last_day
    else:
        fdate_list_dt = IO.read_data([19980101, 20200101], ftype=FType.CALENDAR).index.get_level_values(0)
        fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
        cdate_list = [i for i in fdate_list if i <= min(edate, last_day) and i >= sdate]
        sdate, edate = cdate_list[0], cdate_list[-1]
    return sdate, edate


def check_update_date(sdate=None, edate=None, use_len=None):
    # check_update_date(sdate=None,edate=None)
    use_len = 0 if use_len is None else use_len
    sdate, edate = date_period_handler(sdate, edate)
    fdate_list_dt = IO.read_data([19980101, 20200101], ftype=FType.CALENDAR).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
    cdate_list = [i for i in fdate_list if i >= sdate and i <= edate]
    idx = max(0, fdate_list.index(cdate_list[0]) - use_len)
    sdate_prev = fdate_list[idx]
    print('-' * 20, '\ndata used: %d - %d ' % (sdate_prev, edate))
    print('factor data: %d - %d \ntotal count: %d' % (sdate_prev, edate, len(cdate_list)))
    print('-' * 20)
    return sdate_prev, edate, cdate_list


def align_data(data_dict):
    i = 0
    # dat_type = [type(data_dict[factor])for factor in data_dict]
    # get stock list, date list
    for factor in data_dict:
        if type(data_dict[factor]) == pd.DataFrame:
            if i == 0:
                stock_list = data_dict[factor].columns.tolist()
                date_list = data_dict[factor].index.tolist()
                i = i + 1
            else:
                stock_list = np.intersect1d(stock_list, data_dict[factor].columns.tolist())
                date_list = np.intersect1d(date_list, data_dict[factor].index.tolist())
        elif type(data_dict[factor]) == pd.Series:
            if i == 0:
                date_list = data_dict[factor].index.tolist()
            else:
                date_list = np.intersect1d(date_list, data_dict[factor].index.tolist())

    # align dataframe and series
    data_dict_aligned = {}
    for factor in data_dict:
        # print (factor)
        if type(data_dict[factor]) == pd.DataFrame:
            data_dict_aligned[factor] = data_dict[factor][stock_list].loc[date_list]
        elif type(data_dict[factor]) == pd.Series:
            data_dict_aligned[factor] = data_dict[factor].loc[date_list]
    return data_dict_aligned


def df_formatter(dataframe, factor_name):
    data_MI = pd.DataFrame(dataframe.stack(), columns=[factor_name])
    data_MI.index.names = ['dt', 'Ticker']
    return data_MI


#########################################################################################
"""因子数据处理部分"""


def FactorTypeCheck(factor_dict):
    """ 自动判别因子是否为1，0,-1 的标签矩阵"""
    max_min = [factor_dict.max().max(), factor_dict.min().min()]
    factor_type = 'Categorical' if max_min in [[0, -1], [0, 1], [-1, 1]] else 'Numerical'
    return factor_type


def Standard_Process(factor_dict, nan_ind, stock_industry, FillNaN=False):
    """ nan_ind:  可以根据用户输入决定筛选条件 - 比如VOLUME>0
        True： 1. 去除没有收益的日子
        False: 1. 去除没有收益的日子  2. 标准化
    """
    factor_type = FactorTypeCheck(factor_dict)
    if factor_type == 'Categorical':  # 不进行任何 因子清洗，填充
        print('           Factor Type: Categorical --> No Standardization and FillingNA')
    elif factor_type == 'Numerical':
        factor_dict[~nan_ind] = np.nan
        factor_dict[~np.isfinite(factor_dict)] = np.nan  # 将inf,-inf,nan 取代为nan
        # print ('           BoxSkewPlot Processing')
        factor_dict = BoxSkewPlot(factor_dict)  # 极值处理
        # print ('           Normalizing')
        if FillNaN == True:
            # print ('           Filling NaN with Industry Median...')
            factor_dict = Factor_Fillna(factor_dict, stock_industry, nan_ind)
        else:
            print('           NaN not Filled')
        factor_dict = factor_dict.subtract(factor_dict.mean(axis=1), axis=0).divide(factor_dict.std(axis=1, ddof=0),
                                                                                    axis=0)  # handle nan
    return factor_dict


def DataNormalize(factor_dict):
    factor_dict = factor_dict.subtract(factor_dict.mean(axis=1), axis=0).divide(factor_dict.std(axis=1, ddof=0), axis=0)
    return factor_dict


def box_skew_algo(x):
    y = np.array(x)
    x = y[~np.isnan(y)]
    if len(np.unique(x)) < 10:
        return y
    x = np.sort(x)
    md = np.median(x)
    q3 = np.percentile(x, 75)
    q1 = np.percentile(x, 25)
    iqr = q3 - q1
    rx = np.flip(x, axis=0)
    x, rx = zip(*[(i, j) for i, j in zip(x, rx) if i != j])
    x = np.split(np.array(x), 2)[1]
    rx = np.split(np.array(rx), 2)[1]
    if len(x) < 5:
        return y
    mc = np.median((x + rx - 2.0 * md) / (x - rx))
    a, b = (3.5, 4) if mc >= 0 else (4, 3.5)
    L = q1 - 1.5 * np.exp(-a * mc) * iqr
    U = q3 + 1.5 * np.exp(b * mc) * iqr
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


def Factor_Fillna(factor_dict, stock_industry, nan_ind):
    """ 缺失值处理：
    得到新的因子暴露度序列后，将因子暴露度缺失的地方设为行业中位数。
    # 因子暴露度缺失定义为无法获取此因子 而非该股票不可交易  - 用处理过的因子填充
    # nan_ind 为股票停牌信息  1 为真停牌 或者没上市/ 则不填充

    """
    fill_ind = np.isnan(factor_dict)[~nan_ind]  # 所有NAN * 非停牌的NAN = 缺失数据
    industry_median = pd.DataFrame(index=factor_dict.index, columns=[i for i in range(31)])
    for date in stock_industry.index:
        industry_list = stock_industry.loc[date]
        industry_median.loc[date] = [i[0] for i in
                                     pd.DataFrame(factor_dict.loc[date]).groupby(industry_list).median().values]
    Fill_median = factor_dict.copy()
    for i in [i for i in range(31)]:  # loop industry
        stock_in_industry = industry_list[industry_list == i].index.tolist()
        Fill_median[stock_in_industry] = pd.DataFrame([industry_median[i].tolist()] * len(stock_in_industry)).T
    factor_dict[fill_ind == 1] = Fill_median[fill_ind == 1]
    return factor_dict


def Factor_Fillna_TS(factor_dict, holding_peiord):
    """如果数据不齐，则往回看多少天区间 取均值
       用于稀疏的财报数据矩阵
    """
    factor_fill = factor_dict.rolling(window=holding_peiord, min_periods=1).mean()
    return factor_fill


def np_regression_res(x, y):
    res = np.array([np.nan] * len(x))
    mask = np.isfinite(x) & np.isfinite(y.sum(axis=1))
    if len(mask) == 0:
        return res
    ols1 = sm.OLS(x[mask], y[mask]).fit()
    res[mask] = ols1.resid
    return res


def factor_neutralize_mat(factor_dict, neutral_dict, neutral_list, Normalize=True):
    """
    Generic Version of Neutralizer - but still assume everything aligned
    data_dict: dictionary of dataframe
    Normalize: Choose to normalize residual cross sectionally

    """
    print('-' * 5 + '   Get Factor Neutralized   ' + '-' * 5)
    tic = time.time()
    date_num, stock_num = factor_dict.shape
    factor_num = len(neutral_list)
    y_mat = np.ones([factor_num + 1, date_num, stock_num])  # including intercept
    factor_mat = factor_dict.values
    for i in range(factor_num):
        y_mat[i, :, :] = neutral_dict[neutral_list[i]].values

    res = np.empty([date_num, stock_num])
    res[:] = np.nan
    for date_idx in range(date_num):
        try:
            res[date_idx, :] = np_regression_res(factor_mat[date_idx, :], y_mat[:, date_idx, :].T)
        except:
            continue
    factor_residual = pd.DataFrame(res, columns=factor_dict.columns, index=factor_dict.index)
    factor_residual = DataNormalize(factor_residual) if Normalize == True else factor_residual
    toc = time.time()
    print(str((round((toc - tic), 2))) + 's ellapsed')
    print('-' * 20)
    return factor_residual


def weight_decay(half_life, total_len):  # 其中n是半衰期，m是序列长度
    return [0.5 ** ((total_len - i) / half_life) for i in range(total_len)]


"""Value"""


def date_checker(data_MI, cdate_list):
    """for MultiIndex"""
    date_check = data_MI.index.get_level_values(0).unique().tolist()
    date_check = [date_check] if type(date_check) != list else date_check
    no_date = list(set(cdate_list) - set(date_check))
    no_date.sort()
    if len(no_date) > 0:
        raise Exception('No data for ', str(no_date))
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





def save_dt_list(cdate_list=None):
    save_name = 'D:\\Quant\\backtest\\local_data\\wind_data\\dt_list1.csv'
    cdate_list = [get_current_date(new_date_time=17)]
    fdate_list_dt = IO.read_data([20090101, 20200101], ftype=FType.CALENDAR).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
    dt_list = fdate_list[:fdate_list.index(cdate_list[-1]) + 1]
    pd.DataFrame(fdate_list).to_csv(save_name)
    return


def int2date(date_int, date_format='%Y%m%d'):
    if np.isfinite(date_int):
        date_time = dt.datetime.strptime(str(int(date_int)), '%Y%m%d')
    else:
        date_time = date_int
    return date_time



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# backfill


def get_qtr_list(sdate,edate,num_qtr=None):
    if isinstance(sdate,pd.Timestamp):
        sdate = int(dt.datetime.strftime(sdate,'%Y%m%d'))
        edate = int(dt.datetime.strftime(edate,'%Y%m%d'))
    if not isinstance(sdate,int):
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
            print ('input error: num_qtr not integer')
            raise Exception
    return qtr_list

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
                                    h5_path='Z:\\warehouse\\prod\\ETC\\CHINA_STOCK\\WIND\\STOCK_LISTING_DELISTING_DATE.h5'):
    start_date = IO.str_date_parser(start_date)
    end_date = IO.str_date_parser(end_date)
    full_day_range = pd.date_range(start=start_date, end=end_date, freq='1D')
    trading_dates = tdt.get_trading_date_range(start_date, end_date)
    with pd.HDFStore(h5_path) as hdf_store:
        delist_date = hdf_store.SecDate.delist_date
        list_date = hdf_store.SecDate.ipo_date
    # process delisting date filter
    delist_date = delist_date.reset_index()
    delist_date['Filter'] = True
    delist_date_pd = delist_date.set_index(['delist_date', 'Ticker'])['Filter'].unstack().reindex(index=full_day_range)
    delist_date_pd = delist_date_pd.fillna(method='ffill')
    delist_date_pd = delist_date_pd.reindex(index=trading_dates)
    delist_date_pd = delist_date_pd.fillna(False).astype('bool')
    # process listing date filter
    list_date = list_date.reset_index()
    list_date['Filter'] = True
    list_date_pd = list_date.set_index(['ipo_date', 'Ticker'])['Filter'].unstack().reindex(index=full_day_range)
    list_date_pd = list_date_pd.fillna(method='bfill')
    list_date_pd = list_date_pd.reindex(index=trading_dates)
    list_date_pd = list_date_pd.fillna(False).astype('bool')
    if merged_mask:
        return delist_date_pd | list_date_pd
    else:
        return delist_date_pd, list_date_pd


def backfill(start_date, end_date, factor_qtr_pd, issuing_date_ps=None, trading_date_list=None,
             issue_date_reformed=False, listing_delisting_filter=None):
    assert len(factor_qtr_pd.columns) == 1
    start_date = IO.str_date_parser(start_date)
    end_date = IO.str_date_parser(end_date)
    qtr_list = get_qtr_list(start_date,end_date,num_qtr=3)
    prev_start = IO.str_date_parser(qtr_list[0])
    if issuing_date_ps is None:
        issuing_date_ps = IO.read_data([prev_start, qtr_list[-1]], ftype=FType.FDD, dsource=DSource.WIND,
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
    full_day_range = pd.date_range(start=prev_start, end=end_date, freq='1D')
    data = data.reindex(index=full_day_range).fillna(method='ffill')
    if trading_date_list is None:
        data = data.reindex(index=tdt.get_trading_date_range(start_date, end_date))
    else:
        data = data.reindex(index=trading_date_list)
    if listing_delisting_filter is None:
        listing_delisting_filter = create_listing_delisting_filter(start_date, end_date)
    listing_delisting_filter = listing_delisting_filter.reindex(columns=data.columns).fillna(False).astype('bool')
    data[listing_delisting_filter] = np.nan
    res = pd.DataFrame(data.stack(), columns=factor_qtr_pd.columns)
    res.index.names = ['dt', 'Ticker']
    return res


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# update_wind_htsc

def getQPUserInfo():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r"SOFTWARE\Wow6432Node\QuantPF")
        userid,type = winreg.QueryValueEx(key,"userid")
        session,type = winreg.QueryValueEx(key,"session")
        ipaddr,type = winreg.QueryValueEx(key,"ipaddr")
    except:
        try:
            key,type = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r"SOFTWARE\QuantPF")
            userid,type = winreg.QueryValueEx(key,"userid")
            session,type = winreg.QueryValueEx(key,"session")
            ipaddr,type = winreg.QueryValueEx(key,"ipaddr")
        except:
            userid = '000000'
            session = 'Invalid session'
            ipaddr = 'Invalid IP'
    return userid,session,ipaddr

# def queryUserTableData(sqlStr='', rownum=100000):
#     if sqlStr == '':
#         print('[queryUserTableData函数]参数queryUserTableData为空，请重新输入！')
#         return
#     dbPath = 'http://eip.htsc.com.cn/QuantiveService/DataSetService/'
#     urlVersion = '0161'
#     url = dbPath + 'queryUserTableDataset'
#     userid,session,ipaddr = getQPUserInfo() #获取用户登录信息
#     #传递参数获取数据
#     parms = urllib.parse.urlencode({'apiparam':urlVersion,'userid':userid,'session':session,
#                                     'ipaddr':ipaddr,'rownum':str(rownum),'strsql':sqlStr})
#     parms = parms.encode('utf-8')
#     data = urllib.request.urlopen(url,parms)
#     data = data.read().decode('utf-8')
#     data = ('[['+data[1:-1] +']]').replace(';','],[')
#     return data

conn = None
def queryUserTableData(sql_use):
    global conn
    if conn is None:
        conn = cx_Oracle.connect("center_read/Htsc_Htzx@168.9.2.43/qdb04")
    cur = conn.cursor()
    cur.execute(sql_use)
    index = cur.description
    result = []

    row = []
    for i in range(len(index)):
        row.append(index[i][0])
    result.append(row)

    for res in cur.fetchall():
        row = []
        for i in range(len(index)):
            row.append(res[i])
        result.append(row)
    cur.close()
    # conn.close()
    return str(result)

def sql_parser(data):
    NaN = np.nan
    try:
        _data = eval(data)
    except SyntaxError as _exp:
        print(_exp)
        if 'triple-quoted string' in _exp.msg:
            data = re.sub(r"'{3,}", '', data)
            data = re.sub(r'"{3,}', '', data)
            _data = eval(data)
        else:
            raise SyntaxError
    try:
        res = pd.DataFrame(_data[1:], columns=_data[0])
    except OverflowError:
        res = pd.DataFrame(_data, columns=_data[0])
        res = res.drop([0], axis=0).reset_index(drop=True)
    return res

def data_reformat(dat,dat_fig):   
    #dat = dat.sort_values([dat_fig['dt']])
    dat[dat_fig['dt']] = dat[dat_fig['dt']].apply(lambda x: dt.datetime.strptime(str(x),'%Y%m%d'))
    if 'Ticker' in dat_fig:
        dat[dat_fig['Ticker']] = dat[dat_fig['Ticker']].astype('str')
        dat = dat.sort_values([dat_fig['dt'],dat_fig['Ticker']])
        dat = dat.set_index([dat_fig['dt'],dat_fig['Ticker']])
        dat.index.names = ['dt','Ticker']
    else:
        dat = dat.sort_values(dat_fig['dt'])
        dat = dat.set_index([dat_fig['dt'], 'OBJECT_ID'])
        dat.index.names = ['dt', 'OBJECT_ID']        
    format_list = dat.dtypes
    num_list = [i != np.dtype('object') for i in format_list]
    col_list = dat.columns.values
    for i in range(len(num_list)):
        if num_list[i]:
            dat[col_list[i]] = dat[col_list[i]].astype('float64')
    format_list = [type(i) for i in dat.iloc[0,:]]
    return dat
