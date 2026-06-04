import numpy as np
import pandas as pd
import copy
import statsmodels.api as sm
import time

import os
from pathlib import Path
import json
import datetime as dt
import pickle
import tquant.strategy.day_factor_backtest.utility.dt as tdt
from tquant import tq_logger

def str_date_parser(str_name):
    '''
    --- DESCRIPTION ---
    Parse 'YYYMMMDD.xxx' styled string / file name to datetime object
    '''
    if any([isinstance(str_name, dt.date), isinstance(str_name, dt.datetime), isinstance(str_name, pd.Timestamp)]):
        return pd.Timestamp(str_name)
    if type(str_name) is int:
        str_name = str(str_name)
    if type(str_name) is str:
        if len(str_name) == 8:
            return pd.Timestamp(dt.datetime.strptime(str_name, '%Y%m%d'))
        elif len(str_name) == 14:
            return pd.Timestamp(dt.datetime.strptime(str_name, '%Y%m%d%H%M%S'))
        else:
            raise AssertionError
    else:
        raise AssertionError



def save_pickle(save_dict, save_path):
    with open(save_path, 'wb') as input:
        pickle.dump(save_dict, input, protocol=pickle.HIGHEST_PROTOCOL)
    return


def read_pickle(save_path):
    with open(save_path, 'rb') as input:
        save_dict = pickle.load(input)
    return save_dict


def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func

    return decorate


@static_vars(tic=dt.datetime.now())
def pprint(*args, **kwargs):
    print(('%.3fs <- prev msg: ' % (dt.datetime.now() - pprint.tic).total_seconds()).rjust(22), *args, **kwargs)
    pprint.tic = dt.datetime.now()


def excel_saver(output_dict, excel_name):
    writer = pd.ExcelWriter(excel_name, engine='xlsxwriter')
    for key in output_dict:
        output_dict[key].to_excel(writer, sheet_name=key)
    writer.save()
    return


def get_turnover(factor_data):
    factor_rank = factor_data.rank(pct=True, axis=1, method='first', ascending=False)
    B = pd.DataFrame((factor_rank.values <= 0.1) * 1, index=factor_rank.index, columns=factor_rank.columns).fillna(
        0)
    C = pd.DataFrame(B.values - B.shift(1).values, index=B.index, columns=B.columns).applymap(abs) / 2
    turnover_rate = C.sum(axis=1) / B.sum(axis=1)
    ans = turnover_rate.mean()
    return ans


def max_drawdown(capital_line, interest_type='SIMPLE'):
    # return max draw down in decimal
    mdd_end = np.argmax(np.maximum.accumulate(capital_line) - capital_line)
    if mdd_end == 0:
        return np.nan
    mdd_start = np.argmax(capital_line[:mdd_end])
    if interest_type == 'SIMPLE':
        mdd = capital_line[mdd_start] - capital_line[mdd_end]
    else:
        mdd = 1 - capital_line[mdd_end] / capital_line[mdd_start]
    return -mdd



def quantile_ic(factor_score, holding_period_return, down_lim, up_lim):
    # measure factor ic within range quantiles with positive factor sign
    gap = int(min(1, len(factor_score) / 100))
    ic_sign = np.sign(factor_score.iloc[::gap].corrwith(holding_period_return.iloc[::gap], axis=1).mean())
    factor_score = ic_sign * factor_score
    upper_bound = factor_score.subtract(factor_score.quantile(up_lim, axis=1), axis=0) <= 0
    lower_bound = factor_score.subtract(factor_score.quantile(down_lim, axis=1), axis=0) >= 0
    return ic_sign * factor_score[upper_bound & lower_bound].corrwith(holding_period_return, axis=1)


def winsorized_mean(x, cut_range=(3, 97)):
    x = np.ma.masked_invalid(x)
    x = x.data[~x.mask]
    l_b = np.percentile(x, cut_range[0])
    u_b = np.percentile(x, cut_range[1])
    return np.mean(x[(x >= l_b) & (x <= u_b)])


def multi_index_to_dataframe(h5_data):
    data_dict = {}
    for factor in h5_data.columns:
        data_dict[factor] = h5_data[factor].unstack()
    return data_dict




def cal_hpr_daily(stock_close_pd, holding_period):
    holding_period_ret = stock_close_pd.shift(-1 * holding_period) / stock_close_pd - 1
    holding_period_ret_daily = (holding_period_ret + 1) ** (1 / holding_period) - 1
    return holding_period_ret_daily


def align_data_inner(data_dict):
    # maybe should use dt, Ticker instead
    i = 0
    for factor in data_dict:
        #SJL
        try:
            tq_logger.debug("factor: {}, isMultiIndex: {}, date_list: {}.".format(factor, isinstance(data_dict[factor].index, pd.core.index.MultiIndex), len(date_list)))
        except Exception as e:
            tq_logger.debug(factor+": shape error!")
            tq_logger.debug(e)
        if np.any([isinstance(data_dict[factor], _type) for _type in [pd.DataFrame, pd.Series]]):
            #找股票和日期的最小集合（并集）
            if isinstance(data_dict[factor].index, pd.core.index.MultiIndex):
                if 'dt' in data_dict[factor].index.names:
                    if i == 0:
                        date_list = list(set(data_dict[factor].index.get_level_values(level=0).tolist()))
                        i = i + 1
                    else:
                        date_list = np.intersect1d(date_list, list(
                            set(data_dict[factor].index.get_level_values(level=0).tolist())))
            else:
                if type(data_dict[factor]) == pd.DataFrame:
                    if i == 0:
                        stock_list = data_dict[factor].columns.tolist()
                        date_list = data_dict[factor].index.tolist()
                        i = i + 1
                    else:
                        stock_list = np.intersect1d(stock_list, data_dict[factor].columns.tolist())
                        date_list = np.intersect1d(date_list, data_dict[factor].index.tolist())
                else:  # Series
                    if i == 0:
                        date_list = data_dict[factor].index.tolist()
                        i = i + 1
                    else:
                        date_list = np.intersect1d(date_list, data_dict[factor].index.tolist())
        elif type(data_dict[factor]) == dict:
            for nested_factor in data_dict[factor]:
                if type(data_dict[factor][nested_factor]) == pd.DataFrame:
                    if i == 0:
                        stock_list = data_dict[factor][nested_factor].columns.tolist()
                        date_list = data_dict[factor][nested_factor].index.tolist()
                        i = i + 1
                    else:
                        stock_list = np.intersect1d(stock_list, data_dict[factor][nested_factor].columns.tolist())
                        date_list = np.intersect1d(date_list, data_dict[factor][nested_factor].index.tolist())
        else:
            continue
    data_dict_aligned = {}
    for factor in data_dict:
        if np.any([isinstance(data_dict[factor], _type) for _type in [pd.DataFrame, pd.Series]]):
            if isinstance(data_dict[factor].index, pd.core.index.MultiIndex):
                if 'dt' in data_dict[factor].index.names:
                    data_dict_aligned[factor] = data_dict[factor].loc[date_list]
            else:
                if type(data_dict[factor]) == pd.DataFrame:
                    data_dict_aligned[factor] = data_dict[factor].loc[date_list, stock_list]
                else:
                    data_dict_aligned[factor] = data_dict[factor].loc[date_list]
        elif type(data_dict[factor]) == dict:
            data_dict_aligned[factor] = {}
            for nested_factor in data_dict[factor]:
                if type(data_dict[factor][nested_factor]) == pd.DataFrame:
                    data_dict_aligned[factor][nested_factor] = data_dict[factor][nested_factor].loc[
                        date_list, stock_list]
    return data_dict_aligned


def union(a, b):
    """ return the union of two lists """
    return list(set(a) | set(b))


def align_data_outer(data_dict):
    # maybe should use dt, Ticker instead
    i = 0
    for factor in data_dict:
        if np.any([isinstance(data_dict[factor], _type) for _type in [pd.DataFrame, pd.Series]]):
            if isinstance(data_dict[factor].index, pd.core.index.MultiIndex):
                if 'dt' in data_dict[factor].index.names:
                    if i == 0:
                        date_list = list(set(data_dict[factor].index.get_level_values(level=0).tolist()))
                        i = i + 1
                    else:
                        new_list = list(set(data_dict[factor].index.get_level_values(level=0).tolist()))
                        date_list = union(date_list, new_list)
            else:
                if type(data_dict[factor]) == pd.DataFrame:
                    if i == 0:
                        stock_list = data_dict[factor].columns.tolist()
                        date_list = data_dict[factor].index.tolist()
                        i = i + 1
                    else:
                        # stock_list = np.intersect1d(stock_list, data_dict[factor].columns.tolist())
                        # date_list = np.intersect1d(date_list, data_dict[factor].index.tolist())
                        stock_list = union(stock_list, data_dict[factor].columns.tolist())
                        date_list = union(date_list, data_dict[factor].index.tolist())

                else:  # Series
                    if i == 0:
                        date_list = data_dict[factor].index.tolist()
                        i = i + 1
                    else:
                        date_list = union(date_list, data_dict[factor].index.tolist())
        elif type(data_dict[factor]) == dict:
            for nested_factor in data_dict[factor]:
                if type(data_dict[factor][nested_factor]) == pd.DataFrame:
                    if i == 0:
                        stock_list = data_dict[factor][nested_factor].columns.tolist()
                        date_list = data_dict[factor][nested_factor].index.tolist()
                        i = i + 1
                    else:
                        stock_list = union(stock_list, data_dict[factor][nested_factor].columns.tolist())
                        date_list = union(date_list, data_dict[factor][nested_factor].index.tolist())
        else:
            continue
    date_list.sort()
    stock_list.sort()
    data_dict_aligned = {}
    for factor in data_dict:
        if np.any([isinstance(data_dict[factor], _type) for _type in [pd.DataFrame, pd.Series]]):
            if isinstance(data_dict[factor].index, pd.core.index.MultiIndex):
                if 'dt' in data_dict[factor].index.names:
                    # data_dict_aligned[factor] = data_dict[factor].loc[date_list]
                    data_dict_aligned[factor] = data_dict[factor].reindex(index=date_list)

            else:
                if type(data_dict[factor]) == pd.DataFrame:
                    # data_dict_aligned[factor] = data_dict[factor].loc[date_list, stock_list]
                    data_dict_aligned[factor] = data_dict[factor].reindex(index=date_list, columns=stock_list)
                else:
                    # data_dict_aligned[factor] = data_dict[factor].loc[date_list]
                    data_dict_aligned[factor] = data_dict[factor].reindex(index=date_list)
        elif type(data_dict[factor]) == dict:
            data_dict_aligned[factor] = {}
            for nested_factor in data_dict[factor]:
                if type(data_dict[factor][nested_factor]) == pd.DataFrame:
                    # data_dict_aligned[factor][nested_factor] = data_dict[factor][nested_factor].loc[date_list, stock_list]
                    data_dict_aligned[factor][nested_factor] = data_dict[factor][nested_factor].reindex(index=date_list,
                                                                                                        columns=stock_list)
    return data_dict_aligned


def box_skew_algo(x):
    #根绝上下四分位数去极值
    #箱型图，若中位数小于均值，认为是下偏斜（skew）；或者中位数靠近下四分位数，认为是下偏斜
    y = np.array(x)
    x = y[~np.isnan(y)]
    if len(np.unique(x)) < 10:
        return y
    x = np.sort(x)#从小到大
    md = np.median(x)
    q3 = np.percentile(x, 75)
    q1 = np.percentile(x, 25)
    iqr = q3 - q1
    rx = np.flip(x, axis=0)#行的顺序颠倒，从大到小
    x, rx = zip(*[(i, j) for i, j in zip(x, rx) if i != j])
    x = np.split(np.array(x), 2)[1]#split(ary, indices_or_sections, axis=0) :把一个数组从左到右按顺序切分
    rx = np.split(np.array(rx), 2)[1]
    if len(x) < 5:
        return y
    mc = np.median((x + rx - 2.0 * md) / (x - rx))
    a, b = (3.5, 4.0) if mc >= 0 else (4.0, 3.5)
    L = q1 - 1.5 * np.exp(-a * mc) * iqr#调整后的下四分位数
    U = q3 + 1.5 * np.exp(b * mc) * iqr
    y[np.array([item < L if not np.isnan(item) else False for item in y])] = L
    y[np.array([item > U if not np.isnan(item) else False for item in y])] = U
    return y


def BoxSkewPlot(pd_raw, axis=1):
    if type(pd_raw) == pd.DataFrame:
        pd_process = pd_raw.copy()
        return pd_process.apply(box_skew_algo, axis=axis)
    else:
        raise AssertionError


def norm_winsor(factor_pd, bound=3, winsor=False):
    factor_pd = factor_pd.copy()
    factor_pd = median_filter(factor_pd, mad=bound, winsor=winsor, inplace=True)
    std_ts = factor_pd.std(axis=1, ddof=0)
    std_ts.loc[std_ts == 0] = 1
    factor_pd = factor_pd.subtract(factor_pd.mean(axis=1), axis=0).divide(std_ts, axis=0)
    return factor_pd


def median_filter(factor_pd, mad=3, winsor=False, inplace=False):
    if not inplace:
        factor_pd = factor_pd.copy()
    dm = factor_pd.median(axis=1)
    # caution of symmetric uppper & lower bounds
    dist_dm = (factor_pd.subtract(dm, axis=0)).abs().median(axis=1)
    date_num, stock_num = factor_pd.shape
    fac_ub = pd.DataFrame(np.tile(dm + mad * dist_dm, [stock_num, 1]).T, index=factor_pd.index,
                          columns=factor_pd.columns)
    fac_lb = pd.DataFrame(np.tile(dm - mad * dist_dm, [stock_num, 1]).T, index=factor_pd.index,
                          columns=factor_pd.columns)
    if winsor:
        factor_pd[factor_pd > fac_ub] = np.nan
        factor_pd[factor_pd < fac_lb] = np.nan
    else:
        factor_pd[factor_pd > fac_ub] = fac_ub
        factor_pd[factor_pd < fac_lb] = fac_lb
    return factor_pd


def regression_ols(y, x):
    # calculate ols problem given y as DataFrame and x as dictionary with DataFrames of regressors
    assert (isinstance(x, dict))
    date_num, stock_num = y.shape
    x_list = list(x.keys())
    contains_industry = True if 'Industry' in x_list else False
    x_num = len(x_list) - 1 if contains_industry else len(x_list)
    x_mat = np.ones([x_num, date_num, stock_num])
    y_mat = np.array(y)
    r2_mat = np.empty(date_num)
    r2_mat[:] = np.nan
    beta_mat = np.empty([date_num, x_num + 1])
    beta_mat[:] = np.nan
    tstats_mat = beta_mat.copy()
    res_mat = np.full_like(y, np.nan, dtype=np.double)

    if contains_industry:
        ind_mat = np.array(x['Industry'])
        x_list.remove('Industry')
    i = 0
    for x_name in x_list:
        x_mat[i, :, :] = np.array(x[x_name])
        i = i + 1

    for date_idx in range(date_num):
        if contains_industry:
            ind_dum = pd.get_dummies(ind_mat[date_idx, :]).values
            _x = np.column_stack([x_mat[:, date_idx, :].T, ind_dum])
        else:
            _x = x_mat[:, date_idx, :].T
        try:
            res_mat[date_idx, :], r2_mat[date_idx], beta_mat[date_idx, :], tstats_mat[date_idx, :] = stats_model_ols(
                y_mat[date_idx, :], _x)
        except ValueError:
            pass

    res = pd.DataFrame(res_mat, columns=y.columns, index=y.index)
    r2 = pd.Series(r2_mat, index=y.index)
    beta = pd.DataFrame(beta_mat, columns=['intercept'] + x_list, index=y.index)
    tstats = pd.DataFrame(tstats_mat, columns=['intercept'] + x_list, index=y.index)
    return res, r2, beta, tstats


def stats_model_ols(y, x, min_percentage=20):
    res = np.full_like(y, np.nan, dtype=np.double)
    mask = np.isfinite(y + x.sum(axis=1))
    if np.count_nonzero(mask) / len(mask) * 100 < min_percentage:
        raise ValueError
    ols = resider(x[mask], y[mask], method='sm.OLS', add_const=True, mean_only=False, r_square=False, return_sm=True)
    res[mask] = ols.resid
    return res, ols.rsquared, ols.params, ols.tvalues


def resider(x, y, method='lstsq', add_const=True, mean_only=False, r_square=False, return_sm=False):
    # Two step regression
    # 1: Determine dummy columns in matrix and use them to remove mean
    # 2: Regular ols: OLS or least square to calculate residual
    # Direct OLS or least square may have problems with dummy columns with few 1s
    # Less computation and more robustness
    # x -> axis0: stocks, axis1: factors
    y = y.flatten()  # 1-D array
    dummy_cols = np.apply_along_axis(is_dummy, 0, x)
    d_array = x[:, dummy_cols]
    s_array = x[:, ~dummy_cols]
    r2 = np.nan
    if d_array.shape[1] != 0:
        d_mean_array = np.array([i / j if j != 0 else 0 for i, j in
                                 zip(np.dot(d_array.T, y).flatten(), d_array.sum(axis=0))])
        y = y - np.dot(d_array, d_mean_array)
    if not mean_only and s_array.shape[1] != 0:
        if method == 'lstsq':
            if add_const:
                # Prepend constant in accordance with sm.OLS
                x = np.concatenate((np.ones((s_array.shape[0], 1)), s_array), axis=1)
            else:
                x = s_array
            try:
                coeff, residual_sum = np.linalg.lstsq(x, y, rcond=None)[0:2]
                resid = y - np.dot(x, coeff)
                if r_square:
                    r2 = 1 - residual_sum[0] / (y.size * y.var())
            except:
                resid = np.full_like(y, np.nan, dtype=np.double)
        elif method == 'sm.OLS':
            import statsmodels.api as sm
            x = s_array
            try:
                if add_const:
                    ols_problem = sm.OLS(y, sm.add_constant(x)).fit()
                else:
                    ols_problem = sm.OLS(y, x).fit()
                if return_sm:
                    return ols_problem
                resid = ols_problem.resid
                if r_square:
                    r2 = ols_problem.rsquared
            except:
                #抛异常时，会报错AttributeError: 'numpy.ndarray' object has no attribute 'resid'
                resid = np.full_like(y, np.nan, dtype=np.double)
        else:
            raise AssertionError
    else:
        resid = y
    if r_square:
        return resid, r2
    else:
        return resid


def is_dummy(x):
    x = np.array(x) if not isinstance(x, np.ndarray) else x
    one_num = np.count_nonzero(x == 1)
    zero_num = np.count_nonzero(x == 0)
    if one_num + zero_num == x.size:
        return True
    else:
        return False


def factor_fillna_industry(pd_raw, stock_filter, stock_industry, inplace=False):
    # all inputs are in shape of DataFrame: dates, stocks
    # np.nans in pd_raw which are "True" in stock_filter are filled by industry calc_ic_by_industry
    # median
    if not inplace:
        pd_raw = pd_raw.copy().astype(np.float64)
    fill_indicator = np.isnan(pd_raw) & (stock_filter == True)#FactorBacktest中已处理，factor_data和stock_filter形状一致
    industry_universe = [float(i + 1) for i in range(int(stock_industry.max().max()))]
    industry_median = pd.DataFrame(index=pd_raw.index, columns=industry_universe, dtype=np.float64)
    for row in stock_industry.itertuples():
        date = row[0]
        industry_list = row[1:]

        #修复行业中位数计算bug
        # tmp_series = copy.copy(pd_raw.loc[date])
        # tmp_series.index = industry_list
        # industry_median.loc[date] = tmp_series.groupby(tmp_series.index).median()

        df_p = copy.copy(pd.DataFrame(pd_raw.loc[date]))
        df_p.reset_index(inplace=True)
        df_p['industry'] = stock_industry.loc[date, :]

        industry_median.loc[date] = df_p.groupby('industry')[date].median()

    stock_number = pd_raw.shape[1]
    for ind in industry_universe:
        pass
        # pd_raw[(stock_industry == ind)].dropna(axis=1, how = 'all') = np.tile(industry_median[ind], (stock_number, 1)).T#?
    if not inplace:
        return pd_raw


def calc_ic_by_industry(factor_score, hpr, stock_industry, ic_type='original'):
    ind_num = int(stock_industry.max().max())
    ic_list = list()
    for ind in range(1, ind_num + 1):
        ind_mask = stock_industry == ind
        _ = calc_factor_ic(factor_score[ind_mask], hpr, ic_type, min_pct=0)
        _.name = ind
        ic_list.append(_)
    return pd.concat(ic_list, axis=1)


def calc_corr(factor_pd, style_dict):
    assert isinstance(factor_pd, pd.DataFrame)
    assert isinstance(style_dict, dict)
    corr_list = list()
    for style in style_dict:
        _ = factor_pd.corrwith(style_dict[style], axis=1)
        _.name = style
        corr_list.append(_)
    return pd.concat(corr_list, axis=1)


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


def calc_year_date_num(ps_raw):
    predefined_num = 252
    if isinstance(ps_raw, np.ndarray):
        return predefined_num
    year_list = list(ps_raw.index.year.unique())
    date_num_list = list()
    try:
        for year in year_list:
            year_date_num = len(tdt.get_trading_date_range(dt.datetime(year=int(year), month=1, day=1),
                                                           dt.datetime(year=int(year), month=12, day=31)))
            date_num_list.append(year_date_num)
    except OSError:
        print('Cannot Retrieve Calendar Data')
        return predefined_num
    return np.mean(date_num_list)


# def segment_performance_measure(seg_return, interest_type='SIMPLE'):
#     # eat segment return results
#     _seg_return = seg_return.drop(['Index'], axis=1).dropna(how='all')
#     if len(_seg_return) == 0:
#         return pd.DataFrame()

#     seg_return = seg_return.loc[np.isfinite(seg_return).all(axis=1)]
#     date_1yr = calc_year_date_num(seg_return)
#     seg_return_cum = calc_cum_return_ts(seg_return, interest_type=interest_type)
#     mdd = pd.DataFrame(list(map(max_drawdown, seg_return_cum.T.values,
#                                 [interest_type] * len(seg_return_cum.columns))), index=seg_return_cum.columns)
#     ret_annual = calc_annualized_return(seg_return, interest_type=interest_type)
#     seg_ls_col = [col for col in seg_return.columns.tolist() if col.find('-') > 0]
#     ret_excess_annual = ret_annual - ret_annual['Index']
#     ret_excess_annual[seg_ls_col] = ret_annual[seg_ls_col]
#     # _seg_return = seg_return[::holding_period]
#     _seg_return = seg_return.dropna(how='all')
#     ret_excess = _seg_return.subtract(_seg_return['Index'], axis=0)
#     ret_excess[seg_ls_col] = _seg_return[seg_ls_col]
#     vol_annual = _seg_return.std() * np.sqrt(date_1yr)
#     tracking_error = ret_excess.std(axis=0) * np.sqrt(date_1yr)
#     sharpe_ratio = ret_annual / vol_annual
#     info_ratio = ret_excess_annual / tracking_error
#     ret_excess_cum = calc_cum_return_ts(ret_excess, interest_type=interest_type)
#     mdd_er = pd.DataFrame(list(map(max_drawdown, ret_excess_cum.T.values,
#                                   [interest_type] * len(ret_excess_cum.columns))), index=ret_excess_cum.columns)
#     hit_rate_er = (ret_excess.dropna() > 0).sum() / len(ret_excess.dropna())
#     hit_rate = (_seg_return.dropna() > 0).sum() / len(_seg_return.dropna())
#     # var_95 = ret_excess.quantile(q=0.05)
#     _segment_performance_measure = pd.concat([ret_annual, vol_annual, sharpe_ratio, mdd, hit_rate,
#                                               ret_excess_annual, tracking_error, info_ratio, mdd_er, hit_rate_er],
#                                              axis=1)
#     tr_list = ['Return(Ann.)', 'Vol(Ann.)', 'Sharpe', 'MDD', 'HitRate']
#     er_list = ['Excess Return', 'Tracking Error', 'IR', 'MDD_ER', 'HitRate_ER']
#     _segment_performance_measure.columns = tr_list + er_list
#     _segment_performance_measure.loc[[seg_ls_col[0], 'Index'], er_list] = np.nan
#     return _segment_performance_measure


############################################################
""" calculate ic """


def calc_mean_weighted_np(x, w):
    """Weighted Mean，加权平均"""
    return np.sum(x * w) / np.sum(w)


def calc_cov_weighted_np(x, y, w):
    """Weighted Covariance，加权协方差，Cov(X，Y)=E(X-E(X).*(y-E(Y)))"""
    return np.sum(w * (x - calc_mean_weighted_np(x, w)) * (y - calc_mean_weighted_np(y, w))) / np.sum(w)


def calc_corr_weighted_np(x, y, w):
    """Weighted Correlation 随机变量X和Y的(Pearson)加权相关系数， cov(X,Y)/sqrt(D(X))*sqrt(D(Y))"""
    return calc_cov_weighted_np(x, y, w) / np.sqrt(calc_cov_weighted_np(x, x, w) * calc_cov_weighted_np(y, y, w))


def calc_row_wrapper(func, x, y, w=None, output_format='Series', handle_nan=True, min_pct=0.1, verbose=False, **kwargs):
    #x为因子值，y为收益率，w为因子值排名，1到3000多
    x_mat = x.values
    y_mat = y.reindex(index=x.index, columns=x.columns).values
    if w is not None:
        w_mat = w.reindex(index=x.index, columns=x.columns).values
    row_num, col_num = x.shape
    min_num = int(min_pct * col_num)
    if output_format == 'Series':
        res_mat = x_mat.sum(axis=1)
        res_mat[:] = np.nan
    elif output_format == 'DataFrame':
        res_mat = x_mat
        res_mat[:] = np.nan
    for i in range(row_num):
        if verbose:
            print('%d/%d' % (i + 1, row_num))
        xr, yr = x_mat[i, :], y_mat[i, :]
        if w is not None:
            wr = w_mat[i, :]
            if handle_nan:
                mask = np.isfinite(xr + yr + wr)
                if np.count_nonzero(mask) >= min_num:
                    xr, yr, wr = xr[mask], yr[mask], wr[mask]
                    res_mat[i] = func(xr, yr, wr, **kwargs)  # put into row#计算加权pearson相关系数，即IC值
            else:
                res_mat[i] = func(xr, yr, wr, **kwargs)  #industry put into row
        else:
            if handle_nan:
                mask = np.isfinite(xr + yr)
                if np.count_nonzero(mask) >= min_num:
                    xr, yr = xr[mask], yr[mask]
                    res_mat[i] = func(xr, yr, **kwargs)  # put into row
            else:
                res_mat[i] = func(xr, yr, **kwargs)
    if output_format == 'Series':
        res = pd.Series(res_mat, index=x.index)
    elif output_format == 'DataFrame':
        res = pd.DataFrame(res_mat, index=x.index, columns=x.columns)
    return res


def weight_decay(half_life, total_len):
    """last one has highest weight , half life = time to reach 0.5, weight is normalized"""
    weight_list_raw = [0.5 ** ((total_len - i) / half_life) for i in range(total_len)]
    return weight_list_raw / np.sum(weight_list_raw)


def calc_corr_weighted(x, y, w, min_pct=0.1):
    return calc_row_wrapper(calc_corr_weighted_np, x, y, w, min_pct=min_pct, output_format='Series')


def calc_ic_score_weighted(factor, holding_period_return, min_pct=0.1, return_both=False):
    ic_orig = factor.corrwith(holding_period_return, axis=1)
    if ic_orig.mean() < 0:
        factor = -1 * factor
        ic_sign = -1
    else:
        ic_sign = 1
    ic_sw = ic_sign * calc_corr_weighted(factor, holding_period_return, factor.rank(axis=1), min_pct)
    if return_both:
        return ic_sw, ic_orig
    else:
        return ic_sw


def calc_factor_ic(factor, holding_period_return, ic_type='original', min_pct=0.1):
    if ic_type == 'original':
        ic_ts = factor.corrwith(holding_period_return, axis=1)
    elif ic_type == 'score_weighted':
        ic_ts = calc_ic_score_weighted(factor, holding_period_return, min_pct)
    return ic_ts


def calc_ic_full(factor_pd, stock_close, holding_period=10, fac_name=None, sign_correct=True):
    holding_period_ret = stock_close.shift(-1 * holding_period) / stock_close - 1
    ic_ts_list = []
    _ic_ts = pd.DataFrame(factor_pd.corrwith(holding_period_ret, axis=1), columns=['original'])
    if _ic_ts.mean().values[0] < 0 and sign_correct is True:
        factor_pd = -1 * factor_pd
        _ic_ts = -1 * _ic_ts
    ic_ts_list.append(_ic_ts)
    ic_type = 'return_rank'
    weight = holding_period_ret.rank(axis=1)
    ic_ts_list.append(pd.DataFrame(calc_corr_weighted(factor_pd, holding_period_ret, weight), columns=[ic_type]))

    ic_type = 'score_rank'
    weight = factor_pd.rank(axis=1)
    ic_ts_list.append(pd.DataFrame(calc_corr_weighted(factor_pd, holding_period_ret, weight), columns=[ic_type]))
    ic_ts = pd.concat(ic_ts_list, axis=1)
    if fac_name is not None:
        ic_ts = ic_ts.reset_index()
        ic_ts['factor'] = fac_name
        ic_ts = ic_ts.set_index(['dt', 'factor'])
    return ic_ts


def generate_seg_mask(factor_pd, q=0.2):
    """q big -> score big
       Q1 - high score
    """
    seg_num = int(1 / q)
    seg_list = [i * q for i in range(seg_num)] + [1]
    seg_list.sort(reverse=True)
    seg_mask = {}
    for i in range(seg_num):
        if i > 0:
            upper_bound = lower_bound.copy()  #
        else:
            upper_bound = factor_pd.quantile(q=seg_list[i], axis=1)
        lower_bound = factor_pd.quantile(q=seg_list[i + 1], axis=1)
        upper_mask = factor_pd.subtract(upper_bound, axis=0) <= 0
        lower_mask = factor_pd.subtract(lower_bound, axis=0) > 0
        seg_mask[i + 1] = upper_mask & lower_mask
    return seg_mask


def calc_segment_ic(factor_pd, holding_period_ret, q=0.2, sign_correct=False):
    if sign_correct:
        _ic_ts = pd.DataFrame(factor_pd.corrwith(holding_period_ret, axis=1))
        ic_sign = np.sign(_ic_ts.mean()).values[0]
        factor_pd = factor_pd * ic_sign
    seg_mask_dict = generate_seg_mask(factor_pd, q)
    _seg_ic_ts = [factor_pd[seg_mask_dict[i + 1]].corrwith(holding_period_ret, axis=1) for i in range(int(1 / q))]
    seg_ic_ts = pd.concat(_seg_ic_ts, axis=1)
    seg_ic_ts.columns = ['Q%d' % (i + 1) for i in range(int(1 / q))]
    return seg_ic_ts


def calc_ic(factor_pd, stock_close, holding_period=10, ic_type='original', weight=None, q=0.2, sign_correct=False):
    holding_period_ret = stock_close.shift(-1 * holding_period) / stock_close - 1
    if ic_type == 'original':
        ic_ts = pd.DataFrame(factor_pd.corrwith(holding_period_ret, axis=1), columns=[ic_type])
    elif ic_type == 'ret_positive':
        ret_mask = holding_period_ret > 0
        # top_half_ret = holding_period_ret.quantile(q=0.5,axis=1)
        ic_ts = pd.DataFrame(factor_pd.corrwith(holding_period_ret[ret_mask], axis=1), columns=[ic_type])
    elif ic_type == 'weighted':
        if weight is not None:
            ic_ts = pd.DataFrame(calc_corr_weighted(factor_pd, holding_period_ret, weight), columns=[ic_type])
        # ic_stats = calc_ic_stats(ic_ts)
    elif ic_type == 'seg_ic':
        ic_ts = calc_segment_ic(factor_pd, holding_period_ret, q, sign_correct)
    else:
        raise Exception
    if sign_correct and ic_type != 'seg_ic':
        _ic_ts = pd.DataFrame(factor_pd.corrwith(holding_period_ret, axis=1))
        ic_sign = np.sign(_ic_ts.mean()).values[0]
        ic_ts = ic_ts * ic_sign
    return ic_ts


def calc_market_rank(ret_ts, stock_return):
    """number smaller - ranked higher"""
    stk_cnt = np.isfinite(stock_return).sum(axis=1)
    ret_cnt = np.isfinite(ret_ts)
    underperformer = stock_return.subtract(ret_ts, axis=0) < 0
    underperformer_cnt = underperformer.sum(axis=1)
    market_rank = 1 - (underperformer_cnt / stk_cnt).reindex(index=ret_cnt[ret_cnt].index).reindex(index=ret_ts.index)
    return market_rank


def calc_ic_all(factor_pd, stock_close, holding_period, weight=None, fac_name=None,
                ic_type_list=['original', 'ret_positive', 'weighted', 'seg_ic'],
                q=0.2, sign_correct=False):
    ic_ts_list = []
    for ic_type in ic_type_list:
        _ic_ts = calc_ic(factor_pd, stock_close, holding_period=holding_period, ic_type=ic_type, weight=weight, q=q,
                         sign_correct=sign_correct)
        ic_ts_list.append(_ic_ts)
    ic_ts = pd.concat(ic_ts_list, axis=1)
    if fac_name is not None:
        ic_ts = ic_ts.reset_index()
        ic_ts['factor'] = fac_name
        ic_ts = ic_ts.set_index(['dt', 'factor'])
    return ic_ts


def calc_ic_dict(fac_dict, holding_period_ret, ic_type='original'):
    if ic_type == 'original':
        ic_df = pd.concat([fac_dict[key].corrwith(holding_period_ret, axis=1) for key in fac_dict], axis=1)
    elif ic_type == 'score_weighted':
        ic_df = pd.concat([calc_ic_score_weighted(fac_dict[key], holding_period_ret) for key in fac_dict], axis=1)
    ic_df.columns = list(fac_dict.keys())
    return ic_df


def calc_ts_corr(ts1, ts2, roll_win=60):
    ts_roll_corr = ts2.rolling(roll_win).corr(ts1).dropna()
    return ts_roll_corr


def calc_contextual_ic_helper(factor_pd, holding_period_ret, context_pd, seg_ic=0.5):
    context_mask = generate_seg_mask(context_pd, seg_ic)
    _seg_ic_ts = [factor_pd[context_mask[i + 1]].corrwith(holding_period_ret, axis=1) for i in range(int(1 / seg_ic))]
    seg_ic_ts = pd.concat(_seg_ic_ts, axis=1)
    seg_ic_ts.columns = ['Q%d' % (i + 1) for i in range(int(1 / seg_ic))]
    return seg_ic_ts


def calc_context_ic(factor_pd, stock_close, holding_period, context_dict, seg_ic=0.5, add_own=True):
    holding_period_ret = stock_close.shift(-1 * holding_period) / stock_close - 1
    rename_map = {'Q1': 'high', 'Q2': 'low'} if seg_ic == 0.5 else None
    cd = context_dict.copy()
    if isinstance(cd, pd.DataFrame):
        cd = {'context': cd}
    if add_own:
        cd['Factor'] = factor_pd
    if isinstance(cd, dict):
        context_list = list(cd.keys())
        if 'Industry' in context_list:
            context_list.remove('Industry')
        if 'Factor' in context_list:
            context_list.remove('Factor')
            context_list = ['Factor'] + context_list
        seg_ic_ts_list = [calc_contextual_ic_helper(factor_pd, holding_period_ret, cd[c], seg_ic) for c in context_list]
        seg_ic_ts = pd.concat(seg_ic_ts_list, axis=1).T
        seg_ic_ts.index.names = ['Level']
        if seg_ic == 0.5:
            seg_ic_ts = seg_ic_ts.rename(index=rename_map)
        col_list = []
        for i in context_list:
            col_list.append(i)
            col_list.append(i)
        seg_ic_ts['Context'] = col_list
        seg_ic_ts = seg_ic_ts.reset_index().set_index(['Context', 'Level']).T
    return seg_ic_ts


#########################################################################
def calc_percentile(ts):
    pctrank = lambda x: pd.Series(x).rank(pct=True).iloc[-1]
    return ts.expanding(20).apply(pctrank)


def calc_hhi(factor_pd, positive_only=True):
    pos_mask = factor_pd > 0
    if positive_only:
        fac = factor_pd[pos_mask].copy()
    else:
        fac = factor_pd.copy()
    fac_pct = fac.divide(fac.sum(axis=1), axis=0)
    use_mask = np.isfinite(fac_pct).sum(axis=1) > 0
    fac_hhi = ((fac_pct * 100) ** 2).sum(axis=1) / 100 ** 2
    fac_hhi[~use_mask] = np.nan
    return fac_hhi


def calc_filter_correlation_helper(xy, filter_x_middle=0.4, min_pct=0.8):
    #？
    # xy = np.stack([x, y], axis=1)
    xy_sorted = xy[xy[:, 0].argsort()]  # sort by factor score - small to large
    xy_mask = np.isfinite(xy_sorted.sum(axis=1))
    valid_cnt = np.count_nonzero(xy_mask)
    total_cnt = len(xy_sorted)
    cut = (1 - filter_x_middle) / 2
    if valid_cnt < int(min_pct * total_cnt):
        filter_corr = np.nan
    else:
        xy_valid = xy_sorted[xy_mask]
        idx_0, idx_1 = int(valid_cnt * cut), int((1 - cut) * valid_cnt)
        mid_mask = np.array([True for i in range(valid_cnt)])
        mid_mask[idx_0:idx_1] = False
        filter_corr = np.corrcoef(xy_valid[mid_mask], rowvar=False)[0, 1]
    return filter_corr


def calc_filter_correlation(xy_df, corr_win=240, filter_x_middle=0.4, min_pct=0.8):
    xy_mat = xy_df.values
    row_num, col_num = xy_df.shape
    filter_corr_mat = np.zeros(row_num)
    filter_corr_mat[:] = np.nan
    for i in range(corr_win, row_num):
        filter_corr_mat[i] = calc_filter_correlation_helper(xy_mat[i - corr_win + 1:i + 1], filter_x_middle, min_pct)
    filter_corr_ts = pd.Series(filter_corr_mat, index=xy_df.index)
    return filter_corr_ts


def find_er_ls_col(seg_ret):
    col_list = seg_ret.columns.tolist()
    q_list = [i for i in col_list if i.find('Q') >= 0 and i.find('-') == -1]
    er_col = [i for i in col_list if i.find('-') > 0][0]
    ret = seg_ret[q_list].mean()
    top_q, bottom_q = ret.idxmax(), ret.idxmin()
    return er_col, top_q, bottom_q


def generate_path(base_path, sub_folder_list):
    path_dict = {sub: os.path.join(base_path, str(sub)) for sub in sub_folder_list}
    [os.makedirs(path) if not os.path.exists(path) else None for path in list(path_dict.values()) + [base_path]]
    return path_dict


def multi_astype(pd_raw):
    y = pd_raw.reset_index()
    y.Ticker = y.Ticker.astype('category')
    y.set_index(['dt', 'Ticker'], append=False, inplace=True)
    y = y.sort_index(level=0)
    return y


def multi_astype_obj(pd_raw):
    y = pd_raw.reset_index()
    y.Ticker = y.Ticker.astype('object')
    y.set_index(['dt', 'Ticker'], append=False, inplace=True)
    y = y.sort_index(level=0)
    return y


def pd_unstack(pd_raw):
    if type(pd_raw) == pd.DataFrame:
        columns_lst = pd_raw.columns
    elif type(pd_raw) == pd.Series:
        columns_lst = []
    else:
        raise AssertionError
    if len(columns_lst) > 1:
        rtn = {}
        for item in columns_lst:
            rtn[item] = pd_raw[item].unstack()
    else:
        rtn = pd_raw.unstack()
    return rtn


def tracer(key):
    path = Path.home().joinpath('multifactor.json')
    counter = read_tracer(path)
    counter = auto_add(key, counter)
    set_tracer(path, counter)


def read_tracer(path):
    Path.touch(path)
    with open(path, 'r') as fin:
        try:
            counter = json.load(fin)
        except json.JSONDecodeError:
            counter = None
    return counter


def set_tracer(path, value):
    Path.touch(path)
    with open(path, 'w') as fout:
        json.dump(value, fout)


def auto_add(key, var):
    if var is None:
        var = dict()
    if key in var:
        var[key] += 1
    else:
        var[key] = 1
    return var
