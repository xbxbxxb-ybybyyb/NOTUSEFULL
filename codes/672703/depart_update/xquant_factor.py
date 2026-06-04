import numpy as np
import pandas as pd
import dill as pickle
import os
from sklearn.externals.joblib import Parallel, delayed
import sys
sys.path.insert(0, '/data/user/013546/tools/')
from clean_factor import *
import datetime
from xquant.factordata import FactorData
fa = FactorData()
from xquant.xqutils.helper import link
lm = link.LinkMessage()

sample_raw_path = '/data/group/800020/AlphaDataCenter/Sample/RawSample/'
sample_norm_path = '/data/group/800020/AlphaDataCenter/Sample/NormSample/'
hsample_raw_path = '/data/group/800020/AlphaDataCenter/HFSample/RawSample/'
hsample_norm_path = '/data/group/800020/AlphaDataCenter/HFSample/NormSample/'
basic_data_path = '/data/group/800020/AlphaDataCenter/Basic/daily/'
minute_data_path = '/data/group/800020/AlphaDataCenter/Basic/minute/'
factor_data_path = '/data/group/800020/AlphaDataCenter/Factor/daily/'
hfactor_data_path = '/data/group/800020/AlphaDataCenter/HFactor/one_pm/'
fund_factor_data_path = '/data/group/800020/AlphaDataCenter/Factor/fundamental_tmp/'
day_depart_feature_path = '/data/group/800020/AlphaDataCenter/Department/DepartSample/Sample/feature/'
day_depart_label_path = '/data/group/800020/AlphaDataCenter/Department/DepartSample/Sample/label/'
fix_depart_feature_path = '/data/group/800020/AlphaDataCenter/Department/DepartSample/HFSample/feature/'
fix_depart_label_path = '/data/group/800020/AlphaDataCenter/Department/DepartSample/HFSample/label/'
fix_1300_pkl_path = '/data/user/015623/FactorFactory/PICKLE/'
stock_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Department/DepartSample/stock_list.pkl')
num_threads = 20
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
        df = pd.read_pickle(factor_path + f + '.pkl').loc[start_date:end_date].reindex(columns=stock_list)
    except Exception:
        df = pd.read_pickle(basic_data_path+'is_valid.pkl').loc[start_date:end_date].reindex(columns=stock_list)
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
    is_valid = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/is_valid.pkl').loc[start_date:end_date]
    stock_list = is_valid.columns.tolist()
    date_list = [d.strftime('%Y%m%d') for d in is_valid.index]
    return stock_list, date_list


def get_factor_names(factor_type='Fix1300'):
    map_type = {'Fix1300': 'fix_factors', 'day': 'day_factors'}
    factor_list = pd.read_pickle(
        '/data/group/800020/AlphaExperiment/Factor/DepartmentSample/' + map_type[factor_type] + '.pkl')
    return factor_list

def get_single_date(date, factor_list, stock_list):
    if date >= '20200101':
        df = fa.get_factor_value('x_day_lib', stock=stock_list, mddate=[date], factor_names=factor_list).reset_index()
    else:
        path = '/data/user/015518/quant_data/qualified_factor/x_day_lib/latest/'
        df = pd.read_parquet(path + 'mddate=' + date + '/')[['stock'] + factor_list]

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
    data[factor_list] = data.groupby(by=['date', 'industry_code_all'])[factor_list].transform(
        lambda x: x.fillna(x.mean()))
    data = data.set_index(['date', 'stock'])
    data = neutralize(data[factor_list], data[neu_basic.columns], data_norm=factor_list, how_norm=['log_mkt'])
    data = apply_parallel(data.groupby(level=0), standard_winsor)
    return data.fillna(0)


def get_trade_price(basic_daily_path, basic_minute_path, start_date='', end_date='',
                    price_type='minute', transaction_price='vwap', transaction_time='0930', transaction_period=120):
    adjfactor = pd.read_pickle(basic_daily_path + 'adjfactor.pkl').loc['20140101':]
    trade_price = pd.DataFrame(index=adjfactor.loc[start_date:end_date].index, columns=adjfactor.columns)
    if price_type == 'minute':
        assert len(transaction_time) == 4
        assert transaction_time[:2] in ['09', '10', '11', '13', '14']
        assert int(transaction_time[2:]) >= 0 and int(transaction_time[2:]) < 60
        assert int(transaction_time) >= 930 and int(transaction_time) < 1130 or int(transaction_time) >= 1300 and int(
            transaction_time) < 1500
        assert transaction_period > 0 and isinstance(transaction_period, int) if transaction_price == 'vwap' else True
        os.mkdir('temp_for_check_prediction_minute_trade_price') if not os.path.exists(
            'temp_for_check_prediction_minute_trade_price') else None
        time_saver = transaction_price + '_' + transaction_time + '_' + str(transaction_period)
        if os.path.exists('temp_for_check_prediction_minute_trade_price/' + time_saver + '.pkl'):
            trade_price_0 = pd.read_pickle(
                'temp_for_check_prediction_minute_trade_price/' + time_saver + '.pkl').dropna(how='all', axis=0)
            add_trade_price_dates = sorted(list(set(trade_price.index) - set(trade_price_0.index)))
            same_trade_price_dates = sorted(list(set(trade_price.index) & set(trade_price_0.index)))
            if len(same_trade_price_dates)>0:
                trade_price = trade_price_0.loc[same_trade_price_dates]
        if not os.path.exists(
                'temp_for_check_prediction_minute_trade_price/' + time_saver + '.pkl') or add_trade_price_dates:
            price = pd.DataFrame(index=adjfactor.index, columns=adjfactor.columns, data=np.nan)
            if not os.path.exists('temp_for_check_prediction_minute_trade_price/' + time_saver + '.pkl'):
                add_trade_price_dates = adjfactor.index
            elif len(same_trade_price_dates)>0:
                price.loc[same_trade_price_dates] = trade_price_0.loc[same_trade_price_dates]
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
            price.to_pickle('temp_for_check_prediction_minute_trade_price/' + time_saver + '.pkl')
            trade_price = price.loc[trade_price.index]
    else:
        trade_price = pd.read_pickle(basic_daily_path + price_type + '.pkl').loc[trade_price.index]
    return trade_price


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
    is_valid = pd.read_pickle(basic_data_path + 'is_valid.pkl')
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


def get_future_return(basic_daily_path, trade_price, price_type='1300_1459', lag_list=[1, 3, 5], shift_lag=1,
                      winsard_flag=True, norm_flag=True,roll=True,fill_value=np.nan):
    industry_code_all = pd.read_pickle(basic_daily_path + 'industry_code_all.pkl').shift(shift_lag).loc[
        trade_price.index]
    is_valid = pd.read_pickle(basic_daily_path + 'is_valid.pkl').shift(shift_lag).loc[trade_price.index]
    adjfactor = pd.read_pickle(basic_daily_path + 'adjfactor.pkl').loc[trade_price.index]
    future_return_df = industry_code_all.stack(dropna=False).to_frame(name='industry_code_all')
    future_return_df['is_valid'] = is_valid.stack(dropna=False)
    price_adj = trade_price * adjfactor
    date_list = [i.strftime('%Y%m%d') for i in price_adj.index]
    ori_label_list = []
    for lag in lag_list:
        re = price_adj.pct_change(lag).shift(-lag - (1 - shift_lag))
        label = price_type + '_re_' + str(lag) + 'd'
        ori_label_list.append(label)
        future_return_df[label] = re.stack(dropna=False)
    if roll:
        trade_vwap_adj = get_trade_price(basic_data_path, minute_data_path, date_list[0], date_list[-1],
                              price_type = 'vwap')*adjfactor
        re = trade_vwap_adj.rolling(window=5,min_periods=1).mean().shift(shift_lag-6)/price_adj.shift(shift_lag-1)-1
        label = price_type + '_roll5d'
        ori_label_list.append(label)
        future_return_df[label] = re.stack(dropna=False)
    future_return_df = future_return_df.reset_index().rename(columns={'level_0': 'date', 'level_1': 'stock'})
    all_label_list = ori_label_list.copy()
    for l in ori_label_list:
        all_label_list.append('industry_' + l)
        print(l)
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
    is_valid = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/is_valid.pkl')
    flag = True
    neu_sample = get_neu_sample(basic_data_path, depart_factor_list, start_date, end_date, 0)
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
        pd.to_pickle(tmp, day_depart_feature_path + date + '.pkl')
        if check:
            check_single_sample(day_depart_feature_path, date, depart_factor_list + own_factor_list, silent)
def am_update_depart_feature(sample_path,hsample_path,day_factor_list,fix_factor_list, start_date, end_date, check=True, silent=False):
    is_valid = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/is_valid.pkl')
    flag = False
    neu_sample = get_neu_sample(basic_data_path, fix_factor_list, start_date, end_date, 1)
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
        pd.to_pickle(tmp, hsample_path + date + '.pkl')
        if check:
            check_single_sample(hsample_path, date, fix_factor_list, silent)
            
def am_update_depart_feature_tmp(sample_path,hsample_path,day_factor_list,fix_factor_list, date, check=True, silent=False):
    is_valid = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/is_valid.pkl')
    fix_today_path = fix_1300_pkl_path+date+'/'
    fix_path_list = [fix_today_path] * len(fix_factor_list)
    neu_sample = get_neu_sample(basic_data_path, dict(zip(fix_factor_list, fix_path_list)), date, date, 1)
    neu_sample = neu_sample.fillna(0)
    # get pre_date sample
    tmp = neu_sample.reset_index()
    tmp.rename(columns={'level_0': 'date', 'level_1': 'columns'}, inplace=True)
    tmp['date'] = pd.to_datetime(tmp['date'])
    pre_date = get_trade_date(date, -2)[0].strftime('%Y%m%d')
#     predate_sample = pd.read_pickle(sample_path + pre_date + '.pkl')[['stock'] + day_factor_list]
#     tmp = tmp.merge(predate_sample, on=['stock'], how='left')
    flag = False
    if flag:
        valid_d = date
    else:
        valid_d = pre_date
    this_stock = is_valid.loc[valid_d]
    this_stock = this_stock[this_stock==1].index
    tmp =tmp[tmp['stock'].isin(this_stock)]
    pd.to_pickle(tmp, hsample_path + date + '.pkl')
    if check:
        check_single_sample(hsample_path, date, fix_factor_list, silent)
    return
def am_update_feature(factor_list, hfactor_list, start_date, end_date, check=True, silent=False):
    hpath_list = [hfactor_data_path] * len(hfactor_list)
    neu_sample = get_neu_sample(basic_data_path, dict(zip(hfactor_list, hpath_list)), start_date, end_date, 1)
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
        pd.to_pickle(tmp, hsample_norm_path + date + '.pkl')
    if check:
        Parallel(num_threads)(
            delayed(check_single_sample)(hsample_norm_path, date.strftime('%Y%m%d'), factor_list + hfactor_list, silent)
            for date in date_list)
    return


def pm_update_label(label_path,start_date, end_date,winsard_flag=True, norm_flag=True,lag_list=[1,3,5],fill_value=0):
    max_lag = np.array(lag_list).max()+1
    label_start_date = get_trade_date(start_date, -max_lag)[0].strftime('%Y%m%d')
    label_end_date = get_trade_date(end_date, max_lag)[-1].strftime('%Y%m%d')
    label_date_list = get_trade_date(label_start_date, end_date)
    date_list = get_trade_date(start_date, end_date)
    trade_price = get_trade_price(basic_data_path, minute_data_path, label_start_date, label_end_date,
                                  transaction_time='1300', transaction_period=120)
    label = get_future_return(basic_data_path, trade_price, price_type='1300_1459', lag_list=lag_list, shift_lag=1,
                            winsard_flag=winsard_flag,norm_flag=norm_flag,fill_value=fill_value)
    for date in label_date_list:
        print(date)
        date = date.strftime('%Y%m%d')
        tmp = label.loc[date].reset_index()
        for l in lag_list:
            tmp = get_label_bin(tmp, '1300_1459_re_'+str(l)+'d')
        tmp.rename(columns={'level_0': 'date', 'level_1': 'columns'}, inplace=True)
        pd.to_pickle(tmp.sort_index(by='stock').reset_index(drop=True), label_path + date + '.pkl')
def pm_update_vwap_label(label_path, start_date, end_date,winsard_flag=True, norm_flag=True,lag_list=[1,3,5],fill_value=0):
    max_lag = np.array(lag_list).max()+2
    label_start_date = get_trade_date(start_date, -max_lag)[0].strftime('%Y%m%d')
    label_end_date = get_trade_date(end_date, max_lag)[-1].strftime('%Y%m%d')
    label_date_list = get_trade_date(label_start_date, end_date)
    date_list = get_trade_date(start_date, end_date)
    trade_price_vwap = get_trade_price(basic_data_path, minute_data_path, label_start_date, label_end_date,
                                       price_type='vwap')
    label_vwap = get_future_return(basic_data_path, trade_price_vwap, price_type='vwap', lag_list=lag_list,
                                   shift_lag=0,winsard_flag=winsard_flag,norm_flag=norm_flag,fill_value=fill_value)
    trade_price_0930_1129 = get_trade_price(basic_data_path, minute_data_path, label_start_date,
                                                          label_end_date, transaction_time='0930',
                                                          transaction_period=120)
    label_0930_1129 = get_future_return(basic_data_path, trade_price_0930_1129, price_type='0930_1129', lag_list=lag_list,
                                        shift_lag=0,winsard_flag=winsard_flag,norm_flag=norm_flag,fill_value=fill_value)
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
    neu_sample = get_neu_sample(basic_data_path, factor_path_dict, start_date, end_date, 0)
    print('daily fund factor finish')
    neu_sample = neu_sample.reindex(columns=sorted(neu_sample.columns))
    neu_sample = neu_sample.reset_index().rename(columns={'level_0': 'date', 'level_1': 'columns'})

    date_list = get_trade_date(start_date, end_date)
    for date in date_list:
        print(date)
        x_sample = neu_sample[neu_sample['date'] == date].fillna(0)
        date = date.strftime('%Y%m%d')
        pd.to_pickle(x_sample, sample_norm_path + date + '.pkl')
    if check:
        Parallel(num_threads)(
            delayed(check_single_sample)(sample_norm_path, date.strftime('%Y%m%d'), factor_list + fund_factor_list,
                                         silent) for date in date_list)
    return


def update_sample(start_date, end_date=None, mode=0):
    winsard_flag = True
    norm_flag = True
    lag_list = [1,3,5,10,20]
    fill_value = 0
    own = False
    factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Sample/factor_list.pkl')
    hfactor_list = sorted([f[:-4] for f in os.listdir(hfactor_data_path) if f.endswith('.pkl')])
    all_hfactor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/HFSample/hfactor_list.pkl')
    factor_info = pd.read_pickle('/data/group/800020/AlphaDataCenter/Department/DepartSample/factor_info_nn.pkl')
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
        pm_update_vwap_label(day_depart_label_path, start_date, end_date,winsard_flag, norm_flag,lag_list,fill_value)
    elif mode == 5:
        pm_update_label(fix_depart_label_path,start_date, end_date,winsard_flag, norm_flag,lag_list,fill_value)
factor_info = pd.read_pickle('/data/group/800020/AlphaDataCenter/Department/DepartSample/factor_info_nn.pkl')
factor_list = factor_info['depart_day_factors']
start_date = '20150101'
end_date = '20190630'
res = get_factors_xquant(factor_list, start_date, end_date)
pd.to_pickle(res,'/data/user/013546/rubbish/ori_depart.pkl')