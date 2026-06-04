import pandas as pd
import numpy as np
from tquant.strategy.day_factor_backtest.backtest.utility import winsorized_mean,cal_hpr_daily,calc_cum_return_ts,calc_annualized_return
from tquant.strategy.day_factor_backtest.backtest.utility import calc_year_date_num,max_drawdown


def segment_test_daily(factor_score, daily_return, segment_num,
                       handle_insufficient=False, handle_return_outlier=False, return_bucket_ic=False):
    factor_ret = np.stack([factor_score, daily_return], axis=1)
    factor_ret_sorted = factor_ret[factor_ret[:, 0].argsort()]  # sort by factor score - small to large
    valid_pair_num = np.count_nonzero(np.isfinite(factor_ret.sum(axis=1)))
    valid_factor_num = np.count_nonzero(np.isfinite(factor_ret[:, 0]))
    if valid_pair_num < segment_num:
        if handle_insufficient and valid_pair_num >= 1:
            if return_bucket_ic:
                return [np.nanmean(factor_ret_sorted[:, 1])] * segment_num, np.nan
            else:
                return [np.nanmean(factor_ret_sorted[:, 1])] * segment_num
        else:
            if return_bucket_ic:
                return [np.nan] * segment_num, np.nan
            else:
                return [np.nan] * segment_num
    #SJL
    # num_per_quantile = int(valid_factor_num / segment_num)
    num_per_quantile = int(valid_pair_num / segment_num)
    idx_seperators = np.arange(0, valid_pair_num, num_per_quantile) if segment_num > 1 else [0]
    idx_seperators = idx_seperators[:segment_num] if segment_num > 1 else [
        0]  # there may be stock left due to rounding error
    if handle_return_outlier:
        seg_ret_reversed = [winsorized_mean(factor_ret_sorted[i:i + num_per_quantile, 1]) for i in idx_seperators]
    else:
        seg_ret_reversed = [np.nanmean(factor_ret_sorted[i:i + num_per_quantile, 1]) for i in idx_seperators]
    # calculate bucket IC
    if return_bucket_ic:
        bucket_avg_factor_score = [np.nanmean(factor_ret_sorted[i:i + num_per_quantile, 0]) for i in idx_seperators]
        bucket_ic = np.corrcoef(seg_ret_reversed, bucket_avg_factor_score)[0, 1]
        return seg_ret_reversed, bucket_ic
    else:
        return seg_ret_reversed


def segment_test(factor_pd, stock_close_pd, holding_period, benchmark_price_ps, segment_num,
                 handle_insufficient=False, handle_return_outlier=False, return_bucket_ic=False,
                 transaction_cost=None, max_quantile=None):
    """
    factor_pd : 待测因子DataFrame
    stock_close_pd: 一段时间指定标的的收盘价
    benchmark_price_ps：基准价格DataFrame
    三者行列相同
    holding_period: 持有期（计算收益率）int
    segment_num ： 分层层数int
    handle_insufficient  ： 数据不足时的处理
    handle_return_outlier：是否处理异常数据
    transaction_cost ： 是否考虑交易成本
    return_bucket_ic ： 返回分层收益与因子均值的相关性
    max_quantile
    """
    # given matrix style factor and stock close prices, calculate benchmark return and factor sgement returns
    holding_period_ret = stock_close_pd.shift(-1 * holding_period) / stock_close_pd - 1
    benchmark_holding_period_ret = benchmark_price_ps.shift(-1 * holding_period) / benchmark_price_ps - 1
    holding_period_ret_daily = (holding_period_ret + 1) ** (1 / holding_period) - 1
    holding_period_ret_daily_mat = holding_period_ret_daily.values
    benchmark_holding_period_ret_daily = (benchmark_holding_period_ret + 1) ** (1 / holding_period) - 1
    factor_pd_mat = factor_pd.values
    date_num = factor_pd.shape[0]
    easy_seg_return_mat = np.empty([date_num, segment_num]) * np.nan
    bucket_ics = np.empty([date_num]) * np.nan

    for i in range(date_num):
        if return_bucket_ic:
            _seg_return, _bucket_ic = segment_test_daily(factor_pd_mat[i, :], holding_period_ret_daily_mat[i, :],
                                                         segment_num, handle_insufficient=handle_insufficient,
                                                         handle_return_outlier=handle_return_outlier,
                                                         return_bucket_ic=True)
            easy_seg_return_mat[i, :] = _seg_return
            bucket_ics[i] = _bucket_ic
        else:
            easy_seg_return_mat[i, :] = segment_test_daily(factor_pd_mat[i, :], holding_period_ret_daily_mat[i, :],
                                                           segment_num, handle_insufficient=handle_insufficient,
                                                           handle_return_outlier=handle_return_outlier)

    name_pool = ['Q' + str(segment_num - i) for i in range(int(segment_num))]
    easy_seg_return = pd.DataFrame(easy_seg_return_mat, columns=name_pool, index=factor_pd.index)
    name_pool_reversed = [item for item in reversed(name_pool)]
    easy_seg_return = easy_seg_return[name_pool_reversed]
    if transaction_cost is not None:
        turnover_ps = (1 - factor_pd.corrwith(factor_pd.shift(-holding_period), axis=1)) / holding_period
        turnover_ps = turnover_ps.fillna(0)  # handle only one stock
        easy_seg_return_after_cost = easy_seg_return.subtract(turnover_ps * transaction_cost, axis=0)
        easy_seg_return_after_cost['Index'] = benchmark_holding_period_ret_daily
        easy_seg_return_after_cost['Index'][~easy_seg_return_after_cost.any(axis=1)] = np.nan
        _ = easy_seg_return_after_cost[[name_pool[0], name_pool[-1]]].mean()
        max_quantile = _.idxmax() if max_quantile is None else max_quantile
        easy_seg_return_after_cost[max_quantile + '-' + 'Index'] = easy_seg_return_after_cost[max_quantile] - \
                                                                   easy_seg_return_after_cost['Index']
    easy_seg_return['Index'] = benchmark_holding_period_ret_daily
    easy_seg_return['Index'][~easy_seg_return.any(axis=1)] = np.nan
    _ = easy_seg_return[[name_pool[0], name_pool[-1]]].mean()
    max_quantile = _.idxmax() if max_quantile is None else max_quantile
    easy_seg_return[max_quantile + '-' + 'Index'] = easy_seg_return[max_quantile] - easy_seg_return['Index']
    if return_bucket_ic:
        bucket_ic_pd = pd.DataFrame(bucket_ics, index=factor_pd.index, columns=['Bucket %d IC' % segment_num])
        if transaction_cost is None:
            return easy_seg_return, bucket_ic_pd
        else:
            return easy_seg_return, easy_seg_return_after_cost, bucket_ic_pd
    else:
        if transaction_cost is None:
            return easy_seg_return
        else:
            return easy_seg_return, easy_seg_return_after_cost


def segment_test_by_industry(factor_pd, stock_close_pd, holding_period, benchmark_price_ps, segment_num,
                             stock_industry, industry_weight, handle_insufficient=True, transaction_cost=None,
                             return_industry=False, stock_weight=None, max_quantile=None):
    """
    :param factor_pd:
    :param stock_close_pd:
    :param holding_period:
    :param benchmark_price_ps:
    :param segment_num:
    :param stock_industry: DataFrame，每只票每天所属的行业
    :param industry_weight: 子行业权重，子行业所有票的市值占全市场市值的权重
    :param handle_insufficient:
    :param transaction_cost:
    :param return_industry:
    :param stock_weight: 股票权重，股票市值占全市场的权重
    :param max_quantile:
    :return:
    """
    #按行业分别求分层收益率，
    seg_return_by_industry, seg_return_by_industry_after_cost = [], []
    name_pool = ['Q' + str(i) for i in range(1, int(segment_num + 1))]
    col_selector = name_pool + ['Index']
    if return_industry:
        hpr_daily = cal_hpr_daily(stock_close_pd, holding_period)
        industry_hpr_daily = []
    industry_list = pd.Series(np.unique(stock_industry)).dropna()
    for idx in industry_list:
        # reduce the calculation dimension by dropping columns
        factor_filtered = factor_pd[stock_industry == idx].dropna(axis=1, how='all')
        _ = segment_test(factor_filtered,
                         stock_close_pd.reindex(columns=factor_filtered.columns),
                         holding_period, benchmark_price_ps,
                         segment_num, handle_insufficient,
                         transaction_cost=transaction_cost, max_quantile=max_quantile)
        if transaction_cost is None:
            seg_return = _
        else:
            seg_return, seg_return_after_cost = _[0], _[1]
        seg_return = seg_return[col_selector]
        seg_return['Industry'] = idx#12列，11列分层收益，一列行业
        # bie
        seg_return.index.name = 'dt'
        seg_return_by_industry.append(seg_return)

        if transaction_cost is not None:
            seg_return_after_cost = seg_return_after_cost[col_selector]
            seg_return_after_cost['Industry'] = idx
            # bie
            seg_return_after_cost.index.name = 'dt'
            seg_return_by_industry_after_cost.append(seg_return_after_cost)

        # if return_industry:
        hpr_ind = hpr_daily.reindex(columns=factor_filtered.columns)
        if stock_weight is not None:
            date_list_mask = np.isfinite(hpr_ind.mean(axis=1))
            stk_wght_ind = stock_weight.reindex(columns=factor_filtered.columns).dropna(axis=1, how='all')
            stk_wgt_sum = stk_wght_ind.sum(axis=1)
            stk_wgt_sum[stk_wgt_sum == 0] = np.nan
            stk_wght_ind = stk_wght_ind.divide(stk_wgt_sum, axis=0)
            hpr_ind_mean = (hpr_ind * stk_wght_ind).sum(axis=1)
            hpr_ind_mean[~date_list_mask] = np.nan
        else:
            hpr_ind_mean = hpr_ind.mean(axis=1)
        _industry_hpr_daily = pd.DataFrame(hpr_ind_mean, columns=['total_return'])
        _industry_hpr_daily['Industry'] = idx#两列，一列收益率，一列行业
        # bie
        _industry_hpr_daily.index.name = 'dt'
        industry_hpr_daily.append(_industry_hpr_daily)

    industry_hpr_daily = pd.concat(industry_hpr_daily, axis=0).reset_index().set_index(['dt', 'Industry'])#行业每天的收益率，行业中每只票加权求和，算作行业收益率
    industry_ret_weighted = industry_hpr_daily.multiply(industry_weight, axis=0).groupby('dt').sum()
    seg_return_combined = pd.concat(seg_return_by_industry, axis=0).reset_index().set_index(['dt', 'Industry'])#行业每天的分层收益
    res = seg_return_combined.multiply(industry_weight, axis=0).groupby('dt').sum()
    res['Index'] = industry_ret_weighted  # seg_return['Index']
    _ = res[[name_pool[0], name_pool[-1]]].mean()
    max_quantile = _.idxmax() if max_quantile is None else max_quantile
    res[max_quantile + '-' + 'Index'] = res[max_quantile] - res['Index']
    if transaction_cost is not None:
        seg_return_combined_after_cost = pd.concat(seg_return_by_industry_after_cost,
                                                   axis=0).reset_index().set_index(['dt', 'Industry'])
        res_after_cost = seg_return_combined_after_cost.multiply(industry_weight, axis=0).groupby('dt').sum()
        res_after_cost['Index'] = industry_ret_weighted  # seg_return_after_cost['Index']
        res_after_cost[max_quantile + '-' + 'Index'] = res_after_cost[max_quantile] - res_after_cost['Index']

    if return_industry:
        seg_return_combined[max_quantile + '-' + 'Index'] = seg_return_combined[max_quantile] - industry_hpr_daily[
            'total_return']
        if transaction_cost is None:
            return res, seg_return_combined
        else:
            seg_return_combined_after_cost[max_quantile + '-' + 'Index'] = seg_return_combined_after_cost[
                                                                               max_quantile] - industry_hpr_daily[
                                                                               'total_return']
            #combined 是包含行业明细的收益率值，索引为dt，industry双索引
            return res, res_after_cost, seg_return_combined, seg_return_combined_after_cost
    else:
        if transaction_cost is None:
            return res
        else:
            return res, res_after_cost


def segment_performance_measure(seg_return, interest_type='SIMPLE'):
    """
    :param seg_return: 行为日期，列为每层收益和超额收益
    :param interest_type:
    :return: 各层的收益指标：列为Return(Ann.) Vol(Ann.) Sharpe MDD HitRate Excess Return Tracking Error IR MDD_ER HitRate_ER
    """
    # eat segment return results
    _seg_return = seg_return.drop(['Index'], axis=1).dropna(how='all')
    if len(_seg_return) == 0:
        return pd.DataFrame()

    seg_return = seg_return.loc[np.isfinite(seg_return).all(axis=1)]
    date_1yr = calc_year_date_num(seg_return)
    seg_return_cum = calc_cum_return_ts(seg_return, interest_type=interest_type)
    mdd = pd.DataFrame(list(map(max_drawdown, seg_return_cum.T.values,
                                [interest_type] * len(seg_return_cum.columns))), index=seg_return_cum.columns)
    ret_annual = calc_annualized_return(seg_return, interest_type=interest_type)
    seg_ls_col = [col for col in seg_return.columns.tolist() if col.find('-') > 0]
    ret_excess_annual = ret_annual - ret_annual['Index']
    ret_excess_annual[seg_ls_col] = ret_annual[seg_ls_col]
    # _seg_return = seg_return[::holding_period]
    _seg_return = seg_return.dropna(how='all')
    ret_excess = _seg_return.subtract(_seg_return['Index'], axis=0)
    ret_excess[seg_ls_col] = _seg_return[seg_ls_col]
    vol_annual = _seg_return.std() * np.sqrt(date_1yr)
    tracking_error = ret_excess.std(axis=0) * np.sqrt(date_1yr)
    sharpe_ratio = ret_annual / vol_annual
    info_ratio = ret_excess_annual / tracking_error
    ret_excess_cum = calc_cum_return_ts(ret_excess, interest_type=interest_type)
    mdd_er = pd.DataFrame(list(map(max_drawdown, ret_excess_cum.T.values,
                                   [interest_type] * len(ret_excess_cum.columns))), index=ret_excess_cum.columns)
    hit_rate_er = (ret_excess.dropna() > 0).sum() / len(ret_excess.dropna())
    hit_rate = (_seg_return.dropna() > 0).sum() / len(_seg_return.dropna())
    # var_95 = ret_excess.quantile(q=0.05)
    _segment_performance_measure = pd.concat([ret_annual, vol_annual, sharpe_ratio, mdd, hit_rate,
                                              ret_excess_annual, tracking_error, info_ratio, mdd_er, hit_rate_er],
                                             axis=1)
    tr_list = ['Return(Ann.)', 'Vol(Ann.)', 'Sharpe', 'MDD', 'HitRate']
    er_list = ['Excess Return', 'Tracking Error', 'IR', 'MDD_ER', 'HitRate_ER']
    _segment_performance_measure.columns = tr_list + er_list
    _segment_performance_measure.loc[[seg_ls_col[0], 'Index'], er_list] = np.nan
    return _segment_performance_measure
