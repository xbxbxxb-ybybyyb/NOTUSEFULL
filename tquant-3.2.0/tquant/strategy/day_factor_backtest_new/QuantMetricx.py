from tquant.strategy.day_factor_backtest_new.index_calc.evaluative_index_calc import calc_ic_by_industry, \
    calc_ic_duration_test, alpha_decay_test, calc_factor_ic, calc_corr_weighted, calc_ic_score_weighted
from tquant.strategy.day_factor_backtest_new.index_calc.regression_index_calc import regression_analysis
from tquant.strategy.day_factor_backtest_new.index_calc.segment_index_calc import segment_test, \
    segment_test_by_industry, segment_performance_measure
from tquant.strategy.day_factor_backtest_new.index_calc.statistical_index_calc import turnover_calc, \
    factor_distribution, winsorized_mean
from tquant.strategy.day_factor_backtest_new.data.data_manager import DataManager
from tquant.strategy.day_factor_backtest_new.data.data_preprocess import regression_ols, standard_process
from tquant.strategy.day_factor_backtest_new.util.naming_config import CITIC_I_mapper, month_mapper
from tquant.strategy.day_factor_backtest.backtest.utility import align_data_inner
from datetime import datetime as dt

import pandas as pd
import numpy as np


def factor_ic_by_industry_calc(factor_data, price_use='close', universe='alpha_universe', holding_period=1,
                               ret_shift=True, ic_type='original'):
    """
    分行业计算因子IC
    :param factor_data: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
    :param price_use: 计算收益率因子，默认用收盘价，可改成open、vwap
    :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
    :param holding_period: 持有期（int）
    :param ret_shift: 如果是True，收益率计算周期为 T+2/T+1，如果是False，收益率计算周期为 T+1/T+0
    :param ic_type: 如果是original，因子值等权，如果是score_weighted，按因子值排名加权。默认original
    :return:
    """
    factor_data_cp = factor_data.copy()
    factor_data_cp = factor_data_cp.sort_index()
    start_date = factor_data_cp.index[0]
    end_date = factor_data_cp.index[-1]
    dm = DataManager(start_date=start_date, end_date=end_date,price_use=price_use, universe=universe,
                     holding_period=holding_period, ret_shift=ret_shift, industry_type='CITIC_I')
    # 底层接口
    holding_period_return = dm.get_holding_period_ret_data()
    stock_industry = dm.get_industry_data()
    factor_data_cp.index = pd.to_datetime(factor_data_cp.index, format="%Y/%m/%d")
    stock_filter = dm.get_stock_filter_data()
    factor_data_cp[stock_filter == False] = np.nan
    factor_data_cp = factor_data_cp.dropna(how='all', axis=1)
    data_dict = dict()
    data_dict['factor_data_cp'] = factor_data_cp
    data_dict['holding_period_return'] = holding_period_return
    data_dict['stock_industry'] = stock_industry
    data_dict = align_data_inner(data_dict)
    return calc_ic_by_industry(factor_score=data_dict['factor_data_cp'], hpr=data_dict['holding_period_return'],
                               stock_industry=data_dict['stock_industry'],
                               ic_type=ic_type).rename(columns=CITIC_I_mapper)


def factor_ic_duration_calc(factor_data, price_use='close', ic_type='original', universe='alpha_universe',
                            ret_shift=True):
    """
    因子IC随时间持续性
    :param factor_data: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
    :param price_use: 计算收益率因子，默认用收盘价，可改成open、vwap
    :param ic_type: 如果是original，因子值等权，如果是score_weighted，按因子值排名加权。默认original
    :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
    :return: 因子IC随时间的持续性
    """
    factor_data_cp = factor_data.copy()
    factor_data_cp = factor_data_cp.sort_index()
    start_date = factor_data_cp.index[0]
    end_date = factor_data_cp.index[-1]
    dm = DataManager(start_date=start_date, end_date=end_date, price_use=price_use, universe=universe)
    price_use_data = dm.get_price_use_data()
    if ret_shift:
        price_use_data = price_use_data.shift(-1)
    factor_data_cp.index = pd.to_datetime(factor_data_cp.index, format="%Y/%m/%d")
    stock_filter = dm.get_stock_filter_data()
    factor_data_cp[stock_filter == False] = np.nan
    factor_data_cp = factor_data_cp.dropna(how='all', axis=1)
    data_dict = dict()
    data_dict['factor_data_cp'] = factor_data_cp
    data_dict['price_use_data'] = price_use_data
    data_dict = align_data_inner(data_dict)
    return calc_ic_duration_test(factor_data=data_dict['factor_data_cp'], price_use_data=data_dict['price_use_data'],
                                 ic_type=ic_type)


def factor_alpha_decay_calc(factor_data, universe, price_use='close', max_lag=5, holding_period=1, ic_type='original',
                            ret_shift=True):
    """
    因子IC随时间的衰减
    :param factor_data: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
    :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
    :param price_use: 计算收益率因子，默认用收盘价，可改成open、vwap
    :param max_lag: 因子值与收益率之间相差的最大周期(int)
    :param holding_period: 持有期（int）
    :param ic_type: 如果是original，因子值等权，如果是score_weighted，按因子值排名加权。默认original
    :param ret_shift: 如果是True，收益率计算周期为 T+2/T+1，如果是False，收益率计算周期为 T+1/T+0
    :return: 因子IC随时间的衰减
    """
    factor_data_cp = factor_data.copy()
    factor_data_cp = factor_data_cp.sort_index()
    start_date = factor_data_cp.index[0]
    end_date = factor_data_cp.index[-1]
    dm = DataManager(start_date=start_date, end_date=end_date, price_use=price_use, universe=universe,
                     holding_period=holding_period, ret_shift=ret_shift)
    holding_period_return = dm.get_holding_period_ret_data()
    factor_data_cp.index = pd.to_datetime(factor_data_cp.index, format="%Y/%m/%d")
    stock_filter = dm.get_stock_filter_data()
    factor_data_cp[stock_filter == False] = np.nan
    factor_data_cp = factor_data_cp.dropna(how='all', axis=1)
    data_dict = dict()
    data_dict['factor_data_cp'] = factor_data_cp
    data_dict['holding_period_return'] = holding_period_return
    data_dict = align_data_inner(data_dict)
    return \
    alpha_decay_test(factor_data=data_dict['factor_data_cp'], holding_period_return=data_dict['holding_period_return'],
                     max_lag=max_lag, holding_period=holding_period, ic_type=ic_type)[0]


def factor_ic_calc(factor_data, price_use, universe, holding_period=1, ret_shift=True, ic_type='original', min_pct=0.1):
    """
    计算因子IC值
    :param factor_data: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
    :param price_use: 计算收益率因子，默认用收盘价，可改成open、vwap
    :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
    :param holding_period: 持有期（int）
    :param ret_shift: 如果是True，收益率计算周期为 T+2/T+1，如果是False，收益率计算周期为 T+1/T+0
    :param ic_type: 如果是original，因子值等权，如果是score_weighted，按因子值排名加权。默认original
    :param min_pct: 因子值有效标的数量最低比例
    :return: 因子IC值
    """
    factor_data_cp = factor_data.copy()
    factor_data_cp = factor_data_cp.sort_index()
    start_date = factor_data_cp.index[0]
    end_date = factor_data_cp.index[-1]
    dm = DataManager(start_date=start_date, end_date=end_date, price_use=price_use, universe=universe,
                     holding_period=holding_period, ret_shift=ret_shift)
    holding_period_return = dm.get_holding_period_ret_data()
    factor_data_cp.index = pd.to_datetime(factor_data_cp.index, format="%Y/%m/%d")
    stock_filter = dm.get_stock_filter_data()
    factor_data_cp[stock_filter == False] = np.nan
    factor_data_cp = factor_data_cp.dropna(how='all', axis=1)
    data_dict = dict()
    data_dict['factor_data_cp'] = factor_data_cp
    data_dict['holding_period_return'] = holding_period_return
    data_dict = align_data_inner(data_dict)
    return calc_factor_ic(factor_data=data_dict['factor_data_cp'],
                          holding_period_return=data_dict['holding_period_return'],
                          ic_type=ic_type, min_pct=min_pct)


def factor_regression_analysis(factor_data, price_use='close', holding_period=1, ret_shift=True,
                               universe='alpha_universe', params_of_regressor=None):
    """

    :param factor_data: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
    :param price_use: 计算收益率因子，默认用收盘价，可改成open、vwap
    :param holding_period: 持有期（int）
    :param ret_shift: 如果是True，收益率计算周期为 T+2/T+1，如果是False，收益率计算周期为 T+1/T+0
    :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
    :param params_of_regressor: 回归子
    :return:
    """
    factor_data_cp = factor_data.copy()
    if params_of_regressor is None:
        params_of_regressor = ['Industry', 'Size']
    start_date = factor_data_cp.index[0]
    end_date = factor_data_cp.index[-1]
    # factor_data_cp的索引控制为timestamp格式
    dm = DataManager(start_date=start_date, end_date=end_date, universe=universe)
    if params_of_regressor == ['Industry', 'Size']:
        industry_data = dm.get_industry_data()
        size_data = dm.get_size_data()
        neutral_dict_df = {'Industry': industry_data, 'Size': size_data}
    else:
        raise Exception("目前仅支持按照行业数据和市值因子数据做回归分析，有需要请联系tquant")
    factor_data_cp.index = pd.to_datetime(factor_data_cp.index, format="%Y/%m/%d")
    holding_period_ret = dm.get_holding_period_ret_data()
    stock_filter = dm.get_stock_filter_data()
    factor_data_cp[stock_filter == False] = np.nan
    factor_data_cp = factor_data_cp.dropna(how='all', axis=1)
    data_dict = dict()
    data_dict['factor_data_cp'] = factor_data_cp
    data_dict['Industry'] = neutral_dict_df['Industry']
    data_dict['Size'] = neutral_dict_df['Size']
    data_dict['holding_period_ret'] = holding_period_ret
    data_dict = align_data_inner(data_dict)
    neutral_dict_df['Industry'] = data_dict['Industry']
    neutral_dict_df['Size'] = data_dict['Size']
    return regression_analysis(standardized_data=data_dict['factor_data_cp'], neutral_dict_df=neutral_dict_df,
                               holding_period_ret=data_dict['holding_period_ret'], ic_type='original')


def factor_neutralization_calc(factor_data, universe=None, params_of_regressor=None):
    """
    :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
    :param factor_data: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
    :param params_of_regressor: 因子中性化使用的回归参数，通常为 市值因子 或 行业因子 默认为['Industry','Size']
    :return: 中性化因子值
    """
    factor_data_cp = factor_data.copy()
    factor_data_cp = factor_data_cp.sort_index()
    start_date = factor_data_cp.index[0]
    end_date = factor_data_cp.index[-1]
    dm = DataManager(start_date=start_date, end_date=end_date, universe=universe)
    neutralized_dict = dict()
    if not params_of_regressor:
        params_of_regressor = ['Industry', 'Size']
    if not isinstance(params_of_regressor, list):
        raise Exception("【单因子评价】回归参数必须传list形式")
    if 'Industry' in params_of_regressor:
        neutralized_dict['Industry'] = dm.get_industry_data()
    if 'Size' in params_of_regressor:
        neutralized_dict['Size'] = dm.get_size_data()
    for param in params_of_regressor:
        if param not in ['Industry', 'Size']:
            raise Exception("【单因子评价】中性化处理目前仅支持行业因子或市值因子，需要扩展请联系tquant团队！")
    factor_data_cp.index = pd.to_datetime(factor_data_cp.index, format='%Y%m%d')
    stock_filter = dm.get_stock_filter_data()
    factor_data_cp[stock_filter == False] = np.nan
    factor_data_cp = factor_data_cp.dropna(how='all', axis=1)
    data_dict = dict()
    data_dict['factor_data_cp'] = factor_data_cp
    data_dict['Industry'] = neutralized_dict['Industry']
    data_dict['Size'] = neutralized_dict['Size']
    data_dict = align_data_inner(data_dict)
    neutralized_dict['Industry'] = data_dict['Industry']
    neutralized_dict['Size'] = data_dict['Size']
    return regression_ols(y=data_dict['factor_data_cp'], x=neutralized_dict)[0]


def factor_standard_process_calc(factor_data, universe='alpha_universe', industry_type='CITIC_I', fillna=False,
                                 median=False, standard=False):
    """

    :param industry_type: 行业类型
    :param factor_data: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
    :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
    :param fillna: 是否按照行业中位数进行nan值填充
    :param median: 是否采用3sigema的方式去极值
    :param standard: 是否对数据进行标准化处理
    :return: 对原始因子数据进行预处理
    """
    factor_data_cp = factor_data.copy()
    factor_data_cp = factor_data_cp.sort_index()
    start_date = factor_data_cp.index[0]
    end_date = factor_data_cp.index[-1]
    dm = DataManager(start_date=start_date, end_date=end_date, universe=universe, industry_type=industry_type)
    stock_filter_df = dm.get_stock_filter_data()
    stock_industry_df = dm.get_industry_data()
    factor_data_cp.index = pd.to_datetime(factor_data_cp.index, format='%Y%m%d')
    factor_data_cp.columns.name = 'Ticker'
    stock_filter = dm.get_stock_filter_data()
    factor_data_cp[stock_filter == False] = np.nan
    factor_data_cp = factor_data_cp.dropna(how='all', axis=1)
    data_dict = dict()
    data_dict['factor_data_cp'] = factor_data_cp
    data_dict['stock_filter_df'] = stock_filter_df
    data_dict['stock_industry_df'] = stock_industry_df
    data_dict = align_data_inner(data_dict)
    return standard_process(factor_data=data_dict['factor_data_cp'], stock_filter_df=data_dict['stock_filter_df'],
                            stock_industry_df=data_dict['stock_industry_df'],
                            fillna=fillna, median=median, standard=standard, boxskew=False)[1]


def factor_segment_test(factor_pd, price_use, holding_period, universe='alpha_universe', benchmark=None, segment_num=10,
                        handle_insufficient=False, handle_return_outlier=False, return_bucket_ic=False,
                        transaction_cost=None, max_quantile=None, by_industry=False, industry_type='CITIC_I',
                        ret_shift=True):
    """

    :param factor_pd: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
    :param price_use: 计算收益率因子，默认用收盘价，可改成open、vwap
    :param holding_period: 持有期（int）
    :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
    :param benchmark: 基准，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
    :param segment_num: 分层测试所分层数，int类型
    :param handle_insufficient: 数据是否不足，bool类型
    :param handle_return_outlier: 是否采用Winsorize变换，bool类型
    :param return_bucket_ic: 是否返回分层平均收益与分层因子均值的IC值，bool类型
    :param return_industry: 是否返回行业，bool类型
    :param transaction_cost: float类型，手续费+滑点+契税，取值范围：无：0，万三佣金+千分之一印花税+无滑点：0.0013，万三佣金+千分之一印花税+千分之一滑点：0.0023，默认0.0013
    :param max_quantile: 平均收益最佳的分组
    :param by_industry: bool类型，分层测试中性化，默认False
    :param industry_type: 因子行业中性化，str类型，中信行业：CITIC_I，暂时只支持中信行业
    :return: 因子分层测试收益
    """
    factor_data = factor_pd.copy()
    if not benchmark:
        benchmark = universe
    factor_data = factor_data.sort_index()
    start_date = factor_data.index[0]
    end_date = factor_data.index[-1]
    dm = DataManager(start_date=start_date, end_date=end_date, benchmark=benchmark, universe=universe,
                     price_use=price_use, industry_type=industry_type)
    factor_data.index = pd.to_datetime(factor_data.index, format="%Y/%m/%d")

    stock_close_pd = dm.get_price_use_data()
    stock_close_pd.index = pd.to_datetime(stock_close_pd.index, format='%Y%m%d')
    benchmark_price_ps = dm.get_benchmark_data()
    benchmark_price_ps.index = pd.to_datetime(benchmark_price_ps.index, format='%Y%m%d')
    if ret_shift:
        stock_close_pd = stock_close_pd.shift(-1)
        benchmark_price_ps = benchmark_price_ps.shift(-1)
    if by_industry:
        stock_industry = dm.get_industry_data()
        stock_industry.index = pd.to_datetime(stock_industry.index, format='%Y%m%d')
        industry_weight = dm.get_industry_weight_data()
        if benchmark in ['alpha_universe', 'risk_universe']:
            stock_weight = None
        else:
            stock_weight = dm.get_stock_weight_data()
            stock_weight = stock_weight[stock_weight.columns[0]].unstack()
        stock_filter = dm.get_stock_filter_data()
        factor_data[stock_filter == False] = np.nan
        factor_data = factor_data.dropna(how='all', axis=1)
        data_dict = dict()
        data_dict['factor_data'] = factor_data
        data_dict['stock_close_pd'] = stock_close_pd
        data_dict['benchmark_price_ps'] = benchmark_price_ps
        data_dict['stock_industry'] = stock_industry
        data_dict = align_data_inner(data_dict)
        return segment_test_by_industry(factor_pd=data_dict['factor_data'], stock_close_pd=stock_close_pd,
                                        holding_period=holding_period,
                                        benchmark_price_ps=benchmark_price_ps, segment_num=segment_num,
                                        stock_industry=data_dict['stock_industry'], industry_weight=industry_weight,
                                        handle_insufficient=handle_insufficient, transaction_cost=transaction_cost,
                                        return_industry=True, stock_weight=stock_weight,
                                        max_quantile=max_quantile)
    else:
        stock_filter = dm.get_stock_filter_data()
        factor_data[stock_filter == False] = np.nan
        factor_data = factor_data.dropna(how='all', axis=1)
        data_dict = dict()
        data_dict['factor_data'] = factor_data
        data_dict['stock_close_pd'] = stock_close_pd
        data_dict['benchmark_price_ps'] = benchmark_price_ps
        data_dict = align_data_inner(data_dict)
        return segment_test(factor_pd=data_dict['factor_data'], stock_close_pd=data_dict['stock_close_pd'],
                            holding_period=holding_period, benchmark_price_ps=data_dict['benchmark_price_ps'],
                            segment_num=segment_num, handle_insufficient=handle_insufficient,
                            handle_return_outlier=handle_return_outlier, return_bucket_ic=return_bucket_ic,
                            transaction_cost=transaction_cost, max_quantile=max_quantile)


def factor_segment_performance_measure(factor_pd, price_use='close', holding_period=1, universe='alpha_universe',
                                       benchmark=None, segment_num=10,
                                       handle_insufficient=False, handle_return_outlier=False,
                                       transaction_cost=None, max_quantile=None,
                                       by_industry=False, industry_type='CITIC_I', interest_type='SAMPLE'):
    """

    :param factor_pd: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
    :param price_use: 计算收益率因子，默认用收盘价，可改成open、vwap
    :param holding_period: 持有期（int）
    :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
    :param benchmark: 基准，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
    :param segment_num: int类型，分层数，默认10层
    :param handle_insufficient: 数据是否不足，bool类型
    :param handle_return_outlier: 是否采用Winsorize变换，bool类型
    :param return_industry: 是否返回行业，bool类型
    :param transaction_cost: float类型，手续费+滑点+契税，取值范围：无：0，万三佣金+千分之一印花税+无滑点：0.0013，万三佣金+千分之一印花税+千分之一滑点：0.0023，默认0.0013
    :param max_quantile: 平均收益最佳的分组
    :param by_industry: bool类型，分层测试中性化，默认False
    :param industry_type: 因子行业中性化，str类型，中信行业：CITIC_I，暂时只支持中信行业
    :param interest_type: SIMPLE或cumprod.默认为cumprod，cumprod模式下，计算收益的方式为累乘， SIMPLE模式下，计算收益的方式为累加
    :return:
    """
    factor_pd_cp = factor_pd.copy()
    res = factor_segment_test(factor_pd=factor_pd_cp, price_use=price_use, holding_period=holding_period,
                              universe=universe,
                              benchmark=benchmark, segment_num=segment_num, industry_type=industry_type,
                              handle_insufficient=handle_insufficient, handle_return_outlier=handle_return_outlier,
                              transaction_cost=transaction_cost, max_quantile=max_quantile, by_industry=by_industry,
                              )
    if by_industry:
        if transaction_cost is None:
            seg_return = res[0]
        else:
            seg_return = res[1]
    else:
        if transaction_cost is None:
            seg_return = res
        else:
            seg_return = res[1]

    seg_return.index.name = 'mddate'
    seg_return = seg_return.reset_index()
    seg_return['mddate'] = seg_return['mddate'].apply(pd.Timestamp)
    seg_return.set_index('mddate', inplace=True)
    return segment_performance_measure(seg_return=seg_return, interest_type=interest_type)


def factor_winsorized_mean(data, cut_range=(3, 97)):
    """
    :param data: 样本数据
    :param cut_range: 缩尾百分比
    :return: 缩尾后数据均值
    """
    data_cp = data.copy()
    return winsorized_mean(x=data_cp, cut_range=cut_range)


def factor_distribution_calc(factor_data, universe='alpha_universe', seg_benchmark='alpha_universe'):
    """

    :param factor_data: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
    :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
    :param seg_benchmark: 分层基准，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
    :return: 因子值分布统计息
    """
    factor_data_cp = factor_data.copy()
    factor_data_cp = factor_data_cp.sort_index()
    start_date = factor_data_cp.index[0]
    end_date = factor_data_cp.index[-1]
    dm = DataManager(start_date=start_date, end_date=end_date, universe=universe, benchmark=seg_benchmark)
    stock_filter_df = dm.get_stock_filter_data()

    factor_data_cp.index = [dt.strptime(x, '%Y%m%d') for x in factor_data_cp.index]
    data_dict = dict()
    data_dict['factor_data_cp'] = factor_data_cp
    data_dict['stock_filter_df'] = stock_filter_df

    data_dict = align_data_inner(data_dict)
    data_dict['factor_data_cp'][data_dict['stock_filter_df'] == False] = np.nan
    data_dict['factor_data_cp'] = data_dict['factor_data_cp'].dropna(how='all', axis=1)
    data_dict = align_data_inner(data_dict)

    return factor_distribution(factor_data=data_dict['factor_data_cp'], stock_filter_df=data_dict['stock_filter_df'])


from tquant.strategy.day_factor_backtest_new.index_calc.return_index_calc import get_excess_return, calc_sample_ret


def factor_top_return_stability_calc(factor_data, price_use='vwap', top_range=0.1, transaction_cost=4e-4, random_state=0,
                                     bootstrap_steps=9, experiment_steps=10):
    """
    计算超额收益采样稳定性
    :param factor_data: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
    :param price_use: 计算收益率因子，默认用收盘价，可改成open、vwap
    :param top_range: 因子值排名取样比例
    :param transaction_cost: 交易成本
    :param random_state: 所要划分的样本结果
    :param bootstrap_steps: 测试集占比：1 - 1 / (bootstrap_steps + 1)
    :param experiment_steps: 采样次数
    :return:
    """
    factor_data_cp = factor_data.copy()
    factor_data_cp = factor_data_cp.sort_index()
    excess_return = get_excess_return(factor_df=factor_data_cp, price_use=price_use, top_range=top_range, transaction_cost=transaction_cost)[
        'excess_return']
    res = calc_sample_ret(excess=excess_return, random_state=random_state, bootstrap_steps=bootstrap_steps,
                          experiment_steps=experiment_steps)
    return res


def factor_monthly_excess_ret_calc(factor_data, price_use='vwap', holding_period=1, agg_method='sum',
                                   universe='alpha_universe', benchmark=None, segment_num=10,
                                   handle_insufficient=False, handle_return_outlier=False, return_bucket_ic=False,
                                   transaction_cost=None, max_quantile=None, by_industry=False,
                                   industry_type='CITIC_I', combination=None):
    """
    计算月度超额收益
    :param factor_data: 因子数据，数据为截面数据：行索引为日期(str)，列索引为标的代码
    :param price_use: 计算收益率因子，默认用收盘价，可改成open、vwap
    :param holding_period: 持有期（int）
    :param agg_method: 计算月度收益方法，sum为每日年化收益求和，mean每日年化收益为求平均，默认sum
    :param universe: 股票池，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
    :param benchmark: 基准，str类型，目前有沪深300：hs300，中证500：zz500，上证50：sz50，全市场：alpha_universe，默认alpha_universe
    :param segment_num: 分层测试所分层数，int类型
    :param handle_insufficient: 数据是否不足，bool类型
    :param handle_return_outlier: 是否采用Winsorize变换，bool类型
    :param return_bucket_ic: 是否返回分层平均收益与分层因子均值的IC值，bool类型
    :param transaction_cost: float类型，手续费+滑点+契税，取值范围：无：0，万三佣金+千分之一印花税+无滑点：0.0013，万三佣金+千分之一印花税+千分之一滑点：0.0023，默认0.0013
    :param max_quantile: 平均收益最佳的分组
    :param by_industry: bool类型，分层测试中性化，默认False
    :param industry_type: 因子行业中性化，str类型，中信行业：CITIC_I，暂时只支持中信行业
    :param combination: 指定分组计算月度超额月度收益，默认最佳分组
    :return: 月度超额收益
    """
    factor_data_cp = factor_data.copy()
    res = factor_segment_test(factor_pd=factor_data_cp, price_use=price_use, holding_period=holding_period,
                              universe=universe, benchmark=benchmark, segment_num=segment_num,
                              handle_insufficient=handle_insufficient, handle_return_outlier=handle_return_outlier,
                              return_bucket_ic=return_bucket_ic,
                              transaction_cost=transaction_cost, max_quantile=max_quantile, by_industry=by_industry,
                              industry_type=industry_type)
    if by_industry:
        if transaction_cost is None:
            seg_return = res[0]
        else:
            seg_return = res[1]
    else:
        if transaction_cost is None:
            seg_return = res
        else:
            seg_return = res[1]
    col_list = seg_return.columns.tolist()
    if combination:
        er_col = combination.upper()
        er_use = seg_return[er_col] - seg_return['Index']
    else:
        er_col = [i for i in col_list if i.find('-') > 0][0]
        er_use = seg_return[er_col]  # 超额收益
    year_list = list(set(er_use.index.year))
    year_list.sort(reverse=False)
    month_ps = pd.DataFrame(index=[i for i in range(1, 13)])
    for year in year_list:
        sliced = er_use.loc[str(year)]
        if agg_method == 'mean':
            month_ps[year] = sliced.groupby(sliced.index.month).mean()
        elif agg_method == 'sum':
            month_ps[year] = sliced.groupby(sliced.index.month).sum()
        else:
            raise NotImplementedError
    month_ps = month_ps.rename(index=month_mapper)
    return month_ps
