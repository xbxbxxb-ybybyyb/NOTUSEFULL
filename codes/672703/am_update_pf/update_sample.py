import numpy as np
import pandas as pd
import os
from sklearn.externals.joblib import Parallel,delayed
import sys
import datetime
sys.path.insert(0,'am_update_port/')
from clean_factor import *

sample_raw_path = '/data/group/800020/AlphaDataCenter/Sample/RawSample/'
sample_norm_path = '/data/group/800020/AlphaDataCenter/Sample/NormSample/'
hsample_raw_path = '/data/group/800020/AlphaDataCenter/HFSample/RawSample/'
hsample_norm_path = '/data/group/800020/AlphaDataCenter/HFSample/NormSample/'
basic_data_path =  '/data/group/800020/AlphaDataCenter/Basic/daily/'
minute_data_path = '/data/group/800020/AlphaDataCenter/Basic/minute/'
factor_data_path = '/data/group/800020/AlphaDataCenter/Factor/daily/'
hfactor_data_path = '/data/group/800020/AlphaDataCenter/HFactor/one_pm/'
fund_factor_data_path = '/data/group/800020/AlphaDataCenter/Factor/fundamental_tmp/'
def get_single_factor(factor_path,f,start_date,end_date):
    df = pd.read_pickle(factor_path+f+'.pkl').loc[start_date:end_date]
    return df.stack(dropna=False)
def get_factors(factor_path,factor_list,start_date,end_date):
    from sklearn.externals.joblib import Parallel,delayed
    import multiprocessing
    final_factor = Parallel(n_jobs=int(multiprocessing.cpu_count()))(delayed(get_single_factor)(factor_path,f,start_date,end_date) for f in factor_list)
    final_factor =dict(zip(factor_list,final_factor))
    final_factor = pd.DataFrame(final_factor)
    return final_factor
#处理市值和行业
def get_mkt_indus(path,start_date,end_date,shift_lag=1):
    mkt = pd.read_pickle(path+'mkt_cap_ard.pkl').shift(shift_lag).loc[start_date:end_date]
    log_mkt = np.log(mkt)
    neu_basic = log_mkt.stack(dropna=False).to_frame(name='log_mkt')
    #处理行业
    industry_code_all = pd.read_pickle(path+'industry_code_all.pkl').shift(shift_lag).loc[start_date:end_date]
    industry_dummy = pd.get_dummies(industry_code_all.stack(dropna=False))
    neu_basic[industry_dummy.columns] = industry_dummy
    return neu_basic
def get_neu_sample(basic_path,factor_path,factor_list,start_date,end_date,shift_lag):
    tool_name = ['is_valid_raw','is_valid','industry_code_all']
    data = get_factors(factor_path,factor_list,start_date,end_date)
    for t in tool_name:
        tmp = pd.read_pickle(basic_path+t+'.pkl').shift(shift_lag).loc[start_date:end_date]
        data[t] = tmp.stack(dropna=False)
    neu_basic = get_mkt_indus(basic_path,start_date,end_date,shift_lag)
    data[neu_basic.columns] = neu_basic
    data = data[data['is_valid']==1].reset_index()
    data = data.rename(columns={'level_0':'date','level_1':'stock'})
    data[factor_list] = data.groupby(by=['date','industry_code_all'])[factor_list].transform(lambda x:x.fillna(x.mean()))
    
    data = data.set_index(['date','stock'])
    data = neutralize(data[factor_list],data[neu_basic.columns],data_norm=factor_list,how_norm=['log_mkt'])
    data = apply_parallel(data.groupby(level=0),standard_winsor)
    return data.fillna(0)
def get_trade_price(basic_daily_path,basic_minute_path,start_date='',end_date='',
                    price_type='minute',transaction_price='vwap',transaction_time='0930',transaction_period=120):
    adjfactor = pd.read_pickle(basic_daily_path + 'adjfactor.pkl').loc[start_date:end_date]
    trade_price = pd.DataFrame(index=adjfactor.index, columns=adjfactor.columns)
    if price_type=='minute':
        assert len(transaction_time)==4
        assert transaction_time[:2] in ['09', '10', '11', '13', '14']
        assert int(transaction_time[2:])>=0 and int(transaction_time[2:])<60
        assert int(transaction_time)>=930 and int(transaction_time)<1130 or int(transaction_time)>=1300 and int(transaction_time)<1500
        assert transaction_period>0 and isinstance(transaction_period, int) if transaction_price=='vwap' else True
        os.mkdir('temp_for_check_prediction_minute_trade_price') if not os.path.exists('temp_for_check_prediction_minute_trade_price') else None
        time_saver = transaction_price + '_' + transaction_time + '_' + str(transaction_period)
        if os.path.exists('temp_for_check_prediction_minute_trade_price/' + time_saver + '.pkl'):
            trade_price = pd.read_pickle('temp_for_check_prediction_minute_trade_price/' + time_saver + '.pkl').loc[trade_price.index]
        else:
            price = pd.DataFrame(index=adjfactor.index, columns=adjfactor.columns, data=np.nan)
            for date in [d.strftime('%Y%m%d') for d in adjfactor.index]:
                if transaction_price in ['open', 'close']:
                    price.loc[date] = pd.read_pickle(basic_minute_path + transaction_price.capitalize() + '/' + date + '.pkl').loc[pd.Timestamp(date+transaction_time+'00')]
                else:
                    minute_vol = pd.read_pickle(basic_minute_path + 'Volume/' + date + '.pkl').loc[pd.Timestamp(date+transaction_time+'00'):].iloc[:transaction_period].sum()
                    minute_amt = pd.read_pickle(basic_minute_path + 'Amount/' + date + '.pkl').loc[pd.Timestamp(date+transaction_time+'00'):].iloc[:transaction_period].sum()
                    price.loc[date] = minute_amt / minute_vol
                price[np.isinf(price)] = np.nan
            price.to_pickle('temp_for_check_prediction_minute_trade_price/' + time_saver + '.pkl')
            trade_price = price.loc[trade_price.index] 
    else:
        trade_price = pd.read_pickle(basic_daily_path +price_type+ '.pkl').loc[trade_price.index]
    return trade_price
#高频价格与is_valid生成
def get_valid(basic_daily_path,trade_price):
    adjfactor = pd.read_pickle(basic_daily_path + 'adjfactor.pkl').loc[trade_price.index]
    pre_close = pd.read_pickle(basic_daily_path + 'pre_close.pkl').loc[trade_price.index]
    maxupordown = ((trade_price-pre_close) / pre_close).abs().values >= 0.098
    is_valid_ori = pd.read_pickle(basic_daily_path + 'isvalid_and_not_open_updown_limit.pkl').loc[trade_price.index].astype(bool).values
    is_valid = pd.DataFrame(maxupordown&is_valid_ori,index=trade_price.index,columns=trade_price.columns)
    return is_valid
def get_trade_date(start_date,window):
    is_valid = pd.read_pickle(basic_data_path+'is_valid.pkl')
    if type(window)==type(start_date):
        return is_valid.loc[start_date:window].index
    elif window>0:
        return is_valid.loc[start_date:].iloc[:window].index
    else:
        return is_valid.loc[:start_date].iloc[window:].index
def get_future_return(basic_daily_path,trade_price,price_type='1300_1459',lag_list = [1,3,5],shift_lag = 1,norm_flag=True):
    industry_code_all =  pd.read_pickle(basic_daily_path+'industry_code_all.pkl').shift(shift_lag).loc[trade_price.index]
    is_valid = pd.read_pickle(basic_daily_path+'is_valid.pkl').shift(shift_lag).loc[trade_price.index]
    adjfactor = pd.read_pickle(basic_daily_path+'adjfactor.pkl').loc[trade_price.index]
    future_return_df = industry_code_all.stack(dropna=False).to_frame(name='industry_code_all')
    future_return_df['is_valid'] = is_valid.stack(dropna=False)
    price_adj = trade_price*adjfactor
    ori_label_list = []
    for lag in lag_list:
        re = price_adj.pct_change(lag).shift(-lag-(1-shift_lag))
        label = price_type+'_re_'+str(lag)+'d'
        ori_label_list.append(label)
        future_return_df[label] = re.stack(dropna=False)
    future_return_df = future_return_df.reset_index().rename(columns={'level_0':'date','level_1':'stock'})
    all_label_list = ori_label_list.copy()
    for l in ori_label_list:
        all_label_list.append('industry_'+l)
        print(l)
        future_return_df['industry_'+l] = future_return_df[['date','industry_code_all',l]].dropna().groupby(['date','industry_code_all']).transform(lambda x:x-x.mean())
    future_return_df = future_return_df.set_index(['date','stock'])
    future_return_df = future_return_df[future_return_df['is_valid']==1]
    if norm_flag==True:
        future_return_df[all_label_list] = apply_parallel(future_return_df[all_label_list].groupby(level=0),standard_winsor)
    
    return future_return_df.fillna(0)
def am_update_feature(factor_list,hfactor_list,start_date,end_date):
    neu_sample = get_neu_sample(basic_data_path,hfactor_data_path,hfactor_list,start_date,end_date,1)
    #get pre_date sample
    date_list = get_trade_date(start_date,end_date)
    for date in date_list:
        date = date.strftime('%Y%m%d')
        tmp = neu_sample.loc[date].reset_index()
        tmp.rename(columns={'level_0':'date','level_1':'columns'},inplace=True)
        pre_date = get_trade_date(date,-2)[0].strftime('%Y%m%d')
        predate_sample = pd.read_pickle(sample_norm_path+pre_date+'.pkl')[['stock']+factor_list]
        tmp = tmp.merge(predate_sample,on=['stock'],how='left')
        tmp = tmp.fillna(0)
        pd.to_pickle(tmp,hsample_norm_path+date+'.pkl')    
def pm_update_label(feature_list,start_date,end_date):
    label_start_date = get_trade_date(start_date,-6)[0].strftime('%Y%m%d')
    label_end_date = get_trade_date(end_date,6)[-1].strftime('%Y%m%d')
    label_date_list = get_trade_date(label_start_date,end_date)
    date_list = get_trade_date(start_date,end_date)
    trade_price = get_trade_price(basic_data_path,minute_data_path,label_start_date,label_end_date,transaction_time='1300',transaction_period=120)
    label = get_future_return(basic_data_path,trade_price,price_type='1300_1459',lag_list = [1,3,5],shift_lag =1)
    for date in label_date_list:
        print(date)
        date = date.strftime('%Y%m%d')
        tmp = label.loc[date].reset_index()
        print(len(tmp))
        tmp.rename(columns={'level_0':'date','level_1':'columns'},inplace=True)
        x_sample = pd.read_pickle(hsample_norm_path+date+'.pkl')[['stock']+feature_list]
        tmp = tmp.merge(x_sample,on=['stock'],how='left')
        tmp = tmp.fillna(0)
        pd.to_pickle(tmp,hsample_norm_path+date+'.pkl')
def pm_update_vwap_label(feature_list,start_date,end_date):
    label_start_date = get_trade_date(start_date,-7)[0].strftime('%Y%m%d')
    label_end_date = get_trade_date(end_date,7)[-1].strftime('%Y%m%d')
    label_date_list = get_trade_date(label_start_date,end_date)
    date_list = get_trade_date(start_date,end_date)
    trade_price_vwap = get_trade_price(basic_data_path,minute_data_path,label_start_date,label_end_date,price_type='vwap')
    label_vwap = get_future_return(basic_data_path,trade_price_vwap,price_type='vwap',lag_list = [1,3,5],shift_lag =0)
    trade_price_0930_1129 = trade_price = get_trade_price(basic_data_path,minute_data_path,label_start_date,label_end_date,transaction_time='0930',transaction_period=120)
    label_0930_1129 = get_future_return(basic_data_path,trade_price,price_type='0930_1129',lag_list = [1,3,5],shift_lag =0)
    label_vwap[label_0930_1129.columns] = label_0930_1129
    label = label_vwap.reset_index().rename(columns={'level_0':'date','level_1':'columns'})
    for date in label_date_list:
        print(date)
        tmp = label[label['date']==date]
        print(len(tmp))
        date = date.strftime('%Y%m%d')
        x_sample = pd.read_pickle(sample_norm_path+date+'.pkl')[['stock']+feature_list]
        tmp = tmp.merge(x_sample,on=['stock'],how='left')
        tmp = tmp.fillna(0)
        pd.to_pickle(tmp,sample_norm_path+date+'.pkl')
def pm_update_vwap_sample(start_date,end_date):
    factor_list = sorted([f[:-4] for f in os.listdir(factor_data_path) if f.endswith('.pkl')])
    neu_sample = get_neu_sample(basic_data_path,factor_data_path,factor_list,start_date,end_date,0)
    print('daily factor finish')
    fund_factor_list = [f[:-4] for f in os.listdir(fund_factor_data_path)  if f.endswith('.pkl')]
    neu_sample_fund = get_neu_sample(basic_data_path,fund_factor_data_path,fund_factor_list,start_date,end_date,0)
    print('fund factor finish')
    neu_sample[neu_sample_fund.columns] = neu_sample_fund
    neu_sample = neu_sample.reindex(columns=sorted(neu_sample.columns))
    neu_sample = neu_sample.reset_index().rename(columns={'level_0':'date','level_1':'columns'})
    
    date_list = get_trade_date(start_date,end_date)
    for date in date_list:
        print(date)
        x_sample = neu_sample[neu_sample['date']==date].fillna(0)
        date = date.strftime('%Y%m%d')
        pd.to_pickle(x_sample,sample_norm_path+date+'.pkl')
    
def update_sample(start_date,end_date,mode):
    factor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Sample/factor_list.pkl')
    hfactor_list = sorted([f[:-4] for f in os.listdir(hfactor_data_path) if f.endswith('.pkl')])
    all_hfactor_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/HFSample/hfactor_list.pkl')
    if mode==0:
        am_update_feature(factor_list,hfactor_list,start_date,end_date)
    elif mode==1:
        pm_update_label(all_hfactor_list,start_date,end_date)
        pm_update_vwap_sample(start_date,end_date)
        pm_update_vwap_label(factor_list,start_date,end_date)