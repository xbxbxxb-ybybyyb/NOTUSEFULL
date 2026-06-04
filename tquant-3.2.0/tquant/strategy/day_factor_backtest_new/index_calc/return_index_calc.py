from tquant.strategy.day_factor_backtest_new.util.utility import calc_year_date_num
import pandas as pd
import numpy as np
from tquant.strategy.day_factor_backtest_new.data.data_manager import DataManager
from tquant.strategy.day_factor_backtest_new.data.data_preprocess import regression_ols, align_data_inner
from sklearn.model_selection import train_test_split


def calc_cum_return_ts(return_ps, interest_type='SIMPLE'):
    if interest_type == 'SIMPLE':
        res = return_ps.cumsum() + 1
    else:
        res = (return_ps + 1).cumprod()
    return res


def calc_annualized_return(return_ps, interest_type='SIMPLE'):
    year_date_num = calc_year_date_num(return_ps)
    if interest_type == 'SIMPLE':
        res = return_ps.mean() * year_date_num
    else:
        res = calc_cum_return_ts(return_ps, interest_type=interest_type).iloc[-1] ** (
                year_date_num / len(return_ps)) - 1
    return res


def cal_hpr_daily(stock_close_pd, holding_period):
    holding_period_ret = stock_close_pd.shift(-1 * holding_period) / stock_close_pd - 1
    holding_period_ret_daily = (holding_period_ret + 1) ** (1 / holding_period) - 1
    return holding_period_ret_daily


def sample_random(excess, random_state=0, bootstrap_steps=9):
    ## sample containing two parts
    # part 1: 10% of the sample
    sample_90, sample_10 = train_test_split(excess, test_size=1. / (bootstrap_steps + 1), random_state=random_state)
    # part 2:bootstrap sampling of the rest 90%
    excess_sample = sample_10.tolist()
    for i in range(bootstrap_steps):
        sample_new = sample_90.sample(n=len(sample_10), replace=True, random_state=random_state).tolist()
        excess_sample += sample_new
        random_state += 10
    return pd.Series(excess_sample).mean()


def compute_sampling_ret_stat(excess_return, in_sample=True, random_state=0, bootstrap_steps=9,
                              experiment_steps=10):
    """
    random sampling of excess return
    """
    assert bootstrap_steps >= 1, "bootstrap_steps must be >= 1"
    sample_bin_ret_mean = []
    for i in range(experiment_steps):
        sample_bin_ret_mean.append(
            sample_random(excess_return, random_state=random_state, bootstrap_steps=bootstrap_steps) * 1e4)
        random_state += 1
    sample_bin_ret_mean = pd.Series(sample_bin_ret_mean, index=np.arange(1, experiment_steps + 1))

    bins_ret_diff2ret = (sample_bin_ret_mean.nlargest(
        int(experiment_steps / 2)).mean() - sample_bin_ret_mean.nsmallest(
        int(experiment_steps / 2)).mean()) / sample_bin_ret_mean.mean()
    std2ret = sample_bin_ret_mean.std() / sample_bin_ret_mean.mean()

    sample_bins_ret_stat = pd.DataFrame([bins_ret_diff2ret, std2ret])
    sample_bins_ret_stat.index = ['bins_ret_diff2ret', 'std2ret']
    sample_bins_ret_stat.columns = ['sample_bins_ret_stat']

    sample_bin_ret_mean = sample_bin_ret_mean.to_frame()
    sample_bin_ret_mean.columns = ['sample_bin_ret_mean']

    bin_ret_diff = pd.DataFrame(index=excess_return.index[::5],
                                columns=[str(i) for i in np.arange(1, experiment_steps + 1)] + ['bins_ret_diff2ret',
                                                                                                'sample_std2ret'])
    if bin_ret_diff.shape[0] <= 50:
        print('warning, date num less than 250')
        sample_bins_ret_diff2ret = np.nan
        sample_std2ret = np.nan

    for sdate, edate in zip(bin_ret_diff.index, bin_ret_diff.index[50:]):
        ret_list = []
        for iexp in np.arange(1, experiment_steps + 1):
            _ = sample_random(excess_return[sdate:edate], random_state=iexp) * 1e4
            ret_list.append(_)
            bin_ret_diff.loc[edate, str(iexp)] = _
        ret_list = pd.Series(ret_list, index=np.arange(1, experiment_steps + 1))
        ret_mean = ret_list.mean()
        bin_ret_diff.loc[edate, 'bins_ret_diff2ret'] = (ret_list.nlargest(
            int(experiment_steps / 2)).mean() - ret_list.nsmallest(int(experiment_steps / 2)).mean()) / ret_mean
        bin_ret_diff.loc[edate, 'sample_std2ret'] = ret_list.std() / ret_mean

    sample_bins_ret_diff2ret = bin_ret_diff['bins_ret_diff2ret'].dropna()
    sample_std2ret = bin_ret_diff['sample_std2ret'].dropna()

    return sample_bin_ret_mean, sample_bins_ret_stat, sample_bins_ret_diff2ret, sample_std2ret


def max_drawdown_ts(cum_return_ps, interest_type='SIMPLE', return_drawdown_period=False):
    assert isinstance(cum_return_ps, pd.Series)
    cum_return_ps = cum_return_ps.fillna(0)
    cum_max = np.maximum.accumulate(cum_return_ps)
    if interest_type == 'SIMPLE':
        mdd_ts = cum_return_ps - cum_max
    else:
        mdd_ts = (cum_return_ps - cum_max) / cum_max
    mdd_idx = mdd_ts.idxmin()
    mdd_max_level = cum_max.loc[mdd_idx]
    _ = cum_return_ps.loc[:mdd_idx]
    try:
        mdd_begin_idx = _[_ == mdd_max_level].index[-1]
    except IndexError:
        mdd_begin_idx = None
    _ = cum_return_ps.loc[mdd_idx:]
    try:
        mdd_end_idx = _[_ >= mdd_max_level].index[0]
    except IndexError:
        mdd_end_idx = None
    if return_drawdown_period:
        return mdd_ts, (mdd_begin_idx, mdd_end_idx)
    else:
        return mdd_ts


def max_drawdown(capital_line, interest_type='SIMPLE'):
    # return max draw down in decimal
    cline_e = pd.DataFrame(np.maximum.accumulate(capital_line) - capital_line)
    mdd_end = cline_e.idxmax().loc[0]
    # mdd_end = np.argmax(np.maximum.accumulate(capital_line) - capital_line)
    if mdd_end == 0:
        return np.nan
    cline_s = pd.DataFrame(capital_line[:mdd_end])
    mdd_start = cline_s.idxmax().loc[0]
    # mdd_start = np.argmax(capital_line[:mdd_end])
    if interest_type == 'SIMPLE':
        mdd = capital_line[mdd_start] - capital_line[mdd_end]
    else:
        mdd = 1 - capital_line[mdd_end] / capital_line[mdd_start]
    return -mdd


def compute_calmar_ratio_half_year(excess_return):
    year_list = np.unique(excess_return.index.year.tolist())
    half_year_list = []
    for year in year_list:
        half_year_list.append(str(year) + '0701')
        half_year_list.append(str(year) + '1231')

    calmar_ratio = {}
    for idx, half in enumerate(half_year_list):
        if idx == 0:
            sub_part_ret = excess_return[:half]
        else:
            sub_part_ret = excess_return[half_year_list[idx - 1]:half]
        if len(sub_part_ret.dropna()):
            sub_part_ret = sub_part_ret.dropna()
            nav = (1. + sub_part_ret).cumprod()
            calmar = sub_part_ret.mean() / np.abs(max_drawdown(nav))
            calmar_ratio[half] = calmar
    if len(calmar_ratio):
        calmar_ratio = pd.Series(calmar_ratio).to_frame()
        calmar_ratio.columns = ['calmar_ratio']
        return calmar_ratio
    else:
        return np.nan


def exret_calmar_ratio_half_year_calc(excess_return):
    """

    :param excess_return:
    :return:
    """
    return compute_calmar_ratio_half_year(excess_return=excess_return)


def exret_sampling_stat_calc(excess_return, in_sample=True, random_state=0, bootstrap_steps=9,
                             experiment_steps=10):
    """

    :param excess_return:
    :param in_sample:
    :param random_state:
    :param bootstrap_steps:
    :param experiment_steps:
    :return:
    """
    return compute_sampling_ret_stat(excess_return=excess_return, in_sample=in_sample, random_state=random_state,
                                     bootstrap_steps=bootstrap_steps, experiment_steps=experiment_steps)


def calc_percentile(ts):
    #计算分位数，当天在最近20日中的排名
    pctrank = lambda x: pd.Series(x).rank(pct=True).iloc[-1]
    # 加上raw=False 取消FutureWarning
    # ts.expanding(20).apply(pctrank)
    return ts.expanding(20).apply(pctrank, raw=False)


def get_excess_return(factor_df, price_use='vwap', top_range=0.1, transaction_cost=4e-4):
    start_date = factor_df.index[0]
    end_date = factor_df.index[-1]
    dm = DataManager(start_date=start_date, end_date=end_date)
    from datetime import datetime as dt
    factor_df.index = [dt.strptime(x, '%Y%m%d') for x in factor_df.index]

    if price_use == 'vwap':
        re_1d = dm.get_holding_period_ret_data(price_use=price_use, universe='alpha_universe', holding_period=1,
                                               ret_shift=True, seg_benchmark='alpha_universe')
    elif price_use == 'close':
        re_1d = dm.get_holding_period_ret_data(price_use=price_use, universe='alpha_universe', holding_period=1,
                                               ret_shift=False, seg_benchmark='alpha_universe')
    else:
        raise Exception("price_use仅支持 vwap, close")

    excess_return = re_1d.subtract(re_1d.mean(axis=1), axis=0)

    industry_data = dm.get_industry_data(universe='alpha_universe')
    size_data = dm.get_size_data(universe='alpha_universe')
    data_dict = {'factor_df': factor_df, 'industry': industry_data, 'size': size_data, 'excess_return': excess_return}
    #factor_df = factor_df[is_valid01]
    data_dict = align_data_inner(data_dict)
    factor_df = data_dict['factor_df']
    neutral_dict_df = {'Industry': data_dict['industry'],  'Size': data_dict['size']}
    excess_return = data_dict['excess_return']
    factor_df, r2, _, _ = regression_ols(y=factor_df, x=neutral_dict_df)

    update_date_list_end = factor_df.index[-2]
    factor_ranker_pct_descending = factor_df.rank(pct=True, axis=1, method='first', ascending=False)

    wi_descending_01 = ((factor_ranker_pct_descending <= top_range) * 1).fillna(0)
    wi_descending = wi_descending_01

    wi_turnover = (wi_descending - wi_descending.shift(1)).applymap(abs) / 2
    turnover_rate = wi_turnover.sum(axis=1) / wi_descending.sum(axis=1)
    turnover_rate[np.isinf(turnover_rate)] = np.nan

    wi_descending = wi_descending.divide(wi_descending.sum(axis=1), axis=0)

    ########################
    excess_descending = ((wi_descending * excess_return).sum(axis=1))[start_date:update_date_list_end]
    excess_descending = excess_descending - transaction_cost * turnover_rate

    save_factor_excess = excess_descending.to_frame()
    save_factor_excess.columns = ['excess_return']
    return save_factor_excess[start_date:end_date]


def sample_random(excess, random_state, bootstrap_steps):
    """

    :param excess:
    :param random_state:
    :param bootstrap_steps:
    :return:
    """
    from sklearn.model_selection import train_test_split
    # sample containing two parts
    # part 1: 10% of the sample
    sample_10, sample_90 = train_test_split(excess, test_size=1 - 1 / (bootstrap_steps + 1),
                                            random_state=random_state)
    # part 2:bootstrap sampling of the rest 90%
    excess_sample = sample_10.tolist()
    for i in range(bootstrap_steps):
        sample_new = sample_90.sample(n=len(sample_10), replace=True, random_state=random_state).tolist()
        excess_sample += sample_new
        random_state += 10
    return pd.Series(excess_sample).mean()


def calc_sample_ret(excess, random_state=0, bootstrap_steps=9, experiment_steps=10):
    assert bootstrap_steps >= 1, "bootstrap_steps must be >= 1"
    ret_diff = []  # record sample excess of each sample process

    for i in range(experiment_steps):
        ret_diff.append(
            sample_random(excess, random_state=random_state, bootstrap_steps=bootstrap_steps) * 1e4)
        random_state += 1
    ret_diff = pd.Series(ret_diff)
    ret_diff_mean = abs(ret_diff.mean())

    if ret_diff_mean == 0:
        return 0
    ret_diff_gap = ret_diff.nlargest(experiment_steps // 2).mean() - ret_diff.nsmallest(
        experiment_steps // 2).mean()
    ret_diff_value = ret_diff_gap / ret_diff_mean
    return ret_diff_value

