
# coding: utf-8

# In[1]:


import os
import numpy as np
import pandas as pd
from scipy.stats import norm
import matplotlib
matplotlib.use('Agg')
import sys
sys.path.insert(0,'/data/group/800020/AlphaTools/')
sys.path.insert(0,'/data/user/013546/DailyReport/')
from report_maker import *
from sklearn.externals.joblib import Parallel,delayed


# In[2]:


show_flag = True
first = False
run_path = '/data/user/013546/DailyReport/'
temp_check_path = run_path


# # 函数

# In[3]:


import os
import numpy as np
import pandas as pd
def get_trade_price(transaction_price='vwap', transaction_time='0930', transaction_period=120):
    basic_daily_path = '/data/group/800020/AlphaDataCenter/Basic/daily/'
    basic_minute_path = '/data/group/800020/AlphaDataCenter/Basic/minute/'
    adjfactor = pd.read_pickle(basic_daily_path + 'adjfactor.pkl').loc['20140101':]
    trade_price = pd.DataFrame(index=adjfactor.index, columns=adjfactor.columns)
    minute_close = pd.DataFrame(index=adjfactor.index, columns=adjfactor.columns)
    assert len(transaction_time) == 4
    assert transaction_time[:2] in ['09', '10', '11', '13', '14']
    assert int(transaction_time[2:]) >= 0 and int(transaction_time[2:]) < 60
    assert int(transaction_time) >= 930 and int(transaction_time) < 1130 or int(transaction_time) >= 1300 and int(
        transaction_time) < 1500
    assert transaction_period > 0 and isinstance(transaction_period, int) if transaction_price == 'vwap' else True
    os.mkdir(temp_check_path) if not os.path.exists(temp_check_path) else None
    time_saver = transaction_price + '_' + transaction_time + '_' + str(transaction_period)
    if os.path.exists(temp_check_path + time_saver + '.pkl'):
        trade_price_0 = pd.read_pickle(temp_check_path + time_saver + '.pkl').dropna(how='all', axis=0)
        minute_close_0 = pd.read_pickle(temp_check_path+ time_saver + '_minute_close.pkl')
        add_trade_price_dates = sorted(list(set(trade_price.index) - set(trade_price_0.index)))
        same_trade_price_dates = sorted(list(set(minute_close.index) & set(trade_price_0.index)))
        if len(same_trade_price_dates)>0:
            trade_price = trade_price_0.loc[same_trade_price_dates]
            minute_close = minute_close_0.loc[same_trade_price_dates]
    if not os.path.exists(temp_check_path + time_saver + '.pkl') or add_trade_price_dates:
        price = pd.DataFrame(index=adjfactor.index, columns=adjfactor.columns, data=np.nan)
        close = pd.DataFrame(index=adjfactor.index, columns=adjfactor.columns, data=np.nan)
        if not os.path.exists(temp_check_path + time_saver + '.pkl'):
            add_trade_price_dates = adjfactor.index
        elif len(same_trade_price_dates)>0:
            price.loc[same_trade_price_dates] = trade_price_0.loc[same_trade_price_dates]
            close.loc[same_trade_price_dates] = minute_close_0.loc[same_trade_price_dates]
        for date in [d.strftime('%Y%m%d') for d in add_trade_price_dates]:
            print(date)
            if transaction_time != '0930':
                close.loc[date] = pd.read_pickle(basic_minute_path + 'Close/' + date + '.pkl').loc[
                                         :pd.Timestamp(date + transaction_time + '00')].iloc[-2]
            if transaction_price in ['open', 'close']:
                price.loc[date] =                 pd.read_pickle(basic_minute_path + transaction_price.capitalize() + '/' + date + '.pkl').loc[
                    pd.Timestamp(date + transaction_time + '00')]
            else:
                minute_vol = pd.read_pickle(basic_minute_path + 'Volume/' + date + '.pkl').loc[
                             pd.Timestamp(date + transaction_time + '00'):].iloc[:transaction_period].sum()
                minute_amt = pd.read_pickle(basic_minute_path + 'Amount/' + date + '.pkl').loc[
                             pd.Timestamp(date + transaction_time + '00'):].iloc[:transaction_period].sum()
                price.loc[date] = minute_amt / minute_vol
            price[np.isinf(price)] = np.nan
            close[np.isinf(close)] = np.nan
        price.to_pickle(temp_check_path + time_saver + '.pkl')
        close.to_pickle(temp_check_path + time_saver + '_minute_close.pkl')


def check_prediction(activation, transaction_price='close', transaction_time='0930', transaction_period=1,
                     rebalance_step=1, group_number=20, mode=1):
    act = activation.copy().astype(np.float64)
    act = act.shift(rebalance_step).iloc[rebalance_step:]
    if transaction_time == '0930':
        act = act.shift(1).iloc[1:]

    close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl')

    basic_daily_path = '/data/group/800020/AlphaDataCenter/Basic/daily/'
    basic_minute_path = '/data/group/800020/AlphaDataCenter/Basic/minute/'
    adjfactor = pd.read_pickle(basic_daily_path + 'adjfactor.pkl').loc['20140101':]
    date_list = []

    assert len(
        set(act.index).difference(adjfactor.iloc[1:].index)) == 0, "please enter prediction dates between %s and %s" % (
    adjfactor.index[1], adjfactor.index[-1])
    date_list = sorted([d.strftime(format='%Y%m%d') for d in adjfactor.iloc[adjfactor.index.tolist().index(
        act.index[0]) - rebalance_step:adjfactor.index.tolist().index(act.index[-1]) + 1].index])
    time_saver = transaction_price + '_' + transaction_time + '_' + str(transaction_period)
    trade_price = pd.read_pickle(temp_check_path + time_saver + '.pkl').loc[date_list[0]:date_list[-1]]
    minute_close = pd.read_pickle(temp_check_path + time_saver + '_minute_close.pkl').loc[date_list[0]:date_list[-1]]

    vwap = trade_price.copy()  # pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/vwap.pkl')
    ZZ500 = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/ZZ500_data.pkl')
    close_500 = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close_000905SH.pkl')
    # 权重用价格去调整得到当时价格的权重
    ZZ500_ = ZZ500 / close.loc[ZZ500.index[0]:] * vwap.loc[ZZ500.index[0]:]
    close_500_vwap = ((close_500.loc[ZZ500.index[0]:].T) * (ZZ500_.sum(axis=1) / ZZ500.sum(axis=1))).T
    ret_500 = (close_500_vwap.pct_change(1)) * 100

    pre_close = pd.read_pickle(basic_daily_path + 'pre_close.pkl').loc[trade_price.index]
    maxupordown = (minute_close / pre_close - 1).abs() >= 0.098
    is_valid = ((~maxupordown) & (pd.read_pickle(basic_daily_path + 'isvalid_and_not_open_updown_limit.pkl').loc[
                                      trade_price.index] == 1)).shift(rebalance_step) == True
    if transaction_time == '0930':
        is_valid = (pd.read_pickle(basic_daily_path + 'is_valid_raw.pkl').shift(rebalance_step).loc[
                        trade_price.index] == 1) & (
                               pd.read_pickle(basic_daily_path + 'is_valid.pkl').shift(rebalance_step + 1).loc[
                                   trade_price.index] == 1)

    is_valid_raw = pd.read_pickle(basic_daily_path + 'is_valid_raw.pkl').loc[trade_price.index] == 1
    valid = (is_valid & is_valid_raw).loc[act.index]
    # ret = ((((trade_price * adjfactor.loc[trade_price.index]) / (trade_price * adjfactor.loc[trade_price.index]).shift(rebalance_step)) - 1) * 100).loc[act.index].astype(np.float64) / rebalance_step
    ret = ((((trade_price * adjfactor.loc[trade_price.index]) / (trade_price * adjfactor.loc[trade_price.index]).shift(
        1)) - 1) * 100).loc[act.index].astype(np.float64)
    null_date = ret[pd.notnull(ret).sum(axis=1) == 0].index.tolist()

    missing_date = act.loc[(np.isnan(act) & valid).sum(axis=1) > 0].drop(null_date, errors='ignore').index.tolist()
    if len(missing_date) > 0:
        warning = pd.DataFrame(index=['activation', 'valid'],
                               data=[(pd.notnull(act) & valid).sum(axis=1), valid.sum(axis=1)]).T.loc[missing_date]
        warning.columns.name = 'valid number'
        # print('Warning: number of valid activations is less than number of valid stocks, filling missing activations with median values of corresponding dates')
        # print(warning)
        act[np.isnan(act) & valid] = act.fillna(0.).add(act.median(axis=1), axis=0)

    valid = valid & (ret.abs() <= (20 + 10 * rebalance_step)) & (~np.isinf(ret)) & (~np.isnan(ret))
    act_bnd = (pd.notnull(act[valid]).sum(axis=1) / group_number).astype(int).drop(null_date, errors='ignore') + 1
    act_rank = act[valid].rank(axis=1, pct=False, method='first', ascending=False).drop(null_date, errors='ignore')
    if mode == 1:
        benckmark_ret = ret[valid].mean(axis=1)
    else:
        benckmark_ret = ret_500.loc[act.index[0]:act.index[-1]]['close_000905SH']
    ret_sub_bench = ret[valid].subtract(benckmark_ret, axis=0).drop(null_date,errors='ignore')
    score = pd.DataFrame(index=act.index, columns=np.arange(1, group_number + 1), data=np.nan).drop(null_date,
                                                                                                    errors='ignore')
    score_sub_bench = pd.DataFrame(index=act.index, columns=np.arange(1, group_number + 1), data=np.nan).drop(null_date,
                                                                                                    errors='ignore')
    for i in range(group_number):
        score[i + 1] = ret[act_rank.gt(i * act_bnd, axis=0) & act_rank.le((i + 1) * act_bnd, axis=0)].mean(axis=1)
        score_sub_bench[i + 1] = ret_sub_bench[act_rank.gt(i * act_bnd, axis=0) & act_rank.le((i + 1) * act_bnd, axis=0)].mean(axis=1)
    score.dropna(inplace=True)
    score_sub_bench.dropna(inplace=True)
    return score,score_sub_bench,ret

def check_prediction_new(activation, transaction_price='close', transaction_time='0930', transaction_period=1,
                         rebalance_step=1,
                         group_number=20, mode=1, num_threads=4):
    get_trade_price(transaction_price,transaction_time,transaction_period)
    n = 7 if transaction_period == 240 else 3
    from sklearn.externals.joblib import Parallel, delayed
    w = [0.5, 0.25, 0.15, 0.1]
    res = Parallel(num_threads)(
        delayed(check_prediction)(activation, transaction_price=transaction_price, transaction_time=transaction_time,
                                  transaction_period=transaction_period,
                                  rebalance_step=i, group_number=group_number, mode=mode) for i in range(1, n + 1))
    score = dict(zip(np.arange(1, n + 1), [r[0] for r in res]))
    score_sub_bench =  dict(zip(np.arange(1, n + 1), [r[1] for r in res]))
    score = pd.DataFrame({k: (v.iloc[:, :4] * w).sum(axis=1) for k, v in score.items()})
    score_sub_bench = pd.DataFrame({k: (v.iloc[:, :4] * w).sum(axis=1) for k, v in score_sub_bench.items()})
    ret = dict(zip(np.arange(1, n + 1), [r[2] for r in res]))
    return score,score_sub_bench,ret[1]
def map_act(df):
    from scipy.stats import norm
    df = df.round(10)
    df = df.rank(pct=True,axis=1)
    df[pd.DataFrame(index=df.index,columns=df.columns,data=(df.values==1))] = 1 -1/3676
    df[pd.DataFrame(index=df.index,columns=df.columns,data=(df.values==0))] = 1/3676
    df_norm = pd.DataFrame(norm.ppf(df.values),index=df.index,columns=df.columns)
    return df_norm
def norm_ppf(factor_dict):
    com = None
    for f in factor_dict:
        stock_list = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/is_valid.pkl').columns
        df = map_act(factor_dict[f].reindex(columns=stock_list))
        if com is None:
            com = df
        else:
            com += df
    return com/len(factor_dict)
def get_act(path,start_date,end_date):
    activation = {}
    date_list = sorted([d[:-4] for d in os.listdir(path)])
    for d in date_list:
        if (d<start_date)|(d>end_date):
            continue
        if os.path.exists(path + d + '.csv'):
            x = pd.read_csv(path + d + '.csv', index_col=0, header=None).iloc[:,0]
            activation[d] = x.astype(np.float64)
    activation = pd.DataFrame(activation).T
    activation.index = pd.to_datetime(activation.index)
    return activation
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
def draw_custom_style(df,save_path,k,in_out_sample_split_date,split=True,name=''):
    plt.figure(figsize=(18,6))
    colors_map_in={'All':'r','DeepFM':'lightgreen','LinearRegression':'lightblue','XgboostRegression':'yellow','CatboostMultiClass':'grey'}
    colors_map_out={'All':'darkred','DeepFM':'darkgreen','LinearRegression':'blue','XgboostRegression':'y','CatboostMultiClass':'k'}
    if split==True:
        plt.plot(df.loc[:in_out_sample_split_date])
    plt.plot(df.loc[in_out_sample_split_date:])
    plt.legend(df.columns)
    plt.title(name)
    plt.savefig(save_path  + name+'.png')
    if show_flag:
        plt.show()
def cal_performance(net):
    '''
        net = (stats.loc[(slice(None),'1300'),:]['daily_exc'].reset_index().set_index('level_0')['daily_exc'])/100+1
        net = net.cumprod()
        df = cal_performance(net)
    '''
    period = 252
    ret = np.append(1, net.values)
    Total_return = ret[-1] 
    Annualized_Return = np.power(Total_return, period/(len(ret)-1)) - 1
    ##### 
    net_chg = ret[1:]/ret[:-1] - 1

    Annualized_Volatility = np.std(net_chg)*np.sqrt(period)
    Sharp = Annualized_Return/Annualized_Volatility

    drawndown = []
    for i in range(0, len(ret)):
        l = []
        for j in range(i, len(ret)):
            l.append((ret[j]-ret[i])/ret[i])
        drawndown.append(np.nanmin(l))
    drawndown.append(0)
    Maxdrawndown = abs(np.min(drawndown))

    #####    总净值，年化收益，年化波动率，夏普率，最大回撤
    df = pd.Series(index = ['Total_Net_Value','Annualized_Return','Annualized_Volatility','Sharp','Maxdrawndown'])
    df.iloc[:] = [Total_return, Annualized_Return, Annualized_Volatility, Sharp, Maxdrawndown]
    df = pd.DataFrame(df.values, columns=['Summary'],index = df.to_frame().index)
    return df
def get_stats_in_out(cum_exc_ret,split_in_out_sample_date=None,save_path='',name='High_freq_model'):
    if len(cum_exc_ret)>20:
        cum_exc_ret.index = pd.to_datetime(cum_exc_ret.index)
    plt.figure(figsize=(10,5))
    if split_in_out_sample_date is None:
        plt.plot(cum_exc_ret)
    else:
        plt.plot(cum_exc_ret.loc[:split_in_out_sample_date])
        plt.plot(cum_exc_ret.loc[split_in_out_sample_date:])
    plt.xlabel('date')
    plt.ylabel('cum excess ret(%)')
    if isinstance(cum_exc_ret,pd.DataFrame):
        plt.legend(cum_exc_ret.columns)
    plt.grid()
    plt.title(name)
    plt.savefig(save_path+name+'.png')
    if show_flag:
        plt.show()
def get_pct(score,ret):
    ret[score.columns] = score
    ret['full_market_mean'] = ret.mean(axis=1)
    ret_rank = ret.rank(axis=1,pct=True)
    ret_rank['portfolio'] = ret_rank.iloc[:,(-len(score.columns)-1):-1].mean(axis=1)
    return ret_rank


# In[4]:


close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl')
today = close.index[-1].strftime('%Y%m%d')
stocks = close.columns
model_name_map = {
    'am':['XgboostRegression_0930_1129_re_5d','LinearRegression_0930_1129_re_5d','DeepFM_0930_1129_re_5d','All'],
 'pm':['XgboostReg_Model_V1_1300_1459_re_5d','LinearRegression_1300_1459_re_5d','DeepFM_1300_1459_re_5d','All'],
 'vwap':['XgboostRegression_vwap_re_5d','DeepFM_vwap_re_5d','LinearRegression_vwap_re_5d','All']}
model_dict={'CatboostMultiClass_Model_R5d_bin_0930_1129_re_5d':'Catboost',
            'MLP_Model_0930_1129_re_1d':'MLP',
            'XgboostRegression_0930_1129_re_1d':'Xgboost',
            'XgboostRegression_0930_1129_re_5d':'Xgboost',
            'XgbRegTSFourModel_0930_1129_re_5d':'Xgboost',
            'DeepFM_0930_1129_re_1d':'DeepFM',
            'DeepFM_0930_1129_re_5d':'DeepFM',
            'LinearRegression_0930_1129_re_5d':'LinearRegression',
            'LinearRegression_industry_0930_1129_re_5d':'LinearRegression',
            'CatboostMultiClass_Model_R5d_bin_1300_1459_re_5d':'Catboost',
             'MLP_Model_1300_1459_re_1d':'MLP',
            'XgboostRegression_1300_1459_re_1d':'Xgboost',
            'XgbRegTSFourModel_1300_1459_re_5d':'Xgboost',
            'XgboostReg_Model_V1_1300_1459_re_1d':'Xgboost',
            'XgboostReg_Model_V1_1300_1459_re_5d':'Xgboost',
            'DeepFM_1300_1459_re_1d':'DeepFM',
            'DeepFM_1300_1459_re_5d':'DeepFM',
            'LinearRegression_1300_1459_re_5d':'LinearRegression',
            'CatboostMultiClass_Model_R5d_bin_vwap_re_1d':'Catboost',
             'MLP_Model_vwap_re_1d':'MLP',
            'XgboostRegression_vwap_re_1d':'Xgboost',
            'XgboostRegression_vwap_re_5d':'Xgboost',
            'XgbRegTSFourModel_vwap_re_5d':'Xgboost',
            'DeepFM_vwap_re_1d':'DeepFM',
            'DeepFM_vwap_re_5d':'DeepFM',
            'LinearRegression_vwap_re_5d':'LinearRegression',
            'All_0930':'All',
            'All_vwap':'All',
            'All_1300':'All'
           }
model_list = sorted(list(set(model_dict.values())))
model_list = sorted([m for m in model_list if not m in ['MLP','Catboost']])
print(model_list)
act_path = '/data/group/800020/AlphaDataCenter/Department/DailyPrediction/'
pkl_path = '/data/user/013546/AlphaDataCenter/Department/DailyPrediction/pickles/'
excess_path = '/data/user/013546/AlphaDataCenter/Department/performance/excess/'
save_path = '/data/user/013546/AlphaDataCenter/Department/png/20200804/'
act_params = {
    'vwap':(act_path+'vwap/','0930',240),
    'am':(act_path+'am/', '0930', 120),
    'pm':(act_path+'pm/', '1300', 120)
}
start_date = '20190101'
in_out_sample_date = '20200101'
track_date = '20200601'
excess_list = {'am':('0930',120),'pm':('1300',120),'vwap':('0930',240)}
need_model = sorted(['DeepFM', 'Xgboost', 'LinearRegression', 'All'])
split = True


# In[5]:


act = {}
for k, v in act_params.items():
    print(k)
    if not os.path.exists(v[0]):
        continue
    models = os.listdir(v[0])
    models = [m for m in models if (m in model_name_map[k])&(m!='All')]
    print(models)
    act[k] = {}
    for m in models:
        df = get_act(act_path+k+'/'+m+'/',start_date,today).reindex(columns=stocks).astype(np.float64)
        df = save_data(df,pkl_path+k+'/'+m+'.pkl').loc[start_date:]
        if not df.index.equals(close.loc[df.index[0]:df.index[-1]].index): 
            print(m+' predict date_list is unconsistent!')
        act[k][m] = df
    df = save_data(norm_ppf(act[k]),pkl_path+k+'/All_5d.pkl').loc[start_date:]
    if not df.index.equals(close.loc[df.index[0]:df.index[-1]].index):
        print('All_5d predict date_list is unconsistent!')
    if k!='vwap':
        act[k]['All_'+v[1]] = df
    else:
        act[k]['All_'+k] = df


# In[6]:


excess = {}
quantile_median = {}
quantile_mean = {}
ave_return ={}
excess_bench500={}
if not os.path.exists(excess_path):
    os.makedirs(excess_path)
for k in act:
    excess_path_t = excess_path+k+'/'
    if not os.path.exists(excess_path_t):
        os.makedirs(excess_path_t)
    models = list(act[k].keys())
    for m in act[k]:
        act[k][m].index = pd.to_datetime(act[k][m].index)
        if act[k][m].index[-1]!=pd.to_datetime(today):
            act[k][m] = act[k][m].append(close.loc[today:])
        act[k][m].index = pd.to_datetime(act[k][m].index)
        score_m,score_sub_bench_m,ret_m= check_prediction_new(act[k][m], transaction_price='vwap', 
                                                       transaction_time=excess_list[k][0], transaction_period=excess_list[k][1], 
                                                             num_threads=10)
        if 'All' in m:
            _,score_bench500,_= check_prediction_new(act[k][m], transaction_price='vwap', 
                                                       transaction_time=excess_list[k][0], transaction_period=excess_list[k][1], 
                                                             num_threads=10,mode=0)
            score_bench500 = save_data(score_bench500,excess_path_t+m+'_bench500.pkl').loc[start_date:]
            excess_bench500[m] = score_bench500.mean(axis=1)
        ret_rank = get_pct(score_m,ret_m)
        quantile_mean[m] = ret_rank['portfolio']-ret_rank['full_market_mean']
        quantile_median[m] = ret_rank['portfolio']- 0.5
        tmp_excess = score_sub_bench_m
        print(k,m,tmp_excess.mean())
        save_data(score_m,excess_path_t+m+'_score_m.pkl')
        save_data(ret_m,excess_path_t+m+'_ret_am.pkl')
        tmp_excess = save_data(tmp_excess,excess_path_t+m+'.pkl').loc[start_date:]
        excess[m] = tmp_excess.mean(axis=1)
        ave_return[m] = excess[m].loc[in_out_sample_date:].mean()
excess = pd.DataFrame(excess)
excess_bench500 = pd.DataFrame(excess_bench500)
quantile_mean = pd.DataFrame(quantile_mean)
quantile_median = pd.DataFrame(quantile_median)
ave_return = pd.Series(ave_return).to_frame('ave_return').T


# In[7]:


track_return = {'sharp':{},'mean':{},'today_return':{}}
for m in excess:
    track_return['sharp'][m] = excess[m].loc[track_date:].mean()/excess[m].loc[track_date:].std()
    track_return['mean'][m] = excess[m].loc[track_date:].mean()
    track_return['today_return'][m] = excess[m].loc[today]
track_return = pd.DataFrame({k:pd.Series(v) for k,v in track_return.items()}).T


# In[8]:


excess_hf_model_dict={}
excess_vwap_model_dict={}
quantile_hf_model_dict={}
quantile_vwap_model_dict={}
for m in model_list:
    excess_hf_model_dict[m] = {}
    excess_vwap_model_dict[m] = {}
    quantile_hf_model_dict[m] = {}
    quantile_vwap_model_dict[m] = {}


# In[9]:


excess_map={'am':'0930','pm':'1300','vwap':'vwap'}
for k,v in excess_map.items():
    this_col = [c for c in excess.columns if v in c]
    excess_t =excess[this_col]
    excess_t = excess_t.rename(columns={c:model_dict[c] for c in excess_t.columns})
    quantile_mean_t =quantile_mean[this_col]
    quantile_mean_t = quantile_mean_t.rename(columns={c:model_dict[c] for c in quantile_mean_t.columns})
    quantile_median_t =quantile_median[this_col]
    quantile_median_t = quantile_median_t.rename(columns={c:model_dict[c] for c in quantile_median_t.columns})
    ave_return_t = ave_return[this_col]
    ave_return_t = ave_return_t.rename(columns={c:model_dict[c] for c in ave_return_t.columns})
    track_return_t = track_return[this_col]
    track_return_t = track_return_t.rename(columns={c:model_dict[c] for c in track_return_t.columns})
    draw_custom_style(excess_t[need_model].loc[in_out_sample_date:].cumsum().copy(),save_path,k,in_out_sample_date,split=False,
                      name=k+'_model_predict')
    for model_name in excess_t.columns:
        if k in ['am','pm']:
            excess_hf_model_dict[model_name][k] = excess_t[model_name]
            quantile_hf_model_dict[model_name][k+'_sub_mean'] = quantile_mean_t[model_name]
            quantile_hf_model_dict[model_name][k+'_sub_median'] = quantile_median_t[model_name]
        else:
            excess_vwap_model_dict[model_name][k] = excess_t[model_name]
            quantile_vwap_model_dict[model_name][k+'_sub_mean'] = quantile_mean_t[model_name]
            quantile_vwap_model_dict[model_name][k+'_sub_median'] = quantile_median_t[model_name]
    df = pd.DataFrame(index=ave_return_t.index, columns=['performance'], data=ave_return_t.index)
    tmp = ave_return_t[need_model].round(6)
    df = pd.concat([df, tmp], axis=1)
    df = df.dropna(axis=1)
    render_mpl_table(df, header_columns=0, col_width=2.5, row_height=0.6, font_size=10, save_path=save_path +k+'_score_table'+'.png')
    df = pd.DataFrame(index=track_return_t.index, columns=['performance'], data=track_return_t.index)
    tmp = track_return_t[need_model].round(6)
    df = pd.concat([df, tmp], axis=1)
    df = df.dropna(axis=1)
    render_mpl_table(df, header_columns=0, col_width=2.5, row_height=0.6, font_size=10, save_path=save_path +k+'_track_table'+'.png')
    None if os.path.exists(save_path + 'report/') else os.mkdir(save_path + 'report/')


# In[10]:


excess_hf_model_dict = {k:pd.DataFrame(v) for k,v in excess_hf_model_dict.items()}
excess_vwap_model_dict = {k:pd.DataFrame(v) for k,v in excess_vwap_model_dict.items()}
for k in excess_hf_model_dict:
    print(k)
    draw_custom_style(excess_hf_model_dict[k].cumsum(),save_path,k,in_out_sample_date,split=split,name='hf_'+k+'_in_out_sample')
for k in excess_vwap_model_dict:
    draw_custom_style(excess_vwap_model_dict[k].cumsum(),save_path,k,in_out_sample_date,split=split,name='vwap_'+k+'_in_out_sample')
if show_flag:
    plt.show()


# In[11]:


quantile_hf_model_dict = {k:pd.DataFrame(v) for k,v in quantile_hf_model_dict.items()}
quantile_vwap_model_dict = {k:pd.DataFrame(v) for k,v in quantile_vwap_model_dict.items()}
for k in quantile_hf_model_dict:
    draw_custom_style(quantile_hf_model_dict[k].cumsum(),save_path,k,in_out_sample_date,split=split,name='hf_quantile_'+k+'_in_out_sample')
for k in quantile_vwap_model_dict:
    draw_custom_style(quantile_vwap_model_dict[k].cumsum(),save_path,k,in_out_sample_date,split=split,name='vwap_quantile_'+k+'_in_out_sample')
if show_flag:
    plt.show()


# In[12]:


draw_custom_style(excess_bench500[['All_0930','All_1300']].fillna(0).loc[in_out_sample_date:].cumsum(),save_path,k,in_out_sample_date,split=False,name='hf_excess_bench500')
draw_custom_style(excess_bench500[['All_vwap']].fillna(0).loc[in_out_sample_date:].cumsum(),save_path,k,in_out_sample_date,split=False,name='vwap_excess_bench500')


# In[13]:


#过优化器回测,am由于预测值是前一天给的，传入优化器应shift（1），pm预测值是当天给的，传入优化器无需shift（1）
# 如果测试vwap：需要shift（1）


# In[14]:


from sklearn.externals.joblib import Parallel,delayed
import sys
sys.path.insert(0,'/data/group/800020/AlphaTools/')
from BacktestHF import BacktestHF 
from optimize_hf_industry import optimize_hf
from xquant.xqutils.helper import link
lm = link.LinkMessage()


# In[15]:


pkl_path = '/data/user/013546/AlphaDataCenter/Department/DailyPrediction/pickles/'
am = pd.read_pickle(pkl_path+'am/All_5d.pkl')
pm = pd.read_pickle(pkl_path+'pm/All_5d.pkl')
vwap = pd.read_pickle(pkl_path+'vwap/All_5d.pkl')
pm_0814 = get_act('/data/group/800020/AlphaDataCenter/Department/DailyPrediction/pm/All_500/','20200814','20200814').reindex(columns=stocks)
pm = save_data(pm_0814,pkl_path+'pm/All_5d.pkl')
if am.index[-1]!=pd.to_datetime(today):
    am = am.append(close.loc[today:today])
if vwap.index[-1]!=pd.to_datetime(today):
    vwap = vwap.append(close.loc[today:today])
first = False
test_start_date = today
test_end_date = today
last_date = close.index[-2].strftime('%Y%m%d')
print('last_date',last_date)
print('today',today)
hf_model={}
hf_model['0930'] = map_act(am).shift(1).iloc[1:]
hf_model['1300'] = map_act(pm).loc[start_date:]
vwap_model={}
vwap_model['0930'] = map_act(vwap).shift(1).iloc[1:]


# # 策略参数配置

# In[16]:


config_dict = {}
config_dict['5160304'] = {
    'day':True,
    'optimize_conf':
    {
        'capital':float('4e8'),'hedge_index':'HS300','industry_loose':0.01,'amt_limit':0.025,'dupl_industry':[6133,6134],
        'split_fin':False,'pool_valid_stocks':None,'single_stock_max_weight':0.005,
        'barra_limit_dict':
        {
            'Beta300':               (0.05, 0.05), 
            'Momentum':              (0.05, 0.05), 
            'Size':                  (1000, 1000), 
            'Volatility':            (1000, 1000), 
            'EarningsYield':         (1000, 1000), 
            'Liquidity':             (1000, 1000), 
            'Leverage':              (1000, 1000), 
            'Value':                 (1000, 1000), 
            'Growth':                (1000, 1000)
        }
   },
    'w_path_dict' : 
    {
        '5d_control_size,turnover10%':(0.2,0.5,True),
        '5d_control_size,turnover20%':(0.05,0.5,False)
    },
    'save_perform_path':'/data/user/013546/AlphaDataCenter/Department/png/benchmark_300/',
    'backtest_date':['20200101','20190101'],
    'bt_conf':
    {
        'start_time':'0930',
        'end_time':'0930',
       'transaction_period':240
    },
    'shipan_conf':{
        'open_date':'20200804','next_open_date':'20200805','start_time':'0930'
    },
    'sim_w':{'0930':('sim_w_5160304','simulation_w_vwap')}
}
config_dict['5160503'] = {
    'day':True,
    'optimize_conf':
    {
        'capital':float('8e8'),'hedge_index':'ZZ500','industry_loose':0.05,'amt_limit':0.025,'dupl_industry':None,
        'split_fin':False,'pool_valid_stocks':None,'single_stock_max_weight':0.0025,
        'barra_limit_dict':{
                'Beta500':               (0.01, 0.01), 
                'Momentum':              (0.01, 0.01), 
                'Size':                  (1000, 1000), 
                'Volatility':            (1000, 1000), 
                'EarningsYield':         (1000, 1000), 
                'Liquidity':             (1000, 1000), 
                'Leverage':              (1000, 1000), 
                'Value':                 (1000, 1000), 
                'Growth':                (1000, 1000)
        }
    },
   'w_path_dict' : {
                    '5d_no_control_size,turnover10%':(0.4,1000,True),
                    '5d_control_size,turnover10%':(0.4,0.01,False),
                   '5d_no_control_size,turnover20%':(0.2,1000,False),
                   '5d_control_size,turnover20%':(0.2,0.01,False)
                   },
   'save_perform_path':'/data/user/013546/AlphaDataCenter/Department/png/benchmark_500/',
   'backtest_date':['20200101','20190101'],
    'bt_conf':
    {
        'start_time':'0930',
        'end_time':'0930',
        'transaction_period':240
    },
    'shipan_conf':{
        'open_date':'20200804','next_open_date':'20200805','start_time':'0930'
    },
    'sim_w':{'0930':('sim_w_5160503','simulation_w_vwap')}
}
config_dict['5160803'] = {
    'day':False,
    'optimize_conf':
    {
        'capital':float('8e8'),'hedge_index':'ZZ500','industry_loose':0.05,'amt_limit':0.025,'dupl_industry':None,
        'split_fin':False,'pool_valid_stocks':None,'single_stock_max_weight':0.0025,
        'barra_limit_dict':{
                'Beta500':               (0.01, 0.01), 
                'Momentum':              (0.01, 0.01), 
                'Size':                  (1000, 1000), 
                'Volatility':            (1000, 1000), 
                'EarningsYield':         (1000, 1000), 
                'Liquidity':             (1000, 1000), 
                'Leverage':              (1000, 1000), 
                'Value':                 (1000, 1000), 
                'Growth':                (1000, 1000)
        }
    },
    'w_path_dict': 
    {
        '5d_no_control_size,turnover20%':(0.4,1000,True),
        '5d_control_size,turnover20%':(0.4,0.01,False),
        '5d_no_control_size,turnover40%':(0.2,1000,False),
        '5d_control_size,turnover40%':(0.2,0.01,False)
    },
    'save_perform_path':'/data/user/013546/AlphaDataCenter/Department/png/benchmark_500/',
    'backtest_date':['20200101','20190101'],
    'bt_conf':
    {
       'start_time':'0930',
       'end_time':'1300',
       'transaction_period':120
    },
    'shipan_conf': {
      'open_date':'20200811','next_open_date':'20200812','start_time':'1300'
    },
     'sim_w':{'0930':('sim_w_am_5160803','simulation_w_am'),'1300':('sim_w_pm_5160803','simulation_w_pm')}
}
sim_w_path = '/data/user/013546/DailyReport/performance/shipan/shipan_sim_w/'
shipan_stats_path = '/data/user/013546/DailyReport/performance/shipan/shipan_stats/'
sim_shipan_stats_path = '/data/user/013546/DailyReport/performance/shipan/depart_shipan_stats/'
shipan_pf_code =['5160304','5160503','5160803']
o32_path = '/data/user/011477/order/O32/afternoon/'
sim_shipan_w_path = '/data/group/800020/AlphaDataCenter/Department/DailyWeight/'


# In[17]:


backtest = {}
def get_open_position_w(o32_path,open_o32_date,pf_code):
    
    x = pd.read_excel(o32_path + '综合信息查询_组合证券_' + open_o32_date + '.xls', converters={'组合名称':str, '证券代码':str})
    x = x[(x['组合名称']==pf_code) & (x['证券类别']=='股票')]
    x.index = [i + '.SH' if i[0]=='6' else i + '.SZ' for i in x['证券代码']]
    x['持仓'] = (x['持仓'] / 100).round(0).astype(int) * 100
    if pf_code=='5160503':
        price = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/pre_close.pkl').loc[open_o32_date]
    else:
        price = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/minute/Close/'+open_o32_date+'.pkl').iloc[119]
    x_amt = (x['持仓']*price.loc[x['持仓'].index])
    x_amt = x['市值']
    open_position_weight = x_amt/x_amt.sum()
    open_position_weight = open_position_weight.reindex(price.index)
    open_position_weight = open_position_weight.fillna(0)
    capital = x_amt.sum()
#     capital = capital*1.001
    return capital,open_position_weight
def update_weight_bt_stats(k,v,pf_code,conf,weight_flag=True):
    op_conf = conf['optimize_conf']
    bt_conf = conf['bt_conf']
    shi_conf = conf['shipan_conf']
    if conf['day']:
        turn_ad={'0930':v[0]}
    else:
        turn_ad={'0930':v[0],'1300':v[0]}
    op_conf['barra_limit_dict'].update({'Size':(v[1],v[1])})
    path = conf['save_perform_path']+pf_code+'_'+k+'_capital'+str(op_conf['capital'])+'_amt'+str(op_conf['amt_limit'])+'_turn'+str(v[0])
    w_path = path+'_w.pkl'
    stats_path = path+'_stats.pkl'
    if first:
        last_weight_hf = None
    else:
        last_weight_hf = pd.read_pickle(w_path)[bt_conf['end_time']].loc[last_date]
        last_weight_hf.loc[['601688.SH','600919.SH']] = 0
    if weight_flag:
        print(k+' optimize')
        if bt_conf['end_time']=='1300':
            act = hf_model
        else:
            act = vwap_model
        print(last_weight_hf.loc[['601688.SH','600919.SH']])
        w_today = optimize_hf({k:v.loc[test_start_date:test_end_date] for k,v in act.items()},turn_ad, 
                              prev_weights=last_weight_hf,**op_conf)
        
        if test_start_date=='20200831':
            for kt,vt in w_today.items():
                vt.loc[test_start_date,'600291.SH'] = 0
                w_today[kt] = vt
        save_data(w_today,w_path) 
    w = pd.read_pickle(w_path)
    for kk,vv in w.items():
        vv[['000043.SZ','300216.SZ']] = 0
        w[kk] = vv
    bt_stats={}
    for open_date in config['backtest_date']:
        btf = BacktestHF({k:v.loc[open_date:open_date[:4]+'1231'] for k,v in w.items()}, 
                         benchmark=op_conf['hedge_index'], capital=op_conf['capital'], commission=0.0005,**bt_conf)
        btf.run()
        stats = btf.get_stats()
        stats = save_data(stats,stats_path).loc[open_date:]
        if v[2]:
            save_data(stats,sim_shipan_stats_path+'shipan_'+pf_code+'_stats.pkl')
        transac_time = sorted(stats.index.get_level_values(level=1).unique().tolist())
        net = (stats.loc[(slice(None),bt_conf['end_time']),:]['daily_exc'].reset_index().set_index('level_0')['daily_exc'])/100+1
        net = net.cumprod()
        df = cal_performance(net)
        for tt in transac_time:
            df.loc[tt+'_Turnover'] = stats.loc[(slice(None), tt), :]['turnover'].iloc[1:].mean() / 100
        df.loc['Today_Excess'] = stats.loc[(slice(None),bt_conf['end_time']),:]['daily_exc'].iloc[-1]*0.01
        bt_stats[open_date] = (net,df)
    
    shipan_stats = None
    if v[2]:
        if pf_code in shipan_pf_code:
            for kk,vv in w.items():
                save_data(vv.loc[today:today],sim_w_path+conf['sim_w'][kk][0]+'.pkl')
                save_data(vv.loc[today:today],sim_shipan_w_path+'benchmark_'+op_conf['hedge_index'][-3:]+'/'+conf['sim_w'][kk][1]+'.pkl')
                real_w = pd.read_pickle(sim_shipan_w_path+'benchmark_'+op_conf['hedge_index'][-3:]+'/'+'real_'+conf['sim_w'][kk][1].split('simulation_')[1]+'.pkl')
                lm.sendMessage(today+'***'+pf_code+'****weight delta '+kk+'****'+str((vv.loc[today]-real_w.loc[today]).abs().sum()))
      
            sim_w = {kk:pd.read_pickle(sim_w_path+vv[0]+'.pkl') for kk,vv in conf['sim_w'].items()}
            _,open_position_weight = get_open_position_w(o32_path,shi_conf['open_date'],pf_code)
            sim_w[shi_conf['start_time']].loc[shi_conf['open_date']] = open_position_weight
            shi_op_conf = bt_conf.copy()
            shi_op_conf['start_time'] = shi_conf['start_time']
            btf = BacktestHF({kk:vv.loc[shi_conf['open_date']:] for kk,vv in sim_w.items()},
                         benchmark=op_conf['hedge_index'], capital=op_conf['capital'], commission=0.0005,simulation=True,**shi_op_conf)
            btf.run()
            print(shipan_stats_path+'shipan_'+pf_code+'_stats.pkl')
            stats = save_data(btf.get_stats().loc[shi_conf['next_open_date']:],shipan_stats_path+'shipan_'+pf_code+'_stats.pkl')
            position = save_data(btf.get_position().loc[shi_conf['next_open_date']:],shipan_stats_path+'shipan_'+pf_code+'_position.pkl')
            transac_time = sorted(stats.index.get_level_values(level=1).unique().tolist())
            net = (stats.loc[(slice(None),bt_conf['end_time']),:]['daily_exc'].reset_index().set_index('level_0')['daily_exc'])/100+1
            net = net.cumprod()
            df = cal_performance(net)
            for tt in transac_time:
                df.loc[tt+'_Turnover'] = stats.loc[(slice(None), tt), :]['turnover'].iloc[1:].mean() / 100
            df.loc['Today_Excess'] = stats.loc[(slice(None),bt_conf['end_time']),:]['daily_exc'].iloc[-1]*0.01
            df.loc['Current_MDD'] = net.max()-net.loc[today]
            shipan_stats = (net,df)
    return bt_stats,shipan_stats


# In[21]:


weight_flag = True
bt_stats_dict = {'20190101':{},'20200101':{}}
shipan_stats_dict = {}
for pf_code,config in config_dict.items():
    key_list = config['w_path_dict'].keys()
    print(pf_code,len(key_list))
    res = Parallel(len(key_list))(delayed(update_weight_bt_stats)(k,v,pf_code,config,weight_flag) for k,v in config['w_path_dict'].items())
    for open_date in config['backtest_date']:
        diff_w_net = dict(zip(key_list,[r[0][open_date][0] for r in res]))
        diff_w_perform = dict(zip(key_list,[r[0][open_date][1] for r in res]))
        diff_w_net = pd.DataFrame(diff_w_net)
        diff_w_perform = pd.DataFrame({k:v['Summary'] for k,v in diff_w_perform.items()})
        bt_stats_dict[open_date][pf_code] = (diff_w_net,diff_w_perform)
    shipan_stats_dict[pf_code] = dict(zip(key_list,[r[1] for r in res]))


# In[18]:


shipan_config={'hf':('AlphaHunter',{'ZZ500':('5160803','规模8亿','规模8亿','bt')},['am','pm']),
               'vwap':('QuantMachine',{'ZZ500':('5160503','规模8亿','规模8亿','bt'),'HS300':('5160304','规模4亿','规模4亿','bt300')},['vwap'])}


# In[19]:


from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
def pdf_maker(save_path, report_path,bt):
    story = []
    stylesheet = getSampleStyleSheet()
    stylesheet.add(ParagraphStyle(fontName='SimSun', name='Song', leading=20, fontSize=12))
    normalStyle = stylesheet['Normal']
    now = datetime.datetime.today()
    file_date = now.strftime("%Y%m%d_%H%M%S")
    fig_height, fig_width = 280, 680
    story.append(Paragraph('1. 各模型分20组(前4组)超全市场加权平均超额收益20200101-至今', stylesheet['Song']))

    for excess in shipan_config[bt][2]:
        story.append(Paragraph(excess, stylesheet['Song']))
        add_img(os.path.join(save_path, excess+'_model_predict.png'), story, fig_height*0.8, fig_width*0.9)
        story.append(Spacer(1, 10))
        add_img(os.path.join(save_path, excess+'_score_table.png'), story, fig_height*0.3, fig_width*1)
        story.append(Spacer(1, 10))
        story.append(Paragraph('20200601-至今模型表现', stylesheet['Song']))
        add_img(os.path.join(save_path, excess+'_track_table.png'), story, fig_height*0.3, fig_width*1)
        story.append(Spacer(1, 10))
        story.append(PageBreak())
    i=1
    story.append(Paragraph('2. 集成模型分20组(前4组)加权收益全市场分位数20190101-至今'+'', stylesheet['Song']))
    add_img(os.path.join(save_path, bt+'_quantile_All_in_out_sample.png'), story, fig_height*0.8, fig_width*0.8)
    story.append(Paragraph('3. 集成模型分20组(前4组)加权相对中证500超额收益'+'', stylesheet['Song']))
    add_img(os.path.join(save_path, bt+'_excess_bench500.png'), story, fig_height*0.8, fig_width*0.8)
    story.append(PageBreak())
    def single(name,test,tmp,date=None,rate=0.6):
        get_stats_in_out(test,split_in_out_sample_date=None,save_path=save_path,name=name+'_excess')
        add_img(os.path.join(save_path, name+'_excess.png'), story, fig_height*1, fig_width*0.8)
        df = pd.DataFrame(index=tmp.index, columns=['performance'], data=tmp.index)
        df = pd.concat([df, tmp.round(6)], axis=1)
        render_mpl_table(df, header_columns=0, col_width=3.5, row_height=0.3, font_size=10, 
                         save_path=save_path +name+'_summary.png')
        if len(df.columns)>=4:
            rate = 0.9
        add_img(os.path.join(save_path,name+'_summary.png'), story, fig_height*0.5, fig_width*rate)
        story.append(Spacer(1, 10))
        story.append(PageBreak())
        return 
    number = 4
    for hedge,conf in shipan_config[bt][1].items():
        story.append(Paragraph(str(number)+'. '+shipan_config[bt][0]+' 过优化器（'+'对冲'+hedge+' '+conf[1]+'）回测表现', stylesheet['Song']))
        number+=1
        for k,v in bt_stats_dict.items():
            name = bt+k+conf[3]
            story.append(Paragraph(k+'-至今（'+conf[1]+'）', stylesheet['Song']))
            date = None
            if k=='20190101':
                date = '20200101'
            for kk,vv in config_dict[conf[0]]['w_path_dict'].items():
                if vv[2]:
                    single(name,v[conf[0]][0],v[conf[0]][1],date)  
        story.append(Paragraph(str(number)+'. '+shipan_config[bt][0]+'实盘（'+'对冲'+hedge+' '+conf[2]+'）跟踪表现', stylesheet['Song']))
        number+=1
        for k,v in config_dict[conf[0]]['w_path_dict'].items():
            if v[2]:
                shipan = shipan_stats_dict[conf[0]][k]
                name=bt+'_shipan_'+conf[0]
                single(name,shipan[0],shipan[1])
    i=1
    story.append(Paragraph(str(number)+'. 各模型分20组(前4组)超全市场加权平均超额收益 20190101-至今'+'', stylesheet['Song']))
    for m in need_model:
        story.append(Paragraph(m, stylesheet['Song']))
        add_img(os.path.join(save_path, bt+'_'+m+'_in_out_sample.png'), story, fig_height*0.8, fig_width*0.8)
        if i%2==0:
            story.append(PageBreak())
        i+=1
    doc = SimpleDocTemplate(report_path)
    doc.build(story)


# In[20]:


pdf_maker(save_path, run_path+'compare/' + today + '_Depart_QuantMachine日报.pdf','vwap')
pdf_maker(save_path, run_path+'compare/' + today + '_Depart_AlphaHunter日报.pdf','hf')


# In[21]:


import ftplib
def upload(f, remote_path, local_path):
    fp = open(local_path, "rb")
    buf_size = 1024
    f.storbinary("STOR {}".format(remote_path), fp, buf_size)
    fp.close()


def download(f, remote_path, local_path):
    fp = open(local_path, "wb")
    buf_size = 1024
    f.retrbinary('RETR {}'.format(remote_path), fp.write, buf_size)
    fp.close()
ftp = ftplib.FTP()
ftp.encoding='gbk'
ftp.connect('168.8.2.68')
ftp.login(user='xquant',passwd='Xquant-32')
ftp.cwd('/Xquant/516/QuantMachine回测跟踪/部门因子日报/')
upload(ftp, today + '_Depart_QuantMachine日报.pdf', run_path+'compare/' + today + '_Depart_QuantMachine日报.pdf')
upload(ftp, today + '_Depart_AlphaHunter日报.pdf', run_path+'compare/' + today + '_Depart_AlphaHunter日报.pdf')
ftp.quit()

