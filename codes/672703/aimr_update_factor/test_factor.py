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
    n = 15 if transaction_period == 240 else 10
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
def get_stats_in_out(cum_exc_ret,split_in_out_sample_date=None,name='High_freq_model'):
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
    plt.savefig(name+'.png')
    plt.show()
def get_pct(score,ret):
    ret[score.columns] = score
    ret['full_market_mean'] = ret.iloc[:-1].mean(axis=1)
    ret_rank = ret.rank(axis=1,pct=True)
    ret_rank['portfolio'] = ret_rank.iloc[:,(-len(score.columns)-1):-1].mean(axis=1)
    return ret_rank
excess_list = {'am':('0930',120),'vwap':('0930',240)}
pkl_path = '/data/user/013546/AlphaDataCenter/Factor/neu_factor/'
save_path = '/data/user/013546/AlphaDataCenter/Factor/perform/'
result={}
for t in excess_list:
    result[t]={}
    model_list = [m[:-4] for m in os.listdir(pkl_path)]
    for m in model_list:
        print(m)
        df = pd.read_pickle(pkl_path+m+'.pkl')
        score,score_sub_bench,ret = check_prediction_new(df, transaction_price='vwap', 
                                                       transaction_time=excess_list[t][0], transaction_period=excess_list[t][1], num_threads=10)

        ret_rank = get_pct(score,ret)
        res = (score,score_sub_bench,ret,ret_rank)
        pd.to_pickle(res,save_path+t+'_'+m+'.pkl')