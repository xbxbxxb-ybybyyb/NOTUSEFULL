import os
import numpy as np
import pandas as pd
from scipy.stats import norm
import matplotlib.pyplot as plt
from check_prediction_hf import check_prediction as cphf
import sys
sys.path.insert(0,'/data/group/800020/AlphaTools/')
from check_prediction_hf_no_shift import check_prediction as cphfno
from report_maker import *
from sklearn.externals.joblib import Parallel,delayed

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
    os.mkdir('temp_for_check_prediction_minute_trade_price') if not os.path.exists(
        'temp_for_check_prediction_minute_trade_price') else None
    time_saver = transaction_price + '_' + transaction_time + '_' + str(transaction_period)
    if os.path.exists('temp_for_check_prediction_minute_trade_price/' + time_saver + '.pkl'):
        trade_price_0 = pd.read_pickle(
            'temp_for_check_prediction_minute_trade_price/' + time_saver + '.pkl').dropna(how='all', axis=0)
        minute_close_0 = pd.read_pickle(
            'temp_for_check_prediction_minute_trade_price/' + time_saver + '_minute_close.pkl')
        add_trade_price_dates = sorted(list(set(trade_price.index) - set(trade_price_0.index)))
        same_trade_price_dates = sorted(list(set(minute_close.index) & set(trade_price_0.index)))
        if len(same_trade_price_dates)>0:
            trade_price = trade_price_0.loc[same_trade_price_dates]
            minute_close = minute_close_0.loc[same_trade_price_dates]
    if not os.path.exists(
            'temp_for_check_prediction_minute_trade_price/' + time_saver + '.pkl') or add_trade_price_dates:
        price = pd.DataFrame(index=adjfactor.index, columns=adjfactor.columns, data=np.nan)
        close = pd.DataFrame(index=adjfactor.index, columns=adjfactor.columns, data=np.nan)
        if not os.path.exists('temp_for_check_prediction_minute_trade_price/' + time_saver + '.pkl'):
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
            close[np.isinf(close)] = np.nan
        price.to_pickle('temp_for_check_prediction_minute_trade_price/' + time_saver + '.pkl')
        close.to_pickle('temp_for_check_prediction_minute_trade_price/' + time_saver + '_minute_close.pkl')


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
    trade_price = pd.read_pickle('temp_for_check_prediction_minute_trade_price/' + time_saver + '.pkl').loc[date_list[0]:date_list[-1]]
    minute_close = pd.read_pickle('temp_for_check_prediction_minute_trade_price/' + time_saver + '_minute_close.pkl').loc[date_list[0]:date_list[-1]]

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
        if isinstance(df_update,dict):
            for k,v in store_data.items():
                v=v.append(df_update[k])
                v = v.loc[~v.index.duplicated(keep='last')].sort_index()
                store_data[k] = v.astype(np.float64)
        else:
            store_data=store_data.append(df_update)
            store_data = store_data.loc[~store_data.index.duplicated(keep='last')].sort_index()
            store_data = store_data.astype(np.float64)
    else:
        store_data = df_update.astype(np.float64)
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
    # plt.show()
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
def get_stats_in_out(cum_exc_ret,split_in_out_sample_date=None,save_path,name='High_freq_model'):
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
    # plt.show()
def get_pct(score,ret):
    ret[score.columns] = score
    ret['full_market_mean'] = ret.iloc[:-1].mean(axis=1)
    ret_rank = ret.rank(axis=1,pct=True)
    ret_rank['portfolio'] = ret_rank.iloc[:,(-len(score.columns)-1):-1].mean(axis=1)
    return ret_rank

close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl')
today = close.index[-1].strftime('%Y%m%d')
stocks = close.columns
model_name_map = {
    'am':['XgboostRegression_0930_1129_re_5d','LinearRegression_industry_0930_1129_re_5d','DeepFM_0930_1129_re_5d'],
 'pm':['XgboostRegression_1300_1459_re_5d','LinearRegression_1300_1459_re_5d','DeepFM_1300_1459_re_5d'],
 'vwap':['XgboostRegression_vwap_re_5d','LinearRegression_vwap_re_5d','DeepFM_vwap_re_5d']}

no_pool_model_name_map = {
    'am':['MLP_Model_0930_1129_re_1d','CatboostMultiClass_Model_R5d_bin_0930_1129_re_5d'],
 'pm':['MLP_Model_1300_1459_re_1d','CatboostMultiClass_Model_R5d_bin_1300_1459_re_5d'],
 'vwap':['MLP_Model_vwap_re_1d','CatboostMultiClass_Model_v1_bin_vwap_re_1d']}

model_dict={'CatboostMultiClass_Model_R5d_bin_0930_1129_re_5d':'Catboost',
            'MLP_Model_0930_1129_re_1d':'MLP',
            'XgboostRegression_0930_1129_re_1d':'Xgboost',
            'XgboostRegression_0930_1129_re_5d':'Xgboost',
            'DeepFM_0930_1129_re_1d':'DeepFM',
            'DeepFM_0930_1129_re_5d':'DeepFM',
            'LinearRegression_industry_0930_1129_re_5d':'LinearRegression',
            'CatboostMultiClass_Model_R5d_bin_1300_1459_re_5d':'Catboost',
             'MLP_Model_1300_1459_re_1d':'MLP',
            'XgboostRegression_1300_1459_re_1d':'Xgboost',
            'XgboostReg_Model_V1_1300_1459_re_1d':'Xgboost',
            'XgboostRegression_1300_1459_re_5d':'Xgboost',
            'DeepFM_1300_1459_re_1d':'DeepFM',
            'DeepFM_1300_1459_re_5d':'DeepFM',
            'LinearRegression_1300_1459_re_5d':'LinearRegression',
            'CatboostMultiClass_Model_v1_bin_vwap_re_1d':'Catboost',
             'MLP_Model_vwap_re_1d':'MLP',
            'XgboostRegression_vwap_re_1d':'Xgboost',
            'XgboostRegression_vwap_re_5d':'Xgboost',
            'DeepFM_vwap_re_1d':'DeepFM',
            'DeepFM_vwap_re_5d':'DeepFM',
            'LinearRegression_vwap_re_5d':'LinearRegression',
            'All_0930':'All',
            'All_vwap':'All',
            'All_1300':'All'
           }
model_name_list = sorted(list(set(model_dict.values())))
act_path = '/data/group/800020/AlphaDataCenter/DailyPrediction/'
pkl_path = '/data/user/013546/AlphaDataCenter/DailyPrediction/pickles/'
base_path = '/data/user/013546/DailyReport/'
excess_path = base_path+'excess/'
save_path = base_path
act_params = {
    'vwap':(act_path+'vwap/','0930',240),
    'am':(act_path+'am/', '0930', 120),
    'pm':(act_path+'pm/', '1300', 120)
}
need_model = sorted(['DeepFM', 'Xgboost', 'LinearRegression', 'All'])

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
        df = get_act(act_path+k+'/'+m+'/','20200501',today).reindex(columns=stocks).astype(np.float64)
        df = save_data(df,pkl_path+k+'/'+m+'.pkl')
        if not df.index.equals(close.loc[df.index[0]:df.index[-1]].index): 
            print(m+' predict date_list is unconsistent!')
        act[k][m] = df
    df = save_data(norm_ppf(act[k]),pkl_path+k+'/All_5d.pkl')
    if not df.index.equals(close.loc[df.index[0]:df.index[-1]].index):
        print('All_5d predict date_list is unconsistent!')
    if k!='vwap':
        act[k]['All_'+v[1]] = df
    else:
        act[k]['All_'+k] = df
tmp_predict_path = '/data/user/013546/AlphaDataCenter/DailyPrediction/'
for e,v in no_pool_model_name_map.items():
    for m in v:
        df = get_act('/data/user/013546/AlphaDataCenter/DailyPrediction/'+e+'/'+m+'/','20190102',today).astype(np.float64)
        df = save_data(df.reindex(columns=stocks),pkl_path+e+'/'+m+'.pkl')
        act[e][m] = df
in_out_sample_date = '20200101'
excess_list = {'am':('0930',120),'pm':('1300',120),'vwap':('0930',240)}
excess = {}
quantile = {}
ave_return ={}
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

        ret_rank = get_pct(score_m,ret_m)
        quantile[m] = ret_rank['portfolio']-ret_rank['full_market_mean']
        tmp_excess = score_sub_bench_m
        print(k,m,tmp_excess.mean())
        tmp_excess = save_data(tmp_excess,excess_path_t+m+'.pkl')
        excess[m] = tmp_excess.mean(axis=1)
        ave_return[m] = excess[m].loc[in_out_sample_date:].mean()
excess = pd.DataFrame(excess)
quantile = pd.DataFrame(quantile)
ave_return = pd.Series(ave_return).to_frame('ave_return').T
excess_hf_model_dict={}
excess_vwap_model_dict={}
quantile_hf_model_dict={}
quantile_vwap_model_dict={}
for m in model_name_list:
    excess_hf_model_dict[m] = {}
    excess_vwap_model_dict[m] = {}
    quantile_hf_model_dict[m] = {}
    quantile_vwap_model_dict[m] = {}
excess_map={'am':'0930','pm':'1300','vwap':'vwap'}
for k,v in excess_map.items():
    this_col = [c for c in excess.columns if v in c]
    excess_t =excess[this_col]
    excess_t = excess_t.rename(columns={c:model_dict[c] for c in excess_t.columns})
    quantile_t =quantile[this_col]
    quantile_t = quantile_t.rename(columns={c:model_dict[c] for c in quantile_t.columns})
    ave_return_t =ave_return[this_col]
    ave_return_t = ave_return_t.rename(columns={c:model_dict[c] for c in ave_return_t.columns})
    draw_custom_style(excess_t[need_model].loc['20200101':].cumsum().copy(),save_path,k,'20200101',split=False,
                      name=k+'_model_predict')
    for model_name in excess_t.columns:
        if k in ['am','pm']:
            excess_hf_model_dict[model_name][k] = excess_t[model_name]
            quantile_hf_model_dict[model_name][k] = quantile_t[model_name]
        else:
            excess_vwap_model_dict[model_name][k] = excess_t[model_name]
            quantile_vwap_model_dict[model_name][k] = quantile_t[model_name]
    df = pd.DataFrame(index=ave_return_t.index, columns=['performance'], data=ave_return_t.index)
    tmp = ave_return_t[need_model].round(6)
    df = pd.concat([df, tmp], axis=1)
    df = df.dropna(axis=1)
#     df.index = [i.strftime('%Y%m%d') for i in df.index]
    render_mpl_table(df, header_columns=0, col_width=2.5, row_height=0.6, font_size=10, save_path=save_path +k+'_score_table'+'.png')
    None if os.path.exists(save_path + 'report/') else os.mkdir(save_path + 'report/')

excess_hf_model_dict = {k:pd.DataFrame(v) for k,v in excess_hf_model_dict.items()}
excess_vwap_model_dict = {k:pd.DataFrame(v) for k,v in excess_vwap_model_dict.items()}
for k in excess_hf_model_dict:
    draw_custom_style(excess_hf_model_dict[k].cumsum(),save_path,k,'20191231',split=True,name='hf_'+k+'_in_out_sample')
for k in excess_vwap_model_dict:
    draw_custom_style(excess_vwap_model_dict[k].cumsum(),save_path,k,'20191231',split=True,name='vwap_'+k+'_in_out_sample')
quantile_hf_model_dict = {k:pd.DataFrame(v) for k,v in quantile_hf_model_dict.items()}
quantile_vwap_model_dict = {k:pd.DataFrame(v) for k,v in quantile_vwap_model_dict.items()}
for k in quantile_hf_model_dict:
    draw_custom_style(quantile_hf_model_dict[k].cumsum(),save_path,k,'20191231',split=True,name='hf_quantile_'+k+'_in_out_sample')
for k in quantile_vwap_model_dict:
    draw_custom_style(quantile_vwap_model_dict[k].cumsum(),save_path,k,'20191231',split=True,name='vwap_quantile_'+k+'_in_out_sample')
import sys
sys.path.insert(0,'/data/group/800020/AlphaTools/')
from BacktestHF import BacktestHF 
from optimize import optimize_hf
pkl_path = '/data/user/013546/AlphaDataCenter/DailyPrediction/pickles/'
am = pd.read_pickle(pkl_path+'am/All_5d.pkl')
pm = pd.read_pickle(pkl_path+'pm/All_5d.pkl')
vwap = pd.read_pickle(pkl_path+'vwap/All_5d.pkl')
if am.index[-1]!=pd.to_datetime(today):
    am = am.append(pm.loc[today:today])
if vwap.index[-1]!=pd.to_datetime(today):
    vwap = vwap.append(pm.loc[today:today])
start_date = '20190103'
hf_model={}
hf_model['0930'] = am.shift(1).iloc[1:]
hf_model['1300'] = pm.loc[start_date:]
vwap_model={}
vwap_model['0930'] = vwap.shift(1).iloc[1:]
backtest={}
last_date = close.index[-2].strftime('%Y%m%d')
print('last_date',last_date)
print('today',today)
capital_dict={'vwap':(6e8,'6e8'),
             'hf':(5e8,'5e8')}
t = 'vwap'
backtest[t] = {'20190101':None,'20200101':None}
capital = capital_dict[t][0]
str_cap = capital_dict[t][1]
print(t,capital,str_cap)
hedge_index='ZZ500'
industry_loose = 0.001000
amt_limit = 0.025
dupl_industry=None#[6133,613401,613402,613403]
split_fin=False
pool_valid_stocks=None
barra_limit_dict = {
    'Beta'+hedge_index[-3:]: (0.01, 0.01), 
    'Momentum':              (0.01, 0.01), 
    'Size':                  (1000, 1000), 
    'Volatility':            (1000, 1000), 
    'EarningsYield':         (1000, 1000), 
    'Liquidity':             (1000, 1000), 
    'Leverage':              (1000, 1000), 
    'Value':                 (1000, 1000), 
    'Growth':                (1000, 1000)
}
w_path_dict = {
                '5d_no_control_size,turnover10%':(0.5,1000),
                '5d_control_size,turnover10%':(0.5,0.01),
                '5d_no_control_size,turnover20%':(0.3,1000),
                '5d_control_size,turnover20%':(0.3,0.01),
              }
def single(k,v):
    turn_ad={'0930':v[0]}
    barra_limit_dict.update({'Size':(v[1],v[1])})
    print(k+' optimize')
    w_path = base_path+'performance/'+t+'_'+k+'_capital'+str_cap+'_amt'+str(amt_limit)+'_turn'+str(v[0])+'_w.pkl'
    if not os.path.exists(w_path):
        pd.DataFrame().to_pickle(w_path)
    w = pd.read_pickle(w_path)
    
    end_time = sorted(list(set(w.keys())))[-1]
    last_weight = w[end_time].loc[last_date]
    w_today = optimize_hf({k:v.loc[today:today] for k,v in vwap_model.items()}, turn_ad, hedge_index, capital, barra_limit_dict=barra_limit_dict, industry_loose=industry_loose, amt_limit=amt_limit, 
          prev_weights=last_weight,pool_valid_stocks=None, dupl_industry=None, split_fin=False)
    save_data(w_today,w_path)
    return w_today
res = Parallel(len(w_path_dict))(delayed(single)(k,v) for k,v in w_path_dict.items())
print('*'*10,t+'日频'+str_cap+'对比回测')
start_time='0930'
end_time='0930'
transaction_period=240
hedge_index = 'ZZ500'
for open_date in backtest[t]:
    print(open_date)
    diff_w_net={}
    diff_w_perform={}
    def single(kk,vv):
        print(kk)
        path = base_path+'performance/'+t+'_'+kk+'_capital'+str_cap+'_amt'+str(amt_limit)+'_turn'+str(vv[0])+'_w'
        w = pd.read_pickle(path+'.pkl')
        btf = BacktestHF({k:v.loc[open_date:] for k,v in w.items()}, start_time=start_time,end_time=end_time,transaction_period=transaction_period, 
                         benchmark=hedge_index, capital=capital, commission=0.0005)
        btf.run()
        stats = btf.get_stats()
        save_data(stats,path+'_stats.pkl')
        transac_time = sorted(stats.index.get_level_values(level=1).unique().tolist())
        net = (stats.loc[(slice(None),end_time),:]['daily_exc'].reset_index().set_index('level_0')['daily_exc'])/100+1
        net = net.cumprod()
        df = cal_performance(net)
        for tt in transac_time:
            df.loc[tt+'_Turnover'] = stats.loc[(slice(None), tt), :]['turnover'].iloc[1:].mean() / 100
        df.loc['Today_Excess'] = stats.loc[(slice(None),end_time),:]['daily_exc'].iloc[-1]*0.01
        diff_w_net[kk] = net
        diff_w_perform[kk] = df
        return net,df
    res = Parallel(len(w_path_dict))(delayed(single)(k,v) for k,v in w_path_dict.items())
    diff_w_net = dict(zip(w_path_dict.keys(),[r[0] for r in res]))
    diff_w_perform = dict(zip(w_path_dict.keys(),[r[1] for r in res]))
    diff_w_net = pd.DataFrame(diff_w_net)
    diff_w_perform = pd.DataFrame({k:v['Summary'] for k,v in diff_w_perform.items()})
    backtest[t][open_date] = (diff_w_net,diff_w_perform)

t='hf'
capital = capital_dict[t][0]
str_cap = capital_dict[t][1]
hedge_index='ZZ500'
industry_loose = 0.001000
amt_limit = 0.025
dupl_industry=None#[6133,613401,613402,613403]
split_fin=False
pool_valid_stocks=None
barra_limit_dict = {
    'Beta'+hedge_index[-3:]: (0.01, 0.01), 
    'Momentum':              (0.01, 0.01), 
    'Size':                  (1000, 1000), 
    'Volatility':            (1000, 1000), 
    'EarningsYield':         (1000, 1000), 
    'Liquidity':             (1000, 1000), 
    'Leverage':              (1000, 1000), 
    'Value':                 (1000, 1000), 
    'Growth':                (1000, 1000)
}
w_path_dict = {
                '5d_no_control_size,turnover20%':(0.5,1000),
                '5d_control_size,turnover20%':(0.5,0.01),
                '5d_no_control_size,turnover40%':(0.3,1000),
                '5d_control_size,turnover40%':(0.3,0.01),
              }
save_perform_path = '/data/user/013546/DailyReport/performance/'
def single(k,v):
    turn_ad={'0930':v[0],'1300':v[0]}
    barra_limit_dict.update({'Size':(v[1],v[1])})
    print(k+' optimize')
    w_hf_path = save_perform_path+t+'_'+k+'_capital'+str_cap+'_amt'+str(amt_limit)+'_turn'+str(v[0])+'_w.pkl'
    if not os.path.exists(w_hf_path):
        pd.DataFrame().to_pickle(w_hf_path)
    w_hf = pd.read_pickle(w_hf_path)
    end_time = sorted(list(set(w_hf.keys())))[-1]
    last_weight_hf = w_hf[end_time].loc[last_date]
    w_today = optimize_hf({k:v.loc[today:today] for k,v in hf_model.items()}, turn_ad, hedge_index, capital, barra_limit_dict=barra_limit_dict, industry_loose=industry_loose, amt_limit=amt_limit, 
          prev_weights=last_weight_hf, pool_valid_stocks=None, dupl_industry=None, split_fin=False)
    save_data(w_today,w_hf_path)
Parallel(len(w_path_dict))(delayed(single)(k,v) for k,v in w_path_dict.items())
backtest[t] = {'20190101':None,'20200101':None}
print('*'*10,'高频5d_'+str_cap+'对比回测')
start_time='0930'
end_time='1300'
transaction_period=120
hedge_index = 'ZZ500'
for open_date in backtest[t]:
    print(open_date)
    def single(kk,vv):
        print(kk)
        path = base_path+'performance/'+t+'_'+kk+'_capital'+str_cap+'_amt'+str(amt_limit)+'_turn'+str(vv[0])+'_w'
        w = pd.read_pickle(path+'.pkl')
        if open_date=='20190101':
            end_date = '20191231'
        else:
            end_date = '20201231'
        btf = BacktestHF({k:v.loc[open_date:] for k,v in w.items()}, start_time=start_time,end_time=end_time,transaction_period=transaction_period, 
                         benchmark=hedge_index, capital=capital, commission=0.0005)
        btf.run()
        stats = btf.get_stats()
        save_data(stats,path+'_stats.pkl')
        transac_time = sorted(stats.index.get_level_values(level=1).unique().tolist())
        net = (stats.loc[(slice(None),'1300'),:]['daily_exc'].reset_index().set_index('level_0')['daily_exc'])/100+1
        net = net.cumprod()
        df = cal_performance(net)
        for tt in transac_time:
            df.loc[tt+'_Turnover'] = stats.loc[(slice(None), tt), :]['turnover'].iloc[1:].mean() / 100
        df.loc['Today_Excess'] = stats.loc[(slice(None),end_time),:]['daily_exc'].iloc[-1]*0.01
        return net,df
    res = Parallel(len(w_path_dict))(delayed(single)(k,v) for k,v in w_path_dict.items())
    diff_w_net = dict(zip(w_path_dict.keys(),[r[0] for r in res]))
    diff_w_perform = dict(zip(w_path_dict.keys(),[r[1] for r in res]))
    diff_w_net = pd.DataFrame(diff_w_net)
    diff_w_perform = pd.DataFrame({k:v['Summary'] for k,v in diff_w_perform.items()})
    backtest[t][open_date] = (diff_w_net,diff_w_perform)
backtest300={}
hedge_index='HS300'
benchmark = hedge_index[-3:]
save_perform_path = 'performance/benchmark_'+benchmark+'/'
last_date = close.index[-2].strftime('%Y%m%d')
print('last_date',last_date)
print('today',today)
capital_dict={'vwap':(2e8,'2e8'),
             'hf':(5e8,'5e8')}
t = 'vwap'
backtest300[t] = {'20190101':None,'20200101':None}
capital = capital_dict[t][0]
str_cap = capital_dict[t][1]
print(t,capital,str_cap)
industry_loose = 0.005000
amt_limit = 0.025
dupl_industry=[6133,6134]
split_fin=False
pool_valid_stocks=None
barra_limit_dict = {
    'Beta'+hedge_index[-3:]: (0.05, 0.05), 
    'Momentum':              (0.05, 0.05), 
    'Size':                  (0.5, 0.5), 
    'Volatility':            (1000, 1000), 
    'EarningsYield':         (1000, 1000), 
    'Liquidity':             (1000, 1000), 
    'Leverage':              (1000, 1000), 
    'Value':                 (1000, 1000), 
    'Growth':                (1000, 1000)
}
w_path_dict = {
                '5d_control_size,turnover10%':(0.4,0.5)
              }
def single(k,v):
    turn_ad={'0930':v[0]}
    barra_limit_dict.update({'Size':(v[1],v[1])})
    print(k+' optimize')
    w_path = save_perform_path+t+'_'+k+'_capital'+str_cap+'_amt'+str(amt_limit)+'_turn'+str(v[0])+'_w.pkl'
    w = pd.read_pickle(w_path)
    end_time = sorted(list(set(w.keys())))[-1]
    last_weight = w[end_time].loc[last_date]
    w_today = optimize_hf({k:v.loc[today:today] for k,v in vwap_model.items()}, turn_ad, hedge_index, capital, barra_limit_dict=barra_limit_dict, industry_loose=industry_loose, amt_limit=amt_limit, 
          prev_weights=last_weight,pool_valid_stocks=pool_valid_stocks, dupl_industry=dupl_industry, split_fin=split_fin)
    save_data(w_today,w_path)
    return w_today
res = Parallel(len(w_path_dict))(delayed(single)(k,v) for k,v in w_path_dict.items())
print('*'*10,'benchmark'+benchmark+t+'日频'+str_cap+'对比回测')
start_time='0930'
end_time='0930'
transaction_period=240
for open_date in backtest[t]:
    print(open_date)
    diff_w_net={}
    diff_w_perform={}
    def single(kk,vv):
        print(kk)
        path = save_perform_path+t+'_'+kk+'_capital'+str_cap+'_amt'+str(amt_limit)+'_turn'+str(vv[0])+'_w'
        w = pd.read_pickle(path+'.pkl')
        btf = BacktestHF({k:v.loc[open_date:] for k,v in w.items()}, start_time=start_time,end_time=end_time,transaction_period=transaction_period, 
                         benchmark=hedge_index, capital=capital, commission=0.0005)
        btf.run()
        stats = btf.get_stats()
        save_data(stats,path+'_stats.pkl')
        transac_time = sorted(stats.index.get_level_values(level=1).unique().tolist())
        net = (stats.loc[(slice(None),end_time),:]['daily_exc'].reset_index().set_index('level_0')['daily_exc'])/100+1
        net = net.cumprod()
        df = cal_performance(net)
        for tt in transac_time:
            df.loc[tt+'_Turnover'] = stats.loc[(slice(None), tt), :]['turnover'].iloc[1:].mean() / 100
        df.loc['Today_Excess'] = stats.loc[(slice(None),end_time),:]['daily_exc'].iloc[-1]*0.01
        diff_w_net[kk] = net
        diff_w_perform[kk] = df
        return net,df
    res = Parallel(len(w_path_dict))(delayed(single)(k,v) for k,v in w_path_dict.items())
    diff_w_net = dict(zip(w_path_dict.keys(),[r[0] for r in res]))
    diff_w_perform = dict(zip(w_path_dict.keys(),[r[1] for r in res]))
    diff_w_net = pd.DataFrame(diff_w_net)
    diff_w_perform = pd.DataFrame({k:v['Summary'] for k,v in diff_w_perform.items()})
    backtest300[t][open_date] = (diff_w_net,diff_w_perform)
t='hf'
capital = capital_dict[t][0]
str_cap = capital_dict[t][1]
industry_loose = 0.005000
amt_limit = 0.025
dupl_industry=[6133,6134]
split_fin=False
pool_valid_stocks=None
barra_limit_dict = {
    'Beta'+hedge_index[-3:]: (0.05, 0.05), 
    'Momentum':              (0.05, 0.05), 
    'Size':                  (0.5, 0.5), 
    'Volatility':            (1000, 1000), 
    'EarningsYield':         (1000, 1000), 
    'Liquidity':             (1000, 1000), 
    'Leverage':              (1000, 1000), 
    'Value':                 (1000, 1000), 
    'Growth':                (1000, 1000)
}
w_path_dict = {
                '5d_control_size,turnover20%':(0.4,0.5)
              }
def single(k,v):
    turn_ad={'0930':v[0],'1300':v[0]}
    barra_limit_dict.update({'Size':(v[1],v[1])})
    print(k+' optimize')
    w_hf_path = save_perform_path+t+'_'+k+'_capital'+str_cap+'_amt'+str(amt_limit)+'_turn'+str(v[0])+'_w.pkl'
    w_hf = pd.read_pickle(w_hf_path)
    end_time = sorted(list(set(w_hf.keys())))[-1]
    last_weight_hf = w_hf[end_time].loc[last_date]
    w_today = optimize_hf({k:v.loc[today:today] for k,v in hf_model.items()}, turn_ad, hedge_index, capital, 
                          barra_limit_dict=barra_limit_dict, industry_loose=industry_loose, amt_limit=amt_limit, 
          prev_weights=last_weight_hf, pool_valid_stocks=pool_valid_stocks, dupl_industry=dupl_industry, split_fin=split_fin)
    save_data(w_today,w_hf_path)
Parallel(len(w_path_dict))(delayed(single)(k,v) for k,v in w_path_dict.items())
backtest300[t] = {'20190101':None,'20200101':None}
print('*'*10,'高频5d_'+str_cap+'对比回测')
start_time='0930'
end_time='1300'
transaction_period=120
for open_date in backtest300[t]:
    print(open_date)
    def single(kk,vv):
        print(kk)
        path = save_perform_path+t+'_'+kk+'_capital'+str_cap+'_amt'+str(amt_limit)+'_turn'+str(vv[0])+'_w'
        w = pd.read_pickle(path+'.pkl')
        if open_date=='20190101':
            end_date = '20191231'
        else:
            end_date = '20201231'
        btf = BacktestHF({k:v.loc[open_date:] for k,v in w.items()}, start_time=start_time,
                         end_time=end_time,transaction_period=transaction_period, 
                         benchmark=hedge_index, capital=capital, commission=0.0005)
        btf.run()
        stats = btf.get_stats()
        save_data(stats,path+'_stats.pkl')
        transac_time = sorted(stats.index.get_level_values(level=1).unique().tolist())
        net = (stats.loc[(slice(None),'1300'),:]['daily_exc'].reset_index().set_index('level_0')['daily_exc'])/100+1
        net = net.cumprod()
        df = cal_performance(net)
        for tt in transac_time:
            df.loc[tt+'_Turnover'] = stats.loc[(slice(None), tt), :]['turnover'].iloc[1:].mean() / 100
        df.loc['Today_Excess'] = stats.loc[(slice(None),end_time),:]['daily_exc'].iloc[-1]*0.01
        return net,df
    res = Parallel(len(w_path_dict))(delayed(single)(k,v) for k,v in w_path_dict.items())
    diff_w_net = dict(zip(w_path_dict.keys(),[r[0] for r in res]))
    diff_w_perform = dict(zip(w_path_dict.keys(),[r[1] for r in res]))
    diff_w_net = pd.DataFrame(diff_w_net)
    diff_w_perform = pd.DataFrame({k:v['Summary'] for k,v in diff_w_perform.items()})
    backtest300[t][open_date] = (diff_w_net,diff_w_perform)
#实盘权重
benchmark = '500'
hf_shi_w = pd.read_pickle('/data/user/013546/DailyReport/performance/hf_5d_no_control_size,turnover20%_capital5e8_amt0.025_turn0.5_w.pkl')
vwap_shi_w =pd.read_pickle('/data/user/013546/DailyReport/performance/vwap_5d_no_control_size,turnover10%_capital6e8_amt0.025_turn0.5_w.pkl')
simulation_w_am_path = '/data/group/800020/AlphaDataCenter/DailyWeight/benchmark_'+benchmark+'/simulation_w_am.pkl'
simulation_w_pm_path = '/data/group/800020/AlphaDataCenter/DailyWeight/benchmark_'+benchmark+'/simulation_w_pm.pkl'
simulation_w_vwap_path = '/data/group/800020/AlphaDataCenter/DailyWeight/benchmark_'+benchmark+'/simulation_w_vwap.pkl'
hf_shi_w['0930'].to_pickle(simulation_w_am_path)
hf_shi_w['1300'].to_pickle(simulation_w_pm_path)
vwap_shi_w['0930'].to_pickle(simulation_w_vwap_path)
#实盘权重
benchmark = '300'
hf_shi_w = pd.read_pickle('/data/user/013546/DailyReport/performance/benchmark_'+benchmark+'/'+'hf_5d_control_size,turnover20%_capital5e8_amt0.025_turn0.4_w.pkl')
vwap_shi_w =pd.read_pickle('/data/user/013546/DailyReport/performance/benchmark_'+benchmark+'/'+'vwap_5d_control_size,turnover10%_capital2e8_amt0.025_turn0.4_w.pkl')
simulation_w_am_path = '/data/group/800020/AlphaDataCenter/DailyWeight/benchmark_'+benchmark+'/simulation_w_am.pkl'
simulation_w_pm_path = '/data/group/800020/AlphaDataCenter/DailyWeight/benchmark_'+benchmark+'/simulation_w_pm.pkl'
simulation_w_vwap_path = '/data/group/800020/AlphaDataCenter/DailyWeight/benchmark_'+benchmark+'/simulation_w_vwap.pkl'
hf_shi_w['0930'].to_pickle(simulation_w_am_path)
hf_shi_w['1300'].to_pickle(simulation_w_pm_path)
vwap_shi_w['0930'].to_pickle(simulation_w_vwap_path)
def get_open_position_w(open_o32_date,pf_code):
    
    x = pd.read_excel(o32_path + '综合信息查询_组合证券_' + open_o32_date + '.xls', converters={'组合名称':str, '证券代码':str})
    x = x[(x['组合名称']==pf_code) & (x['证券类别']=='股票')]
    x.index = [i + '.SH' if i[0]=='6' else i + '.SZ' for i in x['证券代码']]
    x['持仓'] = (x['持仓'] / 100).round(0).astype(int) * 100
    if pf_code=='5160503':
        price = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/pre_close.pkl').loc[open_o32_date]
    else:
        price = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/minute/Close/'+open_o32_date+'.pkl').iloc[119]
#     price = x['最新价']
    x_amt = (x['持仓']*price.loc[x['持仓'].index])
    x_amt = x['市值']
    open_position_weight = x_amt/x_amt.sum()
    open_position_weight = open_position_weight.reindex(price.index)
    open_position_weight = open_position_weight.fillna(0)
    capital = x_amt.sum()
#     capital = capital*1.001
    return capital,open_position_weight
benchmark = '500'
pf_code = '5160803'
open_o32_date = '20200601'
o32_path = '/data/user/011477/order/O32/afternoon/'
capital,open_position_weight = get_open_position_w(open_o32_date,pf_code)
hf_w_start_date = '20200601'
vwap_w_start_date = '20200511'
vwap300_w_start_date = '20200602'
shipan_track={}
weight_path = '/data/group/800020/AlphaDataCenter/DailyWeight/benchmark_'+benchmark+'/'
w_am0 = pd.read_pickle(weight_path+'weight_bk/20200515/simulation_w_am.pkl')
w_pm0 = pd.read_pickle(weight_path+'weight_bk/20200515/simulation_w_pm.pkl')
w_vwap0 = pd.read_pickle(weight_path+'weight_bk/vwap_5e8.pkl')
w_am = pd.read_pickle(weight_path+'/simulation_w_am.pkl').loc[hf_w_start_date:today]
w_pm = pd.read_pickle(weight_path+'/simulation_w_pm.pkl').loc[hf_w_start_date:today]
w_vwap = pd.read_pickle(weight_path+'/simulation_w_vwap.pkl').loc[vwap_w_start_date:today]
w_vwap300 = pd.read_pickle('/data/group/800020/AlphaDataCenter/DailyWeight/benchmark_300/simulation_w_vwap.pkl').loc[vwap300_w_start_date:]
def temp(df0,df1):
    v = df0.append(df1)
    return  v.loc[~v.index.duplicated(keep='last')].sort_index()
w_am = temp(w_am0,w_am)
w_pm= temp(w_pm0,w_pm)
w_vwap = temp(w_vwap0,w_vwap)
stats_path = base_path+'performance/'
if not os.path.exists(stats_path):
    os.makedirs(stats_path)
print('*'*10,' shipan track AlphaHunter')
open_date = '20200601'
next_open_date = '20200602'
capital = 53e7
capital_dict = {capital:('53e7','5.3亿')}
v = capital_dict[capital]
e = 'hf'
t = e+'_capital'+v[0]
print(t)
w = {'0930':w_am,'1300':w_pm}
w['1300'].loc[open_date] = open_position_weight
start_time='1300'
end_time='1300'
transaction_period=120
hedge_index = 'ZZ500'
btf = BacktestHF({k:v.loc[open_date:] for k,v in w.items()}, start_time=start_time,end_time=end_time,transaction_period=transaction_period, 
                 benchmark=hedge_index, capital=capital, commission=0.0005,simulation=True)
btf.run()
this_stats = btf.get_stats()
old_stats = pd.read_pickle(stats_path+'shipan_'+e+'_stats.pkl')
stats = old_stats.loc[:open_date].append(this_stats.loc[next_open_date:])
stats = stats.loc[~stats.index.duplicated(keep='last')]
stats.to_pickle(stats_path+'shipan_'+e+'_stats.pkl')
transac_time = sorted(stats.index.get_level_values(level=1).unique().tolist())
net = (stats.loc[(slice(None),'1300'),:]['daily_exc'].reset_index().set_index('level_0')['daily_exc'])/100+1
net = net.cumprod()
df = cal_performance(net)
for tt in transac_time:
    df.loc[tt+'_Turnover'] = stats.loc[(slice(None), tt), :]['turnover'].iloc[1:].mean() / 100
df.loc['Today_Excess'] = stats.loc[(slice(None),end_time),:]['daily_exc'].iloc[-1]*0.01
shipan_track['hf'] = (net,df,v[1])
stats.tail()
pf_code = '5160503'
open_o32_date = '20200515'
o32_path = '/data/user/011477/order/O32/afternoon/'
capital,open_position_weight = get_open_position_w(open_o32_date,pf_code)
open_date = '20200515'
next_open_date = '20200518'
capital = 53e7
capital_dict = {capital:('53e7','5.3亿')}
e = 'vwap'
v = capital_dict[capital]
print('*'*10,' shipan track QuantMachine_'+v[0],'open date:',open_date)
t = e+'_capital'+v[0]
print(t)
w = {'0930':w_vwap}
w['0930'].loc[open_o32_date] = open_position_weight
start_time='0930'
end_time='0930'
transaction_period=240
hedge_index = 'ZZ500'
btf = BacktestHF({k:v.loc[open_date:] for k,v in w.items()}, start_time=start_time,end_time=end_time,transaction_period=transaction_period, 
                 benchmark=hedge_index, capital=capital, commission=0.0005,simulation=True)
btf.run()
print(stats_path+'shipan_'+e+'_stats.pkl')
this_stats = btf.get_stats()
old_stats = pd.read_pickle(stats_path+'shipan_'+e+'_stats.pkl')
stats = old_stats.loc[:open_date].append(this_stats.loc[next_open_date:])
stats = stats.loc[~stats.index.duplicated(keep='last')]
stats.to_pickle(stats_path+'shipan_'+e+'_stats.pkl')
transac_time = sorted(stats.index.get_level_values(level=1).unique().tolist())
net = (stats.loc[(slice(None),'0930'),:]['daily_exc'].reset_index().set_index('level_0')['daily_exc'])/100+1
net = net.cumprod()
df = cal_performance(net)
for tt in transac_time:
    df.loc[tt+'_Turnover'] = stats.loc[(slice(None), tt), :]['turnover'].iloc[1:].mean() / 100
df.loc['Today_Excess'] = stats.loc[(slice(None),end_time),:]['daily_exc'].iloc[-1]*0.01
shipan_track[e] = (net,df,v[1])
stats.tail()
pf_code = '5160304'
open_o32_date = '20200602'
o32_path = '/data/user/011477/order/O32/afternoon/'
capital,open_position_weight = get_open_position_w(open_o32_date,pf_code)
open_date = '20200602'
next_open_date = '20200603'
capital = 20e7
capital_dict = {capital:('20e7','2亿')}
e = 'vwap300'
v = capital_dict[capital]
print('*'*10,' shipan track QuantMachine_'+v[0],'open date:',open_date)
t = e+'_capital'+v[0]
print(t)
w = {'0930':w_vwap300}
w['0930'].loc[open_o32_date] = open_position_weight
start_time='0930'
end_time='0930'
transaction_period=240
hedge_index = 'ZZ500'
btf = BacktestHF({k:v.loc[open_date:] for k,v in w.items()}, start_time=start_time,end_time=end_time,transaction_period=transaction_period, 
                 benchmark=hedge_index, capital=capital, commission=0.0005,simulation=True)
btf.run()
print(stats_path+'shipan_'+e+'_stats.pkl')
stats = btf.get_stats()
if os.path.exists(stats_path+'shipan_'+e+'_stats.pkl'):
    old_stats = pd.read_pickle(stats_path+'shipan_'+e+'_stats.pkl')
    stats = old_stats.loc[:open_date].append(stats.loc[next_open_date:])
stats = stats.loc[~stats.index.duplicated(keep='last')]
stats.to_pickle(stats_path+'shipan_'+e+'_stats.pkl')
transac_time = sorted(stats.index.get_level_values(level=1).unique().tolist())
net = (stats.loc[(slice(None),'0930'),:]['daily_exc'].reset_index().set_index('level_0')['daily_exc'])/100+1
net = net.cumprod()
df = cal_performance(net)
for tt in transac_time:
    df.loc[tt+'_Turnover'] = stats.loc[(slice(None), tt), :]['turnover'].iloc[1:].mean() / 100
df.loc['Today_Excess'] = stats.loc[(slice(None),end_time),:]['daily_exc'].iloc[-1]*0.01
shipan_track[e] = (net,df,v[1])
stats.tail()
excess_map_dict={'hf':'AlphaHunter','vwap':'QuantMachine'}
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
def pdf_maker(save_path, report_path,bt,backtest,backtest300,shipan,model_list,excess_type=['am','pm']):
    
    story = []
    stylesheet = getSampleStyleSheet()
    stylesheet.add(ParagraphStyle(fontName='SimSun', name='Song', leading=20, fontSize=12))
    normalStyle = stylesheet['Normal']
    now = datetime.datetime.today()
    file_date = now.strftime("%Y%m%d_%H%M%S")
    fig_height, fig_width = 280, 680
    story.append(Paragraph('1. 各模型分20组(前4组)超全市场加权平均超额收益20200101-至今', stylesheet['Song']))

    for excess in excess_type:
        story.append(Paragraph(excess, stylesheet['Song']))
        add_img(os.path.join(save_path, excess+'_model_predict.png'), story, fig_height*0.8, fig_width*0.9)
        story.append(Spacer(1, 10))
        add_img(os.path.join(save_path, excess+'_score_table.png'), story, fig_height*0.3, fig_width*1)
        story.append(Spacer(1, 10))
        story.append(PageBreak())
    i=1
    story.append(Paragraph('2. 集成模型分20组(前4组)加权收益全市场分位数20190101-至今'+'', stylesheet['Song']))
    add_img(os.path.join(save_path, bt+'_quantile_All_in_out_sample.png'), story, fig_height*0.8, fig_width*0.8)
    story.append(PageBreak())
    story.append(Paragraph('3. '+excess_map_dict[bt]+' 过优化器（对冲ZZ500）回测表现', stylesheet['Song']))
    for k,v in backtest.items():
        name = bt+k+'bt'
        if bt=='vwap':
            story.append(Paragraph(k+'-至今（规模6亿）', stylesheet['Song']))
        else:
            story.append(Paragraph(k+'-至今（规模5亿）', stylesheet['Song']))
        date = None
        if k=='20190101':
            date = '20200101'
        get_stats_in_out(v[0],split_in_out_sample_date=date,save_path=save_path,name=name+'_excess')
        add_img(os.path.join(save_path, name+'_excess.png'), story, fig_height*1, fig_width*0.8)
    
        tmp = v[1]
        df = pd.DataFrame(index=tmp.index, columns=['performance'], data=tmp.index)
        df = pd.concat([df, tmp.round(6)], axis=1)
        render_mpl_table(df, header_columns=0, col_width=3.5, row_height=0.3, font_size=10, 
                         save_path=save_path +name+'_summary.png')
        if bt=='vwap':
            add_img(os.path.join(save_path,name+'_summary.png'), story, fig_height*0.5, fig_width*0.9)
        else:
            add_img(os.path.join(save_path,name+'_summary.png'), story, fig_height*0.5, fig_width*0.9)
        story.append(Spacer(1, 10))
        story.append(PageBreak())
    story.append(Paragraph('4. '+excess_map_dict[bt]+'实盘跟踪表现（对冲500 规模'+shipan[2]+'）', stylesheet['Song']))
#     story.append(Paragraph('3. '+excess_map_dict[bt]+' 1亿规模过优化器回测表现', stylesheet['Song']))
    name=bt+'_shipan'
    get_stats_in_out(shipan[0],save_path=save_path,name=name+'_excess')
#     add_img(os.path.join(save_path, bt+'_capital10e7_bt.png'), story, fig_height*1, fig_width*0.8)
    add_img(os.path.join(save_path, name+'_excess.png'), story, fig_height*1, fig_width*0.8)
    tmp = shipan[1]
    df = pd.DataFrame(index=tmp.index, columns=['performance'], data=tmp.index)
    df = pd.concat([df, tmp.round(6)], axis=1)
    render_mpl_table(df, header_columns=0, col_width=3.5, row_height=0.3, font_size=10, 
                     save_path=save_path +name+'_summary.png')
    add_img(os.path.join(save_path,name+'_summary.png'), story, fig_height*0.5, fig_width*0.6)
    story.append(Spacer(1, 10))
    story.append(PageBreak())
    story.append(Paragraph('5. '+excess_map_dict[bt]+' 过优化器（对冲HS300）回测表现', stylesheet['Song']))
    for k,v in backtest300.items():
        name = bt+k+'bt300'
        if bt=='vwap':
            story.append(Paragraph(k+'-至今（规模2亿）', stylesheet['Song']))
        else:
            story.append(Paragraph(k+'-至今（规模5亿）', stylesheet['Song']))
        date = None
        if k=='20190101':
            date = '20200101'
        get_stats_in_out(v[0],split_in_out_sample_date=date,save_path=save_path,name=name+'_excess')
        add_img(os.path.join(save_path, name+'_excess.png'), story, fig_height*1, fig_width*0.8)
    
        tmp = v[1]
        df = pd.DataFrame(index=tmp.index, columns=['performance'], data=tmp.index)
        df = pd.concat([df, tmp.round(6)], axis=1)
        render_mpl_table(df, header_columns=0, col_width=3.5, row_height=0.3, font_size=10, 
                         save_path=save_path +name+'_summary.png')
        if bt=='vwap':
            add_img(os.path.join(save_path,name+'_summary.png'), story, fig_height*0.5, fig_width*0.6)
        else:
            add_img(os.path.join(save_path,name+'_summary.png'), story, fig_height*0.5, fig_width*0.6)
        story.append(Spacer(1, 10))
        story.append(PageBreak())
    number = 6
    if bt=='vwap':
        story.append(Paragraph('6. '+excess_map_dict[bt]+'300实盘跟踪表现（对冲300 规模2亿）', stylesheet['Song']))
    #     story.append(Paragraph('3. '+excess_map_dict[bt]+' 1亿规模过优化器回测表现', stylesheet['Song']))
        name=bt+'300_shipan'
        get_stats_in_out(shipan_track['vwap300'][0],save_path=save_path,name=name+'_excess')
    #     add_img(os.path.join(save_path, bt+'_capital10e7_bt.png'), story, fig_height*1, fig_width*0.8)
        add_img(os.path.join(save_path, name+'_excess.png'), story, fig_height*1, fig_width*0.8)
        tmp = shipan_track['vwap300'][1]
        df = pd.DataFrame(index=tmp.index, columns=['performance'], data=tmp.index)
        df = pd.concat([df, tmp.round(6)], axis=1)
        render_mpl_table(df, header_columns=0, col_width=3.5, row_height=0.3, font_size=10, 
                         save_path=save_path +name+'_summary.png')
        add_img(os.path.join(save_path,name+'_summary.png'), story, fig_height*0.5, fig_width*0.6)
        story.append(Spacer(1, 10))
        story.append(PageBreak())
    i=1
    story.append(Paragraph(str(number)+'. 各模型分20组(前4组)超全市场加权平均超额收益 20190101-至今'+'', stylesheet['Song']))
    for m in model_list:
        story.append(Paragraph(m, stylesheet['Song']))
        add_img(os.path.join(save_path, bt+'_'+m+'_in_out_sample.png'), story, fig_height*0.8, fig_width*0.8)
        if i%2==0:
            story.append(PageBreak())
        i+=1
    doc = SimpleDocTemplate(report_path)
    doc.build(story)
pdf_maker(save_path, 'compare/' + today + '_QuantMachine日报.pdf','vwap',backtest['vwap'],backtest300['vwap'],
          shipan_track['vwap'],need_model,['vwap'])
pdf_maker(save_path, 'compare/' + today + '_AlphaHunter日报.pdf','hf',backtest['hf'],backtest300['hf'],
          shipan_track['hf'],need_model,['am','pm'])