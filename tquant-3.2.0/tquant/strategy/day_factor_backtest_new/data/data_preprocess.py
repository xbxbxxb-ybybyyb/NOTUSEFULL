import numpy as np
import pandas as pd
import copy
from tquant.strategy.day_factor_backtest_new.util.utility import pprint
from tquant.strategy.day_factor_backtest_new.data.data_manager import DataManager

from tquant import tq_logger


def align_data_inner(data_dict):
    # maybe should use dt, Ticker instead
    i = 0
    for factor in data_dict:
        # SJL
        try:
            tq_logger.debug("factor: {}, isMultiIndex: {}, date_list: {}.".format(factor,
                                                                                  isinstance(data_dict[factor].index,
                                                                                             pd.core.index.MultiIndex),
                                                                                  len(date_list)))
        except Exception as e:
            tq_logger.debug(factor + ": shape error!")
            tq_logger.debug(e)
        if np.any([isinstance(data_dict[factor], _type) for _type in [pd.DataFrame, pd.Series]]):
            # 找股票和日期的最小集合（交集）
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


def factor_fillna_industry(factor_data, stock_filter, stock_industry, inplace=False):
    """

    :param factor_data:
    :param pd_raw:
    :param stock_filter:
    :param stock_industry:
    :param inplace:
    :return: 对用户开放 使用行业中位数填极值
    """
    # all inputs are in shape of DataFrame: dates, stocks
    # np.nans in pd_raw which are "True" in stock_filter are filled by industry median
    if not inplace:
        factor_data = factor_data.copy().astype(np.float64)
    fill_indicator = np.isnan(factor_data) & (stock_filter == True)
    industry_universe = [i + 1 for i in range(int(stock_industry.max().max()))]
    industry_median = pd.DataFrame(index=factor_data.index, columns=industry_universe, dtype=np.float64)
    for row in stock_industry.itertuples():
        date = row[0]
        # bie
        # industry_list = row[1:]
        df1 = pd.DataFrame(stock_industry.loc[date])
        stock_industry_dict = df1.to_dict()[date]

        df_p = copy.copy(pd.DataFrame(factor_data.loc[date]))
        df_p.reset_index(inplace=True)
        df_p['industry'] = df_p['Ticker'].apply(lambda x: stock_industry_dict[x])
        industry_median.loc[date] = df_p.groupby('industry')[date].median()

        # industry_median.loc[date] = pd_raw.loc[date].groupby(industry_list).median()
    stock_number = factor_data.shape[1]
    for ind in industry_universe:
        factor_data[(stock_industry == ind) & fill_indicator] = np.tile(industry_median[ind], (stock_number, 1)).T
    if not inplace:
        return factor_data


def box_skew_algo(x):
    # 根据上下四分位数去极值
    # 箱型图，若中位数小于均值，认为是下偏斜（skew）；或者中位数靠近下四分位数，认为是下偏斜
    y = np.array(x)
    x = y[~np.isnan(y)]
    if len(np.unique(x)) < 10:
        return y
    x = np.sort(x)  # 从小到大
    md = np.median(x)
    q3 = np.percentile(x, 75)
    q1 = np.percentile(x, 25)
    iqr = q3 - q1
    rx = np.flip(x, axis=0)  # 行的顺序颠倒，从大到小
    x, rx = zip(*[(i, j) for i, j in zip(x, rx) if i != j])
    x = np.split(np.array(x), 2)[1]  # split(ary, indices_or_sections, axis=0) :把一个数组从左到右按顺序切分
    rx = np.split(np.array(rx), 2)[1]
    if len(x) < 5:
        return y
    mc = np.median((x + rx - 2.0 * md) / (x - rx))
    a, b = (3.5, 4.0) if mc >= 0 else (4.0, 3.5)
    L = q1 - 1.5 * np.exp(-a * mc) * iqr  # 调整后的下四分位数
    U = q3 + 1.5 * np.exp(b * mc) * iqr
    y[np.array([item < L if not np.isnan(item) else False for item in y])] = L
    y[np.array([item > U if not np.isnan(item) else False for item in y])] = U
    return y


def BoxSkewPlot(factor_data, axis=1):
    """

    :param factor_data:
    :param axis:
    :return: 对用户开放 箱型线去极值的方法
    """
    if type(factor_data) == pd.DataFrame:
        pd_process = factor_data.copy()
        return pd_process.apply(box_skew_algo, axis=axis)
    else:
        raise AssertionError


def median_filter(factor_pd, mad=3, winsor=False, inplace=False):
    """
    :param factor_pd: 截面因子 pd.DataFrame
    :param mad:
    :param winsor: 是否使用winsor截尾
    :param inplace: 是否替换原数据
    :return: 对用户开放 中位数去极值的公共方法
    """
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


def standard_process(factor_data, stock_filter_df=None, stock_industry_df=None, fillna=False, median=False,
                     standard=False, boxskew=False):
    """

    :param factor_data:
    :param stock_filter_df:
    :param stock_industry_df:
    :param fillna: 是否按照行业中位数进行nan值填充
    :param median: 是否采用3sigema的方式去极值
    :param standard: 是否对数据进行标准化处理
    :param boxskew: 是否使用 箱线图去极值
    :return:
    """
    pprint('Data cleaning')
    if fillna:
        # 缺失值用行业中位数填充
        pprint('Fillna by industry')
        factor_data = factor_fillna_industry(factor_data, stock_filter=stock_filter_df,
                                             stock_industry=stock_industry_df)

    if boxskew:
        pprint('BoxSkewPlot processing')
        standardized_data = BoxSkewPlot(factor_data)
    else:
        standardized_data = factor_data

    pprint('Norm winsor processing')
    if median:
        bound = 3
        winsor = False
        factor_pd = standardized_data.copy()
        standardized_data = median_filter(factor_pd, mad=bound, winsor=winsor, inplace=True)
    if standard:
        std_ts = standardized_data.std(axis=1, ddof=0)
        std_ts.loc[std_ts == 0] = 1
        standardized_data = standardized_data.subtract(standardized_data.mean(axis=1), axis=0).divide(std_ts, axis=0)
    return factor_data, standardized_data


def is_dummy(x):
    x = np.array(x) if not isinstance(x, np.ndarray) else x
    one_num = np.count_nonzero(x == 1)
    zero_num = np.count_nonzero(x == 0)
    if one_num + zero_num == x.size:
        return True
    else:
        return False


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
                # 抛异常时，会报错AttributeError: 'numpy.ndarray' object has no attribute 'resid'
                resid = np.full_like(y, np.nan, dtype=np.double)
        else:
            raise AssertionError
    else:
        resid = y
    if r_square:
        return resid, r2
    else:
        return resid


def stats_model_ols(y, x, min_percentage=20):
    res = np.full_like(y, np.nan, dtype=np.double)
    mask = np.isfinite(y + x.sum(axis=1))
    if np.count_nonzero(mask) / len(mask) * 100 < min_percentage:
        raise ValueError
    ols = resider(x[mask], y[mask], method='sm.OLS', add_const=True, mean_only=False, r_square=False, return_sm=True)
    res[mask] = ols.resid
    return res, ols.rsquared, ols.params, ols.tvalues


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
                y_mat[date_idx, :], _x)  # res： 残差，r2： beta：线性回归系数， tstats：t值
        except ValueError:
            pass

    res = pd.DataFrame(res_mat, columns=y.columns, index=y.index)
    r2 = pd.Series(r2_mat, index=y.index)
    beta = pd.DataFrame(beta_mat, columns=['intercept'] + x_list, index=y.index)
    tstats = pd.DataFrame(tstats_mat, columns=['intercept'] + x_list, index=y.index)
    return res, r2, beta, tstats

