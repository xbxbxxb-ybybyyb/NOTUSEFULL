import numpy as np
import pandas as pd
import os
import sys
from sklearn.externals.joblib import Parallel, delayed
from clean_factor import *
from config_path import *
import datetime
from xquant.factordata import FactorData
fa = FactorData()
from xquant.xqutils.helper import link
lm = link.LinkMessage()

num_threads = 20
stock_list = pd.read_pickle(depart_sample_path+'stock_list.pkl')
factor_info_path_tmp = '/data/group/800469/AlphaDataCenter/Department/DepartSample/factor_info_nnnn.pkl'
depart_factor_pool_path = '/data/group/800002/alpha_factor/lib/x_factor_lib/'
def check_single_sample(path, date, factor_list, silent=True):
    df = pd.read_pickle(path + date + '.pkl')[factor_list]
    corr = df.corr()
    dup = corr[corr == 1].sum(axis=1)
    duplist = dup[dup > 1].index.tolist()
    zero_sample = df.abs().sum()
    zero_list = zero_sample[zero_sample == 0].index.tolist()
    if not silent:
        if len(duplist) > 0:
            print(date, duplist, ' duplicated')
            lm.sendMessage(date + " duplicated: {0}".format(str(duplist)))
        if len(zero_list) > 0:
            print(date, zero_list, 'not update success')
            lm.sendMessage(date + " not update success: {0}".format(str(zero_list)))
    return duplist, zero_list

def get_single_factor(f, factor_path, start_date, end_date):
    try:
        df = pd.read_pickle(factor_path + f + '.pkl').loc[start_date:end_date].reindex(columns=stock_list).astype(np.float64)
        df[np.isinf(df)] = np.nan
    except Exception:
        df = pd.read_pickle(basic_daily_path+'is_valid.pkl').loc[start_date:end_date].reindex(columns=stock_list)
        df = pd.DataFrame(index = df.index,columns = df.columns,data=np.nan)
    df.index = pd.to_datetime(df.index)
    return df.stack(dropna=False)

def get_factors(factor_path_dict, start_date, end_date):
    from sklearn.externals.joblib import Parallel, delayed
    final_factor = Parallel(n_jobs=num_threads)(
        delayed(get_single_factor)(f, factor_path, start_date, end_date) for f, factor_path in factor_path_dict.items())
    final_factor = dict(zip(factor_path_dict.keys(), final_factor))
    final_factor = pd.DataFrame(final_factor)
    return final_factor


def get_stock_date(start_date, end_date):
    is_valid = pd.read_pickle(basic_daily_path+'is_valid.pkl').loc[start_date:end_date]
    stock_list = is_valid.columns.tolist()
    date_list = [d.strftime('%Y%m%d') for d in is_valid.index]
    return stock_list, date_list

def get_single_date(date, factor_list, stock_list):
    if date >= '20200801':
        df = fa.get_factor_value('x_day_lib', stock=stock_list, mddate=[date], factor_names=factor_list).reset_index()
    else:
        df = pd.read_parquet(parquet_path + 'mddate=' + date + '/')[['stock'] + factor_list]

    df['date'] = pd.to_datetime(date)
    return df[df['stock'].isin(stock_list)]


def get_parquet_factors(stock_list, date_list, factor_list):
    res = Parallel(n_jobs=num_threads)(delayed(get_single_date)(date, factor_list, stock_list) for date in date_list)
    return pd.concat(res)


def get_factors_xquant(factor_list, start_date, end_date):
    stock_list, date_list = get_stock_date(start_date, end_date)
    ori_data = get_parquet_factors(stock_list, date_list, factor_list)
    return ori_data.set_index(['date', 'stock'])


# 处理市值和行业
def get_mkt_indus(path, start_date, end_date, shift_lag=1):
    mkt = pd.read_pickle(path + 'mkt_cap_ard.pkl').shift(shift_lag).loc[start_date:end_date]
    log_mkt = np.log(mkt)
    neu_basic = log_mkt.stack(dropna=False).to_frame(name='log_mkt')
    # 处理行业
    industry_code_all = pd.read_pickle(path + 'industry_code_all.pkl').shift(shift_lag).loc[start_date:end_date]
    industry_dummy = pd.get_dummies(industry_code_all.stack(dropna=False))
    neu_basic[industry_dummy.columns] = industry_dummy
    return neu_basic


def get_neu_sample(basic_path, factor_path_dict, start_date, end_date, shift_lag):
    tool_name = ['is_valid_raw', 'is_valid', 'industry_code_all']
  
    if isinstance(factor_path_dict, dict):
        data = get_factors(factor_path_dict, start_date, end_date)
    elif isinstance(factor_path_dict, list):
        data = get_factors_xquant(factor_path_dict, start_date, end_date)
    factor_list = data.columns.tolist()
    for t in tool_name:
        tmp = pd.read_pickle(basic_path + t + '.pkl').shift(shift_lag).loc[start_date:end_date]
        data[t] = tmp.stack(dropna=False)
    neu_basic = get_mkt_indus(basic_path, start_date, end_date, shift_lag)

    data[neu_basic.columns] = neu_basic
    data = data[data['is_valid'] == 1]
    data.index = data.index.remove_unused_levels()

    data = data.reset_index().rename(columns={'level_0': 'date', 'level_1': 'stock'})
    if not 'date' in data.columns:
        data = data.rename(columns={'mddate': 'date'})
    data[factor_list] = data.groupby(by=['date', 'industry_code_all'])[factor_list].transform(
        lambda x: x.fillna(x.mean()))
    data = data.set_index(['date', 'stock'])
    data = neutralize(data[factor_list], data[neu_basic.columns], data_norm=factor_list, how_norm=['log_mkt'])
    data = apply_parallel(data.groupby(level=0), standard_winsor)
    return data.fillna(0)


def save_data(df_update,path):
    if os.path.exists(path):
        store_data = pd.read_pickle(path)
    else:
        store_data = df_update
    if isinstance(df_update,dict):
        for k,v in store_data.items():
            v=v.append(df_update[k])
            v = v.loc[~v.index.duplicated(keep='last')].sort_index()
            store_data[k] = v.astype(np.float64)
    else:
        store_data = store_data.append(df_update).astype(np.float64)
        store_data = store_data.loc[~store_data.index.duplicated(keep='last')].sort_index()
    pd.to_pickle(store_data,path)
    return store_data
def get_trade_price(basic_daily_path, basic_minute_path, start_date='', end_date='',
                    price_type='minute', transaction_price='vwap', transaction_time='0930', transaction_period=120):
    adjfactor = pd.read_pickle(basic_daily_path + 'close.pkl').loc['20140101':]
    trade_price = pd.DataFrame(index=adjfactor.index, columns=adjfactor.columns)
    if price_type == 'minute':
        assert len(transaction_time) == 4
        assert transaction_time[:2] in ['09', '10', '11', '13', '14']
        assert int(transaction_time[2:]) >= 0 and int(transaction_time[2:]) < 60
        assert int(transaction_time) >= 930 and int(transaction_time) < 1130 or int(transaction_time) >= 1300 and int(
            transaction_time) < 1500
        assert transaction_period > 0 and isinstance(transaction_period, int) if transaction_price == 'vwap' else True
        os.mkdir(minute_trade_price_path) if not os.path.exists(minute_trade_price_path) else None
        time_saver = transaction_price + '_' + transaction_time + '_' + str(transaction_period)
        if not os.path.exists(minute_trade_price_path + time_saver + '.pkl'):
            add_trade_price_dates = adjfactor.index
        else:
            trade_price_0 = pd.read_pickle(minute_trade_price_path + time_saver + '.pkl').dropna(how='all', axis=0)
            add_trade_price_dates = sorted(list(set(trade_price.index) - set(trade_price_0.index)))
        price = pd.DataFrame(index=add_trade_price_dates, columns=adjfactor.columns, data=np.nan)
        for date in [d.strftime('%Y%m%d') for d in add_trade_price_dates]:
            if transaction_price in ['open', 'close']:
                price.loc[date] = \
                pd.read_pickle(basic_minute_path + transaction_price.capitalize() + '/' + date + '.pkl').loc[
                    pd.Timestamp(date + transaction_time + '00')]
            else:
                minute_vol = pd.read_pickle(basic_minute_path + 'Volume/' + date + '.pkl').loc[
                             pd.Timestamp(date + transaction_time + '00'):].iloc[:transaction_period].sum()
                minute_amt = pd.read_pickle(basic_minute_path + 'Amount/' + date + '.pkl').loc[
                             pd.Timestamp(date + transaction_time + '00'):].iloc[:transaction_period].sum()
                price.loc[date] = minute_amt / minute_vol
            price[np.isinf(price)] = np.nan
     
        price = save_data(price,minute_trade_price_path + time_saver + '.pkl')
        trade_price = price.loc[trade_price.index]
    else:
        trade_price = pd.read_pickle(basic_daily_path + price_type + '.pkl').loc[trade_price.index]
    return trade_price.loc[start_date:end_date]

# 高频价格与is_valid生成
def get_valid(basic_daily_path, trade_price):
    adjfactor = pd.read_pickle(basic_daily_path + 'adjfactor.pkl').loc[trade_price.index]
    pre_close = pd.read_pickle(basic_daily_path + 'pre_close.pkl').loc[trade_price.index]
    maxupordown = ((trade_price - pre_close) / pre_close).abs().values >= 0.098
    is_valid_ori = pd.read_pickle(basic_daily_path + 'isvalid_and_not_open_updown_limit.pkl').loc[
        trade_price.index].astype(bool).values
    is_valid = pd.DataFrame(maxupordown & is_valid_ori, index=trade_price.index, columns=trade_price.columns)
    return is_valid


def get_trade_date(start_date, window):
    is_valid = pd.read_pickle(basic_daily_path + 'is_valid.pkl')
    if type(window) == type(start_date):
        return is_valid.loc[start_date:window].index
    elif window > 0:
        return is_valid.loc[start_date:].iloc[:window].index
    else:
        return is_valid.loc[:start_date].iloc[window:].index


# 将样本收益率标签转化为分组标签
def get_label_bin(data, return_type):
    bin_label = 'bin_' + return_type
    data[bin_label] = 0
    data = data.sort_values(by=return_type, ascending=False)
    n_stock_select = np.multiply([0.3, 0.3], data.shape[0])
    n_stock_select = np.around(n_stock_select).astype(int)
    for i in range(3):
        pos_step = int(n_stock_select[1] / 3.)
        data.iloc[int(i * pos_step):int((i + 1) * pos_step), -1] = 3 - i
    for i in range(3):
        neg_step = int(n_stock_select[0] / 3.)
        data.iloc[(data.shape[0] - int((i + 1) * pos_step)):(data.shape[0] - int(i * pos_step)), -1] = -1 * (3 - i)

    data = data[data[bin_label].abs() >= 0]
    return data

def get_rank_norm(df):
    from scipy.stats import norm
    df = df.rank(pct=True,axis=1)
    df[pd.DataFrame(index=df.index,columns=df.columns,data=(df.values==1))] = 1 -1/3676
    df[pd.DataFrame(index=df.index,columns=df.columns,data=(df.values==0))] = 1/3676
    df_norm = pd.DataFrame(norm.ppf(df.values),index=df.index,columns=df.columns)
    return df_norm
def get_future_return_team(basic_daily_path, trade_price, price_type='1300_1459', lag_list=[1, 3, 5], shift_lag=1,
                      winsard_flag=True, norm_flag=True):
    industry_code_all = pd.read_pickle(basic_daily_path + 'industry_code_all.pkl').shift(shift_lag).loc[
        trade_price.index]
    label_start_date = trade_price.index[0].strftime('%Y%m%d')
    label_end_date = trade_price.index[-1].strftime('%Y%m%d')
    is_valid = pd.read_pickle(basic_daily_path + 'is_valid.pkl').shift(shift_lag).loc[trade_price.index]
    adjfactor = pd.read_pickle(basic_daily_path + 'adjfactor.pkl').loc[trade_price.index]
    future_return_df = industry_code_all.stack(dropna=False).to_frame(name='industry_code_all')
    future_return_df['is_valid'] = is_valid.stack(dropna=False)
    price_adj = trade_price * adjfactor
    ori_label_list = []
    for lag in lag_list:
        re = price_adj.pct_change(lag).shift(-lag - (1 - shift_lag))
        label = price_type + '_NoExtremum_re_' + str(lag) + 'd'
        ori_label_list.append(label)
        future_return_df[label] = re.stack(dropna=False)

    future_return_df = future_return_df.reset_index().rename(columns={'level_0': 'date', 'level_1': 'stock'})
    all_label_list = ori_label_list.copy()

    future_return_df = future_return_df.set_index(['date', 'stock'])
    future_return_df = future_return_df[future_return_df['is_valid'] == 1]
    if winsard_flag == True:
        future_return_df[all_label_list] = apply_parallel(future_return_df[all_label_list].groupby(level=0), winsorize)
    if norm_flag == True:
        future_return_df[all_label_list] = apply_parallel(future_return_df[all_label_list].groupby(level=0),
                                                          standardlize)
    return future_return_df[all_label_list].fillna(0)
def get_future_return(basic_daily_path, trade_price, price_type='1300_1459', lag_list=[1, 3, 5], shift_lag=1,
                      winsard_flag=True, norm_flag=True,sharp_flag=True,
                        roll=True,fill_value=np.nan,fake_team=True):
    industry_code_all = pd.read_pickle(basic_daily_path + 'industry_code_all.pkl').shift(shift_lag).loc[
        trade_price.index]
    is_valid = pd.read_pickle(basic_daily_path + 'is_valid.pkl').shift(shift_lag).loc[trade_price.index]
    adjfactor = pd.read_pickle(basic_daily_path + 'adjfactor.pkl').loc[trade_price.index]
    future_return_df = industry_code_all.stack(dropna=False).to_frame(name='industry_code_all')
    future_return_df['is_valid'] = is_valid.stack(dropna=False)
    price_adj = trade_price * adjfactor
    ret_1d = price_adj.shift(-1- (1 - shift_lag))/price_adj.shift(-(1-shift_lag))-1
    date_list = [i.strftime('%Y%m%d') for i in price_adj.index]
    ori_label_list = []
    for lag in lag_list:
        re = price_adj.shift(-lag- (1 - shift_lag))/price_adj.shift(-(1-shift_lag))-1
        label = price_type + '_re_' + str(lag) + 'd'
        norm_label = price_type + '_norm_re_' + str(lag) + 'd'
        ori_label_list.append(label)
        norm_re = get_rank_norm(re)
        future_return_df[label] = re.stack(dropna=False)
        future_return_df[norm_label] = norm_re.stack(dropna=False)
        if sharp_flag:
            sharp_re = ret_1d.rolling(lag,2).mean()/ret_1d.rolling(lag,2).std()
            future_return_df[price_type+'_sharp_re_' + str(lag) + 'd'] = sharp_re.stack(dropna=False)
    
    if roll:
        trade_vwap_adj = get_trade_price(basic_daily_path, minute_data_path, date_list[0], date_list[-1],
                              price_type = 'vwap')*adjfactor
        re = trade_vwap_adj.rolling(window=5,min_periods=1).mean().shift(shift_lag-6)/price_adj.shift(shift_lag-1)-1
        label = price_type + '_roll5d'
        ori_label_list.append(label)
        future_return_df[label] = re.stack(dropna=False)
    future_return_df = future_return_df.reset_index().rename(columns={'level_0': 'date', 'level_1': 'stock'})
    all_label_list = ori_label_list.copy()
    for l in ori_label_list:
        all_label_list.append('industry_' + l)
        future_return_df['industry_' + l] = future_return_df[['date', 'industry_code_all', l]].dropna().groupby(
            ['date', 'industry_code_all']).transform(lambda x: x - x.mean())
    future_return_df = future_return_df.set_index(['date', 'stock'])
    future_return_df = future_return_df[future_return_df['is_valid'] == 1]
    if winsard_flag:
        all_winsard_label_list = [l+'_winsard' for l in all_label_list]
        future_return_df[all_winsard_label_list] = apply_parallel(future_return_df[all_label_list].groupby(level=0), winsorize)
        all_label_list+=all_winsard_label_list
    if norm_flag == True:
        future_return_df[all_label_list] = apply_parallel(future_return_df[all_label_list].groupby(level=0),
                                                          standardlize)
    return future_return_df.fillna(fill_value)
def pm_update_depart_feature(depart_factor_list,own_factor_list,start_date,end_date,own=True, check=True, silent=False):
    shipan_factors = pd.read_pickle(factor_source_path)['shipan_factors']
    is_valid = pd.read_pickle(basic_daily_path+'is_valid.pkl')
    flag = True
    neu_sample = get_neu_sample(basic_daily_path, dict(zip(depart_factor_list, [depart_factor_pool_path] * len(depart_factor_list))), start_date, end_date, 0)
    date_list = get_trade_date(start_date, end_date)
    if own:
        pm_update_vwap_sample(start_date,end_date, check=True, silent=False)
    for date in date_list:
        date = date.strftime('%Y%m%d')
        tmp = neu_sample.loc[date].reset_index()
        tmp.rename(columns={'level_0': 'date', 'level_1': 'columns'}, inplace=True)
        tmp['date'] = pd.to_datetime(tmp['date'])
        
        own_sample = pd.read_pickle(sample_norm_path + date + '.pkl')[['stock'] + own_factor_list]
        tmp = tmp.merge(own_sample, on=['stock'], how='left')
        tmp = tmp.fillna(0)
        if flag:
            valid_d = date
        else:
            valid_d = get_trade_date(date,-2)[0].strftime('%Y%m%d')
        this_stock = is_valid.loc[valid_d]
        this_stock = this_stock[this_stock==1].index
        tmp =tmp[tmp['stock'].isin(this_stock)]
        pd.to_pickle(tmp.sort_index(by='stock').reset_index(drop=True), day_depart_feature_path + date + '.pkl')
        if check:
            check_single_sample(day_depart_feature_path, date, sorted(list(set(depart_factor_list + own_factor_list)&set(shipan_factors))), silent)
def am_update_depart_feature(sample_path,hsample_path,day_factor_list,fix_factor_list, start_date, end_date, check=True, silent=False):
    shipan_factors = pd.read_pickle(factor_source_path)['shipan_factors']
    is_valid = pd.read_pickle(basic_daily_path+'is_valid.pkl')
    flag = False
    neu_sample = get_neu_sample(basic_daily_path, dict(zip(fix_factor_list, [depart_factor_pool_path] * len(fix_factor_list))), start_date, end_date, 1)
    neu_sample = neu_sample.fillna(0)
    date_list = get_trade_date(start_date, end_date)
    for date in date_list:
        date = date.strftime('%Y%m%d')
        tmp = neu_sample.loc[date].reset_index()
        tmp.rename(columns={'level_0': 'date', 'level_1': 'columns'}, inplace=True)
        tmp['date'] = pd.to_datetime(tmp['date'])
        pre_date = get_trade_date(date, -2)[0].strftime('%Y%m%d')
        if flag:
            valid_d = date
        else:
            valid_d = pre_date
        this_stock = is_valid.loc[valid_d]
        this_stock = this_stock[this_stock==1].index
        tmp =tmp[tmp['stock'].isin(this_stock)]
        pd.to_pickle(tmp.sort_index(by='stock').reset_index(drop=True), hsample_path + date + '.pkl')
        if check:
            check_single_sample(hsample_path, date, sorted(list(set(fix_factor_list)&set(shipan_factors))), silent)
            
def am_update_depart_feature_tmp(sample_path,hsample_path,day_factor_list,fix_factor_list, date, check=True, silent=False):
    is_valid = pd.read_pickle(basic_daily_path+'is_valid.pkl')
    fix_today_path = fix_1300_pkl_path+date+'/'
    fix_path_list = [fix_today_path] * len(fix_factor_list)
    neu_sample = get_neu_sample(basic_daily_path, dict(zip(fix_factor_list, fix_path_list)), date, date, 1)
    neu_sample = neu_sample.fillna(0)
    # get pre_date sample
    tmp = neu_sample.reset_index()
    tmp.rename(columns={'level_0': 'date', 'level_1': 'columns'}, inplace=True)
    tmp['date'] = pd.to_datetime(tmp['date'])
    pre_date = get_trade_date(date, -2)[0].strftime('%Y%m%d')

    flag = False
    if flag:
        valid_d = date
    else:
        valid_d = pre_date
    this_stock = is_valid.loc[valid_d]
    this_stock = this_stock[this_stock==1].index
    tmp =tmp[tmp['stock'].isin(this_stock)]
    pd.to_pickle(tmp.sort_index(by='stock').reset_index(drop=True), hsample_path + date + '.pkl')
    if check:
        check_single_sample(hsample_path, date, fix_factor_list, silent)
    return
def am_update_feature(factor_list, hfactor_list, start_date, end_date, check=True, silent=False):
    hpath_list = [hfactor_data_path] * len(hfactor_list)
    neu_sample = get_neu_sample(basic_daily_path, dict(zip(hfactor_list, hpath_list)), start_date, end_date, 1)
    # get pre_date sample
    date_list = get_trade_date(start_date, end_date)
    for date in date_list:
        date = date.strftime('%Y%m%d')
        tmp = neu_sample.loc[date].reset_index()
        tmp.rename(columns={'level_0': 'date', 'level_1': 'columns'}, inplace=True)
        pre_date = get_trade_date(date, -2)[0].strftime('%Y%m%d')
        predate_sample = pd.read_pickle(sample_norm_path + pre_date + '.pkl')[['stock'] + factor_list]
        tmp = tmp.merge(predate_sample, on=['stock'], how='left')
        tmp = tmp.fillna(0)
        pd.to_pickle(tmp.sort_index(by='stock').reset_index(drop=True), hsample_norm_path + date + '.pkl')
    if check:
        Parallel(num_threads)(
            delayed(check_single_sample)(hsample_norm_path, date.strftime('%Y%m%d'), factor_list + hfactor_list, silent)
            for date in date_list)
    return


def pm_update_label(label_path,start_date, end_date,winsard_flag=True, norm_flag=True,sharp_flag=False,lag_list=[1,3,5],fill_value=0):
    max_lag = np.array(lag_list).max()+1
    label_start_date = get_trade_date(start_date, -max_lag)[0].strftime('%Y%m%d')
    label_end_date = get_trade_date(end_date, max_lag)[-1].strftime('%Y%m%d')
    label_date_list = get_trade_date(label_start_date, end_date)
    date_list = get_trade_date(start_date, end_date)
    trade_price = get_trade_price(basic_daily_path, minute_data_path, label_start_date, label_end_date,
                                  transaction_time='1300', transaction_period=120)
    label = get_future_return(basic_daily_path, trade_price, price_type='1300_1459', lag_list=lag_list, shift_lag=1,
                            winsard_flag=winsard_flag,norm_flag=norm_flag,sharp_flag=sharp_flag,fill_value=fill_value)
    
    for date in label_date_list:
        print(date)
        date = date.strftime('%Y%m%d')
        tmp = label.loc[date].reset_index()
        for l in lag_list:
            tmp = get_label_bin(tmp, '1300_1459_re_'+str(l)+'d')
        tmp.rename(columns={'level_0': 'date', 'level_1': 'columns'}, inplace=True)
        pd.to_pickle(tmp.sort_index(by='stock').reset_index(drop=True), label_path + date + '.pkl')
def pm_update_vwap_label(label_path, start_date, end_date,winsard_flag=True, norm_flag=True,sharp_flag=False,lag_list=[1,3,5],fill_value=0):
    max_lag = np.array(lag_list).max()+2
    label_start_date = get_trade_date(start_date, -max_lag)[0].strftime('%Y%m%d')
    label_end_date = get_trade_date(end_date, max_lag)[-1].strftime('%Y%m%d')
    label_date_list = get_trade_date(label_start_date, end_date)
    date_list = get_trade_date(start_date, end_date)
    trade_price_vwap = get_trade_price(basic_daily_path, minute_data_path, label_start_date, label_end_date,
                                       price_type='vwap')
    label_vwap = get_future_return(basic_daily_path, trade_price_vwap, price_type='vwap', lag_list=lag_list,
                                   shift_lag=0,winsard_flag=winsard_flag,norm_flag=norm_flag,sharp_flag=sharp_flag,fill_value=fill_value)
    label_vwap_team = get_future_return_team(basic_daily_path, trade_price_vwap, price_type='vwap', 
                lag_list=[1, 3, 5], shift_lag=0,winsard_flag=True, norm_flag=True)
    label_vwap[label_vwap_team.columns] = label_vwap_team
    trade_price_0930_1129 = get_trade_price(basic_daily_path, minute_data_path, label_start_date,
                                                          label_end_date, transaction_time='0930',
                                                          transaction_period=120)
    label_0930_1129 = get_future_return(basic_daily_path, trade_price_0930_1129, price_type='0930_1129', lag_list=lag_list,
                                        shift_lag=0,winsard_flag=winsard_flag,norm_flag=norm_flag,sharp_flag=sharp_flag,fill_value=fill_value)
    label_vwap[label_0930_1129.columns] = label_0930_1129
    label = label_vwap.reset_index().rename(columns={'level_0': 'date', 'level_1': 'columns'})
    for date in label_date_list:
        print(date)
        tmp = label[label['date'] == date]
        for l in lag_list:
            tmp = get_label_bin(tmp, 'vwap_re_'+str(l)+'d')
            tmp = get_label_bin(tmp, '0930_1129_re_'+str(l)+'d')
        date = date.strftime('%Y%m%d')
        pd.to_pickle(tmp.sort_index(by='stock').reset_index(drop=True), label_path + date + '.pkl')
def pm_update_vwap_sample(start_date, end_date, check=True, silent=False):
    factor_list = sorted([f[:-4] for f in os.listdir(factor_data_path) if f.endswith('.pkl')])
    fund_factor_list = [f[:-4] for f in os.listdir(fund_factor_data_path) if f.endswith('.pkl')]
    path_list = [factor_data_path] * len(factor_list) + [fund_factor_data_path] * len(fund_factor_list)
    print(len(factor_list + fund_factor_list), len(path_list))
    factor_path_dict = dict(zip(factor_list + fund_factor_list, path_list))
    neu_sample = get_neu_sample(basic_daily_path, factor_path_dict, start_date, end_date, 0)
    print('daily fund factor finish')
    neu_sample = neu_sample.reindex(columns=sorted(neu_sample.columns))
    neu_sample = neu_sample.reset_index().rename(columns={'level_0': 'date', 'level_1': 'columns'})

    date_list = get_trade_date(start_date, end_date)
    for date in date_list:
        print(date)
        x_sample = neu_sample[neu_sample['date'] == date].fillna(0)
        date = date.strftime('%Y%m%d')
        pd.to_pickle(x_sample.sort_index(by='stock').reset_index(drop=True), sample_norm_path + date + '.pkl')
    if check:
        Parallel(num_threads)(
            delayed(check_single_sample)(sample_norm_path, date.strftime('%Y%m%d'), factor_list + fund_factor_list,
                                         silent) for date in date_list)
    return
    
def single(sample,f,stock_list):
    df = sample[f].unstack().reindex(columns=stock_list)
    save_data(df,neu_factor_data_path+f+'.pkl')
def get_day_sample(day,factor_list):
    return pd.read_pickle(sample_norm_path + day+'.pkl').set_index(['date','stock'],drop=True)[factor_list]
def get_org_factor(factor_list,start_date,end_date):
    stock_list,date_list = get_stock_date(start_date,end_date)
    sample = Parallel(num_threads)(delayed(get_day_sample)(day,factor_list) for day in date_list)
    sample = pd.concat(sample)
    Parallel(num_threads)(delayed(single)(sample,f,stock_list) for f in factor_list)
def factor_transform(f,plus,start_date,end_date,reform_window=20):
    ori_start_date = get_trade_date(start_date,-(reform_window))[0]
    df = pd.read_pickle(neu_factor_data_path+f[:-(len(plus)+1)]+'.pkl').loc[ori_start_date:end_date]
    # 不同的算子
    if plus == 'mean20':
        f1 = df.rolling(20,1).mean()
    elif plus == 'min20':
        f1 = df.rolling(20,1).min()
    elif plus == 'max20':
        f1 = df.rolling(20,1).max()
    elif plus == 'std20':
        f1 = df.rolling(20,1).std()
    elif plus == 'skew20':
        f1 = df.rolling(20,1).skew()
    elif plus == 'kurt20':
        f1 = df.rolling(20,1).kurt()
    elif plus == 'sharpe20':
        f1 = df.rolling(20,1).mean() / df.rolling(20,1).std()
    elif plus == 'cv20':
        f1 = df.rolling(20,1).std() / df.rolling(20,1).mean()
    elif plus == 'meandis20':
        f1 = (df - df.rolling(10,1).mean()).rolling(10,1).mean()
    elif plus == 'mindis20':
        f1 = (df - df.rolling(10,1).min()).rolling(10,1).mean()
    elif plus == 'maxdis20':
        f1 = (df - df.rolling(10,1).max()).rolling(10,1).mean()
    save_data(f1.loc[start_date:end_date],extend_factor_data_path+f+'.pkl')
def get_single_factor2(f,date):
    temp = pd.read_pickle(extend_factor_data_path+f+'.pkl').loc[date]
    return temp
def get_single_sample(factor_list,date):
    print(date)
    sample = {}
    for f in factor_list:
        sample[f] = get_single_factor2(f,date)
    sample = pd.DataFrame(sample)
    sample['date'] = pd.to_datetime(date)
    sample['stock'] = sample.index
    sample = sample.reset_index(drop=True)
    is_valid = pd.read_pickle(basic_daily_path+'is_valid.pkl').loc[date]
    industry_code = pd.read_pickle(basic_daily_path+'industry_code_all.pkl')
    idst = industry_code.loc[date]
    idst = idst[sample['stock'].values]
    sample = sample[sample['stock'].isin(is_valid[is_valid>0].index)]
    sample.loc[:,factor_list]= Normalization(sample.loc[:,factor_list],idst,axis=1).norm_dataframe()
    sample = sample.reset_index(drop=True).rename(columns={'level_0':'date','level_1':'stock'}).sort_values(by=['date','stock'])
    sample.to_pickle(extend_sample_path+date+'.pkl')
def update_lf_sample(start_date,end_date):
    extend_factor_list = pd.read_pickle(group_extend_path+'extend_factor_list.pkl')
    extend_map_dict = pd.read_pickle(group_extend_path+'extend_dict.pkl')
    ori_factor_list = pd.read_pickle(group_extend_path+'org_factor_list.pkl')
    get_org_factor(ori_factor_list,start_date,end_date)
    Parallel(num_threads)(delayed(factor_transform)(f,extend_map_dict[f],start_date,end_date) for f in extend_factor_list)
    update_date_list = get_trade_date(start_date,end_date)
    for date in update_date_list:
        get_single_sample(extend_factor_list,date.strftime('%Y%m%d'))
    Parallel(num_threads)(delayed(check_single_sample)(extend_sample_path, date.strftime('%Y%m%d'), extend_factor_list, False) for date in update_date_list)

def update_sample(start_date, end_date=None, mode=0):
    winsard_flag = True
    norm_flag = True
    sharp_flag = False
    lag_list = [1,3,5,10,20]
    fill_value = np.nan
    own = False
    factor_list = pd.read_pickle(factor_list_path)
    hfactor_list = sorted([f[:-4] for f in os.listdir(hfactor_data_path) if f.endswith('.pkl')])
    all_hfactor_list = pd.read_pickle(hfactor_list_path)
    factor_info = pd.read_pickle(factor_info_path)
    day_factors = factor_info['day_factors']
    fix_factors = factor_info['fix_factors']
    depart_day_factors = factor_info['depart_day_factors']
    own_day_factors = factor_info['own_day_factors']
    if mode == 0:
        am_update_feature(factor_list, hfactor_list, start_date, end_date)
    elif mode == 1:
        pm_update_label(all_hfactor_list, start_date, end_date)
        pm_update_vwap_sample(start_date, end_date)
        pm_update_vwap_label(factor_list, start_date, end_date)
    elif mode == 2:
        if end_date is None:
            am_update_depart_feature_tmp(day_depart_feature_path,fix_depart_feature_path,day_factors,fix_factors, start_date, check=True, silent=False)
        else:
            am_update_depart_feature(day_depart_feature_path,fix_depart_feature_path,day_factors,fix_factors, start_date, end_date, check=True, silent=False)
    elif mode == 3:
        pm_update_depart_feature(depart_day_factors,own_day_factors,start_date,end_date,own)
    elif mode == 4:
        pm_update_vwap_label(day_depart_label_path, start_date, end_date,winsard_flag, norm_flag,sharp_flag,lag_list,fill_value)
    elif mode == 5:
        pm_update_label(fix_depart_label_path,start_date, end_date,winsard_flag, norm_flag,sharp_flag,lag_list,fill_value)

def load_sample(factor_list,sample_dates=[],strategy_type='lf',label_name='vwap_re_5d',train_flag=True):
    if strategy_type in timepoint_list:
        hf_flag = True
    else:
        hf_flag = False
    factor_day_path_dict = pd.read_pickle(factor_day_path_dict_path)
    factor_fix_path_dict = pd.read_pickle(factor_fix_path_dict_path)
    factor_label_path_dict = pd.read_pickle(factor_label_path_dict_path)
    factor_info = {}
    for k,v in factor_day_path_dict.items():
        factor_info[k] = sorted(list(set(factor_list)&set(v[1])))
    common_factors = sorted(list(set(factor_info['depart_day_factors'])&set(factor_info['own_day_factors'])))
    factor_info['own_day_factors'] = sorted(list(set(factor_info['own_day_factors'])-set(common_factors)))
    factor_own = [i[:-11] for i in factor_list if 'TeamSample' in i.split('_')]
    if len(factor_own)>0:        
        factor_info['own_day_factors'] = sorted(list(set(factor_info['own_day_factors']+factor_own)))
        factor_info['depart_day_factors'] = sorted(list(set(factor_info['depart_day_factors'])-set(factor_own)))
        print(factor_own[0],len(factor_own),len(factor_info['own_day_factors']),len(factor_info['depart_day_factors']))
        factor_list = sorted(list(set(factor_info['own_day_factors']+factor_info['depart_day_factors'])))
        
    factor_fix_info = {}
    for k,v in factor_fix_path_dict.items():
        factor_fix_info[k] = sorted(list(set(factor_list)&set(v)))
    sample = []
    for day in sample_dates:
        sample_day = None
        feature_day = day
        for k,v in factor_info.items():
            if len(v)>0:
                if hf_flag:
                    feature_day = fa.tradingday(day,-2)[0]
                df = pd.read_pickle(factor_day_path_dict[k][0]+feature_day+'.pkl')[['date','stock']+v]
                if sample_day is None:
                    sample_day = df
                else:
                    sample_day = sample_day.merge(df,on=['stock'],how='left')
        for k,v in factor_fix_info.items():
            if len(v)>0:
                df = pd.read_pickle(feature_fix_path+strategy_type+'/feature/'+day+'.pkl')[['date','stock']+v]
                if sample_day is None:
                    sample_day = df
                else:
                    sample_day = sample_day.merge(df,on=['stock'],how='left')
        if train_flag:
            df = pd.read_pickle(factor_label_path_dict[strategy_type]+day+'.pkl')[['date','stock',label_name]]
            sample_day = df.merge(sample_day[['stock']+factor_list],how='left',on=['stock'])
            sample_day = sample_day[~np.isnan(sample_day[label_name])]
        sample.append(sample_day)
    return pd.concat(sample)