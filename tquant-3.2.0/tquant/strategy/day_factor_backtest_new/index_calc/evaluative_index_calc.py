import numpy as np
import pandas as pd
from tquant.strategy.day_factor_backtest_new.data.data_manager import DataManager


def calc_mean_weighted_np(x, w):
    """Weighted Mean，加权平均"""
    return np.sum(x * w) / np.sum(w)


def calc_cov_weighted_np(x, y, w):
    """Weighted Covariance，加权协方差，Cov(X，Y)=E(X-E(X).*(y-E(Y)))"""
    return np.sum(w * (x - calc_mean_weighted_np(x, w)) * (y - calc_mean_weighted_np(y, w))) / np.sum(w)


def calc_corr_weighted_np(x, y, w):
    """Weighted Correlation 随机变量X和Y的(Pearson)加权相关系数， cov(X,Y)/sqrt(D(X))*sqrt(D(Y))"""
    a = calc_cov_weighted_np(x, y, w)
    b = np.sqrt(calc_cov_weighted_np(x, x, w) * calc_cov_weighted_np(y, y, w))
    if b == 0:
        return np.nan
    else:
        return a / b


def calc_row_wrapper(func, x, y, w=None, output_format='Series', handle_nan=True, min_pct=0.1, verbose=False, **kwargs):
    # x为因子值，y为收益率，w为因子值排名，1到3000多
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
                res_mat[i] = func(xr, yr, wr, **kwargs)  # industry put into row
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


def get_prod_ret(df):
    # 获取累计收益
    df.fillna(value=0, inplace=True)
    data_dict = {}
    for i in df.columns:
        data_dict[i] = df[i].tolist()
    df1 = df.copy()
    for key in data_dict.keys():
        ll = [1 + j for j in data_dict[key]]
        df1.loc['prod', key] = np.prod(ll)
    return df1


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


def calc_factor_ic(factor_data, holding_period_return, ic_type='original', min_pct=0.1):
    if ic_type == 'original':
        ic_ts = factor_data.corrwith(holding_period_return, axis=1)
    elif ic_type == 'score_weighted':
        ic_ts = calc_ic_score_weighted(factor_data, holding_period_return, min_pct)
    return ic_ts


def calc_ic_stats(ic_ts):
    ic_ts = ic_ts.dropna()
    icir = ic_ts.mean() / ic_ts.std()
    hit_rate = (ic_ts > 0).sum() / len(ic_ts)
    ic_stats = pd.DataFrame([ic_ts.mean(), ic_ts.std(), icir, hit_rate])
    ic_stats.index = ['IC Mean', 'IC Std', 'ICIR', 'Hit Rate']
    return ic_stats


def alpha_decay_test(factor_data, holding_period_return, max_lag=5, holding_period=1, ic_type='original'):
    total_rebal = int(factor_data.shape[0] / holding_period)
    max_lag = total_rebal if max_lag > total_rebal else max_lag  # control for input error
    lag_list = [i * holding_period for i in range(max_lag)]  # max_lag决定IC偏移多少次
    IC_ts = np.empty([len(factor_data), len(lag_list)])
    for i in range(len(lag_list)):
        lag_ret = holding_period_return.shift(-1 * lag_list[i])  # 逐个holding_period计算收益率
        IC_ts[:, i] = calc_factor_ic(factor_data, lag_ret, ic_type)
    ic_decay = pd.DataFrame(np.nanmean(IC_ts, axis=0), index=lag_list, columns=['IC Decay'])  # 随着时间推移后的IC
    alpha_ts = calc_factor_ic(factor_data, holding_period_return, ic_type) * \
               holding_period_return.std(axis=1) / holding_period
    alpha_cumsum = pd.DataFrame(alpha_ts.cumsum(), columns=['Alpha (IC*Dispersion)'])  # 因子与收益的协方差除以因子的标准差乘以调仓周期 的 累加和
    return ic_decay, alpha_cumsum


def calc_ic_duration_test(factor_data, price_use_data, ic_type='original'):
    duration_list = [-5, -3, -1, 1, 3, 5, 10, 20]  # , 40, 60, 80, 100, 120]
    ret_dict = {}
    for i in duration_list:
        if i <= 0:
            # calculate gain
            ret_dict[i] = price_use_data / price_use_data.shift(-1 * i) - 1
        if i > 0:
            # calculate return
            ret_dict[i] = price_use_data.shift(-1 * i) / price_use_data - 1
    ic_ts = pd.DataFrame()
    for i in duration_list:
        ic_ts[i] = calc_factor_ic(factor_data, ret_dict[i], ic_type)
    lag_list_name = [str(i) + 'd' for i in duration_list]
    ic_duration = pd.DataFrame(np.nanmean(ic_ts, axis=0), index=lag_list_name, columns=['IC Duration'])
    return ic_duration


def calc_ic_by_industry(factor_score, hpr, stock_industry, ic_type='original'):
    ind_num = int(stock_industry.max().max())
    ic_list = list()
    for ind in range(1, ind_num + 1):
        ind_mask = stock_industry == ind
        _ = calc_factor_ic(factor_score[ind_mask], hpr, ic_type, min_pct=0)
        _.name = ind
        ic_list.append(_)
    return pd.concat(ic_list, axis=1)






