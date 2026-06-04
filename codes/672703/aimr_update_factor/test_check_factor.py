import os
import numpy as np
import pandas as pd
run_path = '/data/user/013546/DailyReport/'
temp_check_path = run_path
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

from xquant.compute.aimr import AIMR
params =AIMR.getParam()
path = '/data/group/800020/AlphaExperiment/dept_vwapf_all/'
path = '/data/group/800020/AlphaExperiment/own_factors_neu/'
save_path = '/data/user/013546/AlphaDataCenter/Factor/own_day/'
close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl')
stocks = close.columns.tolist()
map_dict = pd.read_pickle('/data/user/013546/rubbish/map_dict.pkl')
factor_list = map_dict[int(params)]
i = 1
def single(f):
    df = pd.read_pickle(path+f+'.pkl').reindex(columns=stocks)
    res = check_prediction(df, 'vwap', '0930', 240, i, 20)
    res[1].to_pickle(save_path+'check'+str(i)+'d/'+f+'.pkl')
from sklearn.externals.joblib import Parallel,delayed
while i<=5:
    Parallel(15)(delayed(single)(f) for f in factor_list)
    i+=1
