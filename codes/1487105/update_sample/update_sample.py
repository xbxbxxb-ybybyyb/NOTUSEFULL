import numpy as np
import pandas as pd
import os
from sklearn.externals.joblib import Parallel,delayed
import sys
import datetime
from clean_factor import *
from config_path import * 
from xquant.xqutils.helper import link
lm = link.LinkMessage()

num_threads = 5


# -*- coding: utf-8 -*-
"""
@author: chenz
"""
import copy
import numpy as np
import pandas as pd
import warnings
warnings.simplefilter(action = "ignore", category = RuntimeWarning)
## 去极值与标准化程序,结果差距最终在于median的区别
## 输入的factor与industry应当是isvalid=1筛选后的dataframe
## 1.将 nan和inf的值均设为nan
## 2.极值小于有效数字个数的0.1，则进行去极值，否则不去极值
## 3.去极值后如果std==0,则直接减去平均数（避免了标准化后为inf）
## 4.选择功能有axis（对行还是列做去极值以及标准化）
class Normalization:
    def __init__(self,factor,industry,axis=0,remove_extreme_method='mad',standard=True,weight=5):
        self.factor=factor
        self.industry = industry
        self.axis=axis
        self.extreme=remove_extreme_method# 去极值的方法，可供选择'mad'（中位数去极值）,'std'（sigma去极值）
        self.standard=standard
        self.weight=weight
    
    def get_valid(self,factor,industry):# 满足条件1,行业均值填充nan
        # print(factor)
        # factor[np.isinf(factor.astype('float').values)]=np.nan
        for fc in factor.columns.tolist():
            # print(industry.shape,factor.loc[:,fc].shape)
            temp = pd.concat([industry,factor.loc[:,fc]],axis=1)
            temp.columns =['industry', 'value']
            temp = temp.astype('float')
            temp['value']=temp['value'].fillna(temp.groupby('industry')['value'].transform('mean'))
            factor.loc[:,fc] = temp['value']
        factor = factor.fillna(factor.mean())
        return factor
    
    def mad_remove_extreme(self,arr):## arr是一个一维向量，'mad'去极值方法，满足条件2
        arr1 = copy.deepcopy(arr)
        arr[np.isinf(arr1)]=np.nan
        md=np.nanmedian(arr)
        mdmd=np.nanmedian(abs(arr-md))
        
        upper=md+self.weight*mdmd
        lower=md-self.weight*mdmd
        
        if (((arr>upper)|(arr<lower)).sum()<=(~np.isnan(arr)).sum()*0.1):
            arr[arr>upper]=upper
            arr[arr<lower]=lower

        arr[np.isinf(arr1)*(arr1>0)]=np.nanmax(arr)
        arr[np.isinf(arr1)*(arr1<0)]=np.nanmin(arr)

        return arr
        
    def std_remove_extreme(self,arr):## arr是一个一维向量，'std'去极值方法，满足条件2
        arr1 = copy.deepcopy(arr)
        arr[np.isinf(arr1)]=np.nan
        mu=np.nanmean(arr)
        sigma=np.nanstd(arr,ddof=1)
        
        upper=mu+self.weight*sigma
        lower=mu-self.weight*sigma
        
        if (((arr>upper)|(arr<lower)).sum()<=(~np.isnan(arr)).sum()*0.1):
            arr[arr>upper]=upper
            arr[arr<lower]=lower

        arr[np.isinf(arr1)*(arr1>0)]=np.nanmax(arr)
        arr[np.isinf(arr1)*(arr1<0)]=np.nanmin(arr)

        return arr        
    
    def norm_dataframe(self):
        index_=self.factor.index
        columns_=self.factor.columns
        
        if self.extreme=='mad':
            factor_mat=np.apply_along_axis(self.mad_remove_extreme,abs(1-self.axis),self.factor.astype(np.float64).values)
        elif self.extreme=='std':
            factor_mat=np.apply_along_axis(self.std_remove_extreme,abs(1-self.axis),self.factor.astype(np.float64).values)        
        
        factor_m = pd.DataFrame(factor_mat, index=index_, columns=columns_)
        factor=self.get_valid(factor_m, self.industry)# 确保是深复制
        factor=factor.astype(np.float64).values
        
        if self.axis==1:## axis 选择功能，默认是对行做去极值，标准化，满足条件4
            factor=factor.T
        
        if self.standard:          
            mu=np.nanmean(factor,axis=1)
            # sigma=np.nanstd(factor,axis=1,ddof=1)
            sigma=np.nanstd(factor,axis=1,ddof=1)
            factor[sigma==0,:]=np.subtract(factor[sigma==0,:].T,mu[sigma==0]).T
            factor[sigma!=0,:]=np.divide(np.subtract(factor[sigma!=0,:].T,mu[sigma!=0]),sigma[sigma!=0]).T
            
        if self.axis==1:# 将最后的结果转置（与前面的axis）保持一致
            factor=factor.T
        return pd.DataFrame(factor,index=index_,columns=columns_)
    

def get_single_factor(f,factor_path,start_date,end_date):
    df = pd.read_pickle(factor_path+f+'.pkl').loc[start_date:end_date]
    return df.stack(dropna=False)
def get_factors(factor_path_dict,start_date,end_date):
    from sklearn.externals.joblib import Parallel,delayed
    final_factor = Parallel(n_jobs=num_threads)(delayed(get_single_factor)(f,factor_path,start_date,end_date) for f,factor_path in factor_path_dict.items())
    final_factor =dict(zip(factor_path_dict.keys(),final_factor))
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
def get_neu_sample(basic_path,factor_path_dict,start_date,end_date,shift_lag):
    factor_list = list(factor_path_dict.keys())
    tool_name = ['is_valid_raw','is_valid','industry_code_all']
    data = get_factors(factor_path_dict,start_date,end_date)
    for t in tool_name:
        tmp = pd.read_pickle(basic_path+t+'.pkl').shift(shift_lag).loc[start_date:end_date]
        data[t] = tmp.stack(dropna=False)
    neu_basic = get_mkt_indus(basic_path,start_date,end_date,shift_lag)
    data[neu_basic.columns] = neu_basic
    data = data[data['is_valid']==1].reset_index()
    data = data.rename(columns={'level_0':'date','level_1':'stock'})
    data[factor_list] = data.groupby(by=['date','industry_code_all'])[factor_list].transform(lambda x:x.fillna(x.mean()))
    
    data = data.set_index(['date','stock'])
    data.index = data.index.remove_unused_levels()
    data = neutralize(data[factor_list],data[neu_basic.columns],data_norm=factor_list,how_norm=['log_mkt'])
    data = apply_parallel(data.groupby(level=0),standard_winsor)
    data.index = data.index.remove_unused_levels()
    return data.fillna(0)
def get_neu_sample_groups(basic_data_path,factor_path_dict,start_date,end_date,shift_lag=0,g_num_1=10,label_rank=True):
    # prepare
    factor_list = list(factor_path_dict.keys())
    factor_list.sort()
    tool_name = ['is_valid_raw','is_valid','industry_code_all']
    data = get_factors(factor_path_dict,start_date,end_date)
    for t in tool_name:
        tmp = pd.read_pickle(basic_data_path+t+'.pkl').shift(shift_lag).loc[start_date:end_date]
        data[t] = tmp.stack(dropna=False)
    neu_basic = get_mkt_indus(basic_data_path,start_date,end_date,shift_lag)
    data[neu_basic.columns] = neu_basic
    data = data[data['is_valid']==1].reset_index()
    data = data.rename(columns={'level_0':'date','level_1':'stock'})

    # fillna
    data[factor_list] = data.groupby(by=['date','industry_code_all'])[factor_list].transform(lambda x:x.fillna(x.mean()))

    # divide size groups
    data_part = data[factor_list+['log_mkt','date','stock']].copy()
    data_part['log_mkt'] = round(data_part['log_mkt'],1)
    data_part['log_mkt_rank'] = data_part.groupby(by='date')['log_mkt'].rank(pct=True,method='average')
    data_part['log_mkt_group1'] = pd.cut(data_part['log_mkt_rank'],bins=np.linspace(0,1,g_num_1+1),labels=np.arange(1,g_num_1+1,1))
    data_part = data_part.set_index(['date','stock','log_mkt_group1'])
    data_part.index = data_part.index.remove_unused_levels()
    data_part = data_part[factor_list]

    # winsorize
    data_part = apply_parallel(data_part.groupby(level=[0,2]),winsorize)

    # zscore or rank in groups
    if label_rank is False:
        data_part = apply_parallel(data_part.groupby(level=[0,2]),standardlize)
    else:
        data_part = data_part.groupby(level=[0,2]).rank(pct=True,method='average')
    data_part = data_part.reset_index(level=[2],drop=True)
    
    # zscore  all
    data_part = apply_parallel(data_part.groupby(level=[0]),standard_winsor)    
    return data_part.fillna(0)        
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
# 将样本收益率标签转化为分组标签
def get_label_bin(data,return_type):
    bin_label = 'bin_'+return_type
    data[bin_label] = 0
    data = data.sort_values(by=return_type, ascending=False)
    n_stock_select = np.multiply([0.3,0.3], data.shape[0])
    n_stock_select = np.around(n_stock_select).astype(int)
    for i in range(3):
        pos_step = int(n_stock_select[1]/3.)
        data.iloc[int(i*pos_step):int((i+1)*pos_step),-1] = 3-i
    for i in range(3):
        neg_step = int(n_stock_select[0]/3.)
        data.iloc[(data.shape[0]-int((i+1)*pos_step)):(data.shape[0]-int(i*pos_step)),-1] = -1 * (3-i)
    
    data = data[data[bin_label].abs()>=0]
    return data
def get_future_return(basic_daily_path, trade_price, price_type='1300_1459', lag_list=[1, 3, 5], shift_lag=1,
                      winsard_flag=True, norm_flag=True,roll=True):
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
        label = price_type + '_re_' + str(lag) + 'd'
        ori_label_list.append(label)
        future_return_df[label] = re.stack(dropna=False)
    if roll:
        trade_vwap_adj = get_trade_price(basic_data_path, minute_data_path, label_start_date, label_end_date,
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
    if winsard_flag == True:
        future_return_df[all_label_list] = apply_parallel(future_return_df[all_label_list].groupby(level=0), winsorize)
    if norm_flag == True:
        future_return_df[all_label_list] = apply_parallel(future_return_df[all_label_list].groupby(level=0),
                                                          standardlize)
    return future_return_df.fillna(0)
    
def get_stock_date(start_date, end_date):
    is_valid = pd.read_pickle(basic_daily_path+'is_valid.pkl').loc[start_date:end_date]
    stock_list = is_valid.columns.tolist()
    date_list = [d.strftime('%Y%m%d') for d in is_valid.index]
    return stock_list, date_list    
    
def check_single_sample(path,date,factor_list,silent=True):
    df = pd.read_pickle(path+date+'.pkl')[factor_list]
    corr = df.corr()
    dup = corr[corr==1].sum(axis=1)
    duplist = dup[dup>1].index.tolist()
    zero_sample = df.abs().sum()
    zero_list = zero_sample[zero_sample==0].index.tolist()
    if not silent:
        if len(duplist)>0:
            print(date,duplist,' duplicated')
            lm.sendMessage(date+ " duplicated: {0}".format(str(duplist)))
        if len(zero_list)>0:
            print(date,zero_list,'not update success')
            lm.sendMessage(date+ " not update success: {0}".format(str(zero_list)))
        else:
            print(date,zero_list,'update success')
            lm.sendMessage(date+ " update success: {0}".format(str(zero_list)))
    return duplist,zero_list
def am_update_feature(factor_list,hfactor_list,start_date,end_date,check=True,silent=False):
    hpath_list = [hfactor_data_path]*len(hfactor_list)
    neu_sample = get_neu_sample(basic_data_path,dict(zip(hfactor_list,hpath_list)),start_date,end_date,1)
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
    if check:
        Parallel(num_threads)(delayed(check_single_sample)(hsample_norm_path,date.strftime('%Y%m%d'),factor_list+hfactor_list,silent) for date in date_list)
    return   
def pm_update_label(feature_list,start_date, end_date,winsard_flag=True, norm_flag=True,lag_list=[1,3,5]):
    label_start_date = get_trade_date(start_date, -6)[0].strftime('%Y%m%d')
    label_end_date = get_trade_date(end_date, 6)[-1].strftime('%Y%m%d')
    label_date_list = get_trade_date(label_start_date, end_date)
    date_list = get_trade_date(start_date, end_date)
    trade_price = get_trade_price(basic_data_path, minute_data_path, label_start_date, label_end_date,
                                  transaction_time='1300', transaction_period=120)
    label = get_future_return(basic_data_path, trade_price, price_type='1300_1459', lag_list=lag_list, shift_lag=1,
                            norm_flag=norm_flag)
    for date in label_date_list:
        print(date)
        date = date.strftime('%Y%m%d')
        tmp = label.loc[date].reset_index()
        for w in lag_list:
            tmp = get_label_bin(tmp, '1300_1459_re_'+str(w)+'d')
        tmp.rename(columns={'level_0': 'date', 'level_1': 'columns'}, inplace=True)
        tmp.rename(columns={'level_0':'date','level_1':'columns'},inplace=True)
        x_sample = pd.read_pickle(hsample_norm_path+date+'.pkl')[['stock']+feature_list]
        tmp = tmp.merge(x_sample,on=['stock'],how='left')
        tmp = tmp.fillna(0)
        pd.to_pickle(tmp.sort_index(by='stock').reset_index(drop=True),hsample_norm_path+date+'.pkl')
        
def pm_update_vwap_label(feature_list,start_date,end_date,winsard_flag=True, norm_flag=True, lag_list=[1, 3, 5]):
    
    label_start_date = get_trade_date(start_date, -7)[0].strftime('%Y%m%d')
    label_end_date = get_trade_date(end_date, 7)[-1].strftime('%Y%m%d')
    label_date_list = get_trade_date(label_start_date, end_date)
    date_list = get_trade_date(start_date, end_date)
    trade_price_vwap = get_trade_price(basic_data_path, minute_data_path, label_start_date, label_end_date,
                                       price_type='vwap')
    label_vwap = get_future_return(basic_data_path, trade_price_vwap, price_type='vwap', lag_list=lag_list,
                                   shift_lag=0,norm_flag=norm_flag)
    trade_price_0930_1129 = get_trade_price(basic_data_path, minute_data_path, label_start_date,
                                                          label_end_date, transaction_time='0930',
                                                          transaction_period=120)
    label_0930_1129 = get_future_return(basic_data_path, trade_price_0930_1129, price_type='0930_1129', lag_list=lag_list,
                                        shift_lag=0,norm_flag=norm_flag)
    label_vwap[label_0930_1129.columns] = label_0930_1129
    label = label_vwap.reset_index().rename(columns={'level_0': 'date', 'level_1': 'columns'})
    for date in label_date_list:
        print(date)
        tmp = label[label['date']==date]
        for w in lag_list:
            tmp = get_label_bin(tmp, 'vwap_re_'+str(w)+'d')
            tmp = get_label_bin(tmp, '0930_1129_re_'+str(w)+'d')
        print(len(tmp))
        date = date.strftime('%Y%m%d')
        x_sample = pd.read_pickle(sample_norm_path+date+'.pkl')[['stock']+feature_list]
        tmp = tmp.merge(x_sample,on=['stock'],how='left')
        tmp = tmp.fillna(0)
        pd.to_pickle(tmp.sort_index(by='stock').reset_index(drop=True),sample_norm_path+date+'.pkl')
        
def pm_update_vwap_sample(start_date,end_date,check=True,silent=False):
    factor_list = sorted([f[:-4] for f in os.listdir(factor_data_path) if f.endswith('.pkl')])
    fund_factor_list = [f[:-4] for f in os.listdir(fund_factor_data_path)  if f.endswith('.pkl')]
    path_list = [factor_data_path]*len(factor_list)+[fund_factor_data_path]*len(fund_factor_list)
    print(len(factor_list+fund_factor_list),len(path_list))
    factor_path_dict = dict(zip(factor_list+fund_factor_list,path_list))
    neu_sample = get_neu_sample(basic_data_path,factor_path_dict,start_date,end_date,0)
    print('daily fund factor finish')
    neu_sample = neu_sample.reindex(columns=sorted(neu_sample.columns))
    neu_sample = neu_sample.reset_index().rename(columns={'level_0':'date','level_1':'columns'})
    
    date_list = get_trade_date(start_date,end_date)
    for date in date_list:
        print(date)
        x_sample = neu_sample[neu_sample['date']==date].fillna(0)
        date = date.strftime('%Y%m%d')
        pd.to_pickle(x_sample,sample_norm_path+date+'.pkl')
    if check:
        Parallel(num_threads)(delayed(check_single_sample)(sample_norm_path,date.strftime('%Y%m%d'),factor_list+fund_factor_list,silent) for date in date_list)
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
    
    
def update_sample(start_date,end_date,mode,silent=False):
    #data_center_path
    factor_list = pd.read_pickle('/%s/Sample/factor_list.pkl' % data_center_path)
    hfactor_list = sorted([f[:-4] for f in os.listdir(hfactor_data_path) if f.endswith('.pkl')])
    all_hfactor_list = pd.read_pickle('/%s/HFSample/hfactor_list.pkl' % data_center_path)
    if mode==0:
        am_update_feature(factor_list,hfactor_list,start_date,end_date)
    elif mode==1:
#        pm_update_label(all_hfactor_list,start_date,end_date)
        pm_update_vwap_sample(start_date,end_date)
        pm_update_vwap_label(factor_list,start_date,end_date)