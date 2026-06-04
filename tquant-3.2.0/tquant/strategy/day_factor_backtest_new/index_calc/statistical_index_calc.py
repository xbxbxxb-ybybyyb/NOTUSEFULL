import numpy as np
import pandas as pd
import scipy.stats as sps

import numpy as np
import pandas as pd


def turnover_calc(factor_data):
    """
    :param factor_data: 截面因子形式的dataframe
    :return: 因子值每天 首尾10% 的平均变化率
    """
    factor_rank = factor_data.rank(pct=True, axis=1, method='first', ascending=False)
    # B中需要值作比较，原NAN值比较后最后为NAN填充为0，现在把factor_rank提前填充NAN值，且比较后结果为False，填充值大于0.1即可
    factor_rank.fillna(999999999, inplace=True)
    B = pd.DataFrame((factor_rank.values <= 0.1) * 1, index=factor_rank.index,
                     columns=factor_rank.columns)  # .fillna(0)
    C = pd.DataFrame(B.values - B.shift(1).values, index=B.index, columns=B.columns).applymap(abs) / 2
    turnover_rate = C.sum(axis=1) / B.sum(axis=1)
    ans = turnover_rate.mean()
    return ans


def summary_table(factor_data, factor_name=None, universe='alpha_universe', holding_period=1,
                              avg_turnover=None,
                              benchmark='alpha_universe', segment_number=10, standard=False, median=False, fillna=False,
                              seg_by_industry=False, transaction_cost=0, industry_type='CITIC_I',
                              interest_type='SIMPLE',
                              ic_type='score_weighted', compare_style='Size', ret_price='close', ret_shift=False):
    """

    :param factor_data: 截面因子形式的dataframe
    :param factor_name: 因子名称 str 默认为none
    :param universe:    股票池 str 默认为 alpha_universe
    :param holding_period: 调仓周期 int 默认为1
    :param avg_turnover:   平均转换率，float
    :param benchmark:  基准指数 str 默认为 alpha_universe
    :param segment_number: 分层层数 默认为 10层
    :param standard: 是否标准化，bool, 默认为False
    :param median:   是否中位数去极值，bool, 默认为False
    :param fillna:   是否填充nan值，bool, 默认为False
    :param seg_by_industry: 是否按行业分层 ，bool, 默认为False
    :param transaction_cost: 交易成本 默认为0
    :param industry_type:  行业分类标准, 'CITIC' 仅支持中信行业分类
    :param ic_type:  计算ic的方法
    :param compare_style:
    :param interest_type:
    :param ret_price: 计算收益的行情因子，str, 默认为'cloes'
    :param ret_shift: 收益是否偏移一天， bool ， 默认为False
    :return: pd.dataframe 对所传参数进行一个统计，化成表格在回测报告中进行展示，本身不涉及计算问题。
    """
    factor_date_list = factor_data.index.tolist()
    start_date = factor_date_list[0].strftime("%Y-%m-%d")
    end_date = factor_date_list[-1].strftime("%Y-%m-%d")
    test_date = start_date + ' - ' + end_date
    universe = 'A Shares' if universe is None else universe
    date_num, stock_num = factor_data.shape
    sum_index = ['Factor Name', 'Test Period', 'Stock Universe', 'Stock Count', 'Date Count', 'Holding Period',
                 'Average Turnover']
    sum_val_str = [str(i) for i in
                   [factor_name, test_date, universe.replace('_', ' '), stock_num, date_num, holding_period,
                    avg_turnover]]
    sum_df = pd.DataFrame(sum_val_str, index=sum_index)
    sum_df.columns = ['Basic Info']
    sft_setting = pd.DataFrame(
        [['Benchmark', 'Segment Number', 'Standard', 'median_winsor', 'Fillna By Industry',  # 'easy_test',
          'Seg by Industry', 'Transaction Cost'],
         [benchmark, segment_number, standard, median, fillna, seg_by_industry, transaction_cost]],
        columns=sum_index, index=[' ', 'Settings']).T  # sjl，'Robust Segment'已去除，分层时去除异常点
    sft_setting2 = pd.DataFrame([['Industry Type', 'IC Type', 'Compare Style', 'Interest Type',
                                  'Ret Price', 'Ret Shift', ''],
                                 [industry_type, ic_type, compare_style, interest_type, ret_price, ret_shift]],
                                columns=sum_index,
                                index=[' ', 'Settings2']).T  # sjl，self.easy_test去除，替换为industry_type，因子中性化所选行业
    sum_df = pd.concat([sum_df, sft_setting, sft_setting2], axis=1)
    return sum_df


def factor_distribution(factor_data, stock_filter_df=None):
    """
    :param factor_data: factor_data: 截面因子形式的dataframe
    :param stock_filter_df: 与factor_data 拥有相同格式的 某个股票池的成分股信息
    :return: pd.DataFrame : 'Skew', 'Kurtosis', 'Complete%', 'Median', 'Mean', 'Max', 'Min', 'Std'
    """
    factor_np = factor_data.values.flatten()
    factor_val = factor_np[np.isfinite(factor_np)]
    factor_min = np.min(factor_val)
    factor_max = np.max(factor_val)
    factor_mean = np.mean(factor_val)
    factor_median = np.median(factor_val)
    factor_std = np.std(factor_val)
    factor_skew = sps.skew(factor_val)  # 偏度
    factor_kurtosis = sps.kurtosis(factor_val)  # 峰度
    factor_complete = len(factor_val) / stock_filter_df.sum().sum()
    colname = ['Skew', 'Kurtosis', 'Complete%', 'Median', 'Mean', 'Max', 'Min', 'Std']
    factor_dist_df = pd.DataFrame([factor_skew, factor_kurtosis, factor_complete,
                                   factor_median, factor_mean, factor_max, factor_min, factor_std], index=colname)
    return factor_dist_df


def factor_score_correlation_calc(factor_pd, holding_period=1):
    """
    :param factor_pd:
    :param holding_period:
    :return:
    """
    factor_auto_correlation = pd.DataFrame()
    factor_auto_correlation['Pearson Linear ' + str(holding_period) + ' Days'] = factor_pd.corrwith(
        factor_pd.shift(holding_period), axis=1)
    factor_rank = factor_pd.rank(axis=1)
    factor_auto_correlation['Spearman Rank ' + str(holding_period) + ' Days'] = factor_rank.corrwith(
        factor_rank.shift(holding_period), axis=1)
    return factor_auto_correlation


def collinear_test(standardized_data, neutral_dict):
    factor_corr = {}
    for item in neutral_dict:
        factor_corr[item] = standardized_data.corrwith(neutral_dict[item], axis=1)
    factor_corr = pd.DataFrame.from_dict(factor_corr, orient='index').T
    return factor_corr


def factor_neutral_corr_calc(factor_data, universe='alpha_universe', params_of_regressor=None):
    return collinear_test(factor_data=factor_data, universe=universe, params_of_regressor=params_of_regressor)


def winsorized_mean(x: object, cut_range: object = (3, 97)) -> object:
    x = np.ma.masked_invalid(x)
    x = x.data[~x.mask]
    l_b = np.percentile(x, cut_range[0])
    u_b = np.percentile(x, cut_range[1])
    return np.mean(x[(x >= l_b) & (x <= u_b)])


