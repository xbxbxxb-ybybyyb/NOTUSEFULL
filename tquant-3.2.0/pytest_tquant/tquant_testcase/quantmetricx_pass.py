import numpy as np, pandas as pd
from datetime import datetime as dt
from tquant.strategy.day_factor_backtest_new.QuantMetricx import *
from tquant import StockData, BasicData
bd = BasicData()
sd = StockData()
#  -----------------------------------------------------------------------
# # 用SDK取数
# stock_list = sd.get_plate_info('MARKET', '20191231', 'ALLA')['stock'].tolist()
# trd_days = bd.get_trading_day('20200101', '20200331')
# factor_data = sd.get_factor_valuation_metrics(stock_list, trd_days, ['ev2'])

# # 将数据转换成行索引为日期(str)，列索引为标的格式
# factor_data = factor_data['ev2'].unstack()
# factor_data = factor_data.sort_index()
# # print(factor_data)
#  -----------------------------------------------------------------------
# 北向资金原始因子数据
data_path = '/app/mount/code/CGW/DayFactorBacktest_test/nw_total_share_pct.pkl'  # 北向资金原始数据pickle文件路径
factor_data = pd.read_pickle(data_path)
factor_data.index.names = ['mddate', 'stock']
# factor_data.reset_index(inplace=True)
# factor_data['mddate'] = factor_data['mddate'].apply(pd.Timestamp)
# factor_data.set_index(['mddate', 'stock'], inplace=True)
factor_data = factor_data['NW_total_share_pct'].unstack()
factor_data = factor_data.sort_index()
factor_data = factor_data.loc['20190102':'20190331', :]
#  -----------------------------------------------------------------------
# factor_ic_calc
# count = 0
# for price_use in ['close', 'open', 'vwap']:
#     for universe in ['alpha_universe', 'hs300', 'sz50']:
#         for holding_period in [1,5,10]:
#             for ret_shift in [True, False]:
#                 for ic_type in ['original', 'score_weighted']:
#                     count += 1
#                     print('序号：{}，参数组合：price_use-{}, universe-{}, holding_period-{}, ret_shift-{}, ic_type-{}'
#                         .format(count, price_use, universe, holding_period, ret_shift, ic_type))
#                     res = factor_ic_calc(factor_data=factor_data, price_use=price_use, universe=universe,
#                                         holding_period=holding_period, ret_shift=ret_shift, ic_type=ic_type, )
#                     print(res.head())
#  -----------------------------------------------------------------------
# # factor_ic_by_industry_calc
# count = 0
# for price_use in ['close', 'open', 'vwap']:
#     for universe in ['alpha_universe', 'hs300', 'sz50']:
#         for holding_period in [1,5,10]:
#             for ret_shift in [True, False]:
#                 for ic_type in ['original', 'score_weighted']:
#                     count += 1
#                     print('序号：{}，参数组合：price_use-{}, universe-{}, holding_period-{}, ret_shift-{}, ic_type-{}'
#                         .format(count, price_use, universe, holding_period, ret_shift, ic_type))
#                     res = factor_ic_by_industry_calc(factor_data=factor_data, price_use=price_use, universe=universe,
#                                         holding_period=holding_period, ret_shift=ret_shift, ic_type=ic_type, )
#                     print(res.head())
#  -----------------------------------------------------------------------
# # factor_ic_duration_calc
# count = 0
# for price_use in ['close', 'open', 'vwap']:
#     for universe in ['alpha_universe', 'hs300', 'sz50']:
#         for ic_type in ['original', 'score_weighted']:
#             for ret_shift in [True, False]:
#                 count += 1
#                 print('序号：{}，参数组合：price_use-{}, universe-{}, ic_type-{}, ret_shift-{}'
#                             .format(count, price_use, universe, ic_type, ret_shift))
#                 res = factor_ic_duration_calc(factor_data=factor_data, price_use=price_use, universe=universe,
#                                     ic_type=ic_type, ret_shift=ret_shift)
#                 print(res)
#  -----------------------------------------------------------------------
# # factor_alpha_decay_calc
# count = 0
# for price_use in ['close', 'open', 'vwap']:
#     for universe in ['alpha_universe', 'hs300', 'sz50']:
#         for max_lag in [3,5,8]:
#             for holding_period in [1,5,10]:
#                 for ic_type in ['original', 'score_weighted']:
#                     for ret_shift in [True, False]:
#                         count += 1
#                         print('序号：{}，参数组合：price_use-{}, universe-{}, max_lag-{}, holding_period-{}, ic_type-{}, ret_shift-{}'
#                         .format(count, price_use, universe, max_lag, holding_period, ic_type, ret_shift))
#                         res = factor_alpha_decay_calc(factor_data=factor_data, price_use=price_use, universe=universe,max_lag=max_lag, holding_period=holding_period,
#                                             ic_type=ic_type,ret_shift=ret_shift)
#                         print(res)
#  -----------------------------------------------------------------------
# # factor_regression_analysis
# count = 0
# for price_use in ['close', 'open', 'vwap']:
#     for holding_period in [1,5,10]:
#         for ret_shift in [True, False]:
#             for universe in ['alpha_universe', 'hs300', 'sz50']:
#                 count += 1
#                 print('序号：{}，参数组合：price_use-{}, holding_period-{}, ret_shift-{}, universe-{}, params_of_regressor-None'
#                 .format(count, price_use, holding_period, ret_shift, universe))
#                 res = factor_regression_analysis(factor_data=factor_data,price_use=price_use, holding_period=holding_period, ret_shift=ret_shift,
#                                             universe=universe, params_of_regressor=None)
#                 print(res.head())
#  -----------------------------------------------------------------------
# # factor_neutralization_calc
# count = 0
# for universe in ['alpha_universe', 'hs300', 'sz50']:
#     count += 1
#     print('序号：{}，参数组合：universe-{}, params_of_regressor-None'
#                 .format(count, universe))
#     res = factor_neutralization_calc(factor_data=factor_data, universe=universe, params_of_regressor=None)
#     print(res.head())
#  -----------------------------------------------------------------------
# factor_standard_process_calc
# count = 0
# for universe in ['alpha_universe', 'hs300', 'sz50']:
#     for fillna in [False, True]:
#         for median in [False, True]:
#             for standard in [False, True]:
#                     count += 1
#                     print('序号：{}，参数组合：universe-{}, industry_type-CITIC_I, fillna-{}, median-{}, standard-{}'
#                         .format(count, universe, fillna, median, standard))
#                     res = factor_standard_process_calc(factor_data=factor_data, universe=universe, industry_type='CITIC_I', fillna=fillna,
#                                                 median=median, standard=standard)
#                     print(res.head())
#  -----------------------------------------------------------------------
# factor_segment_test
# count = 0
# for universe in ['alpha_universe', 'hs300']:
#     for benchmark in [None, 'hs300']:
#         for transaction_cost in [0, 0.0013]:
#             for by_industry in [False, True]:
#                 count += 1
#                 print('序号：{}，参数组合：universe-{}, benchmark-{}, transaction_cost-{}, by_industry-{}'
#                     .format(count, universe, benchmark, transaction_cost, by_industry))
#                 res = factor_segment_test(factor_pd=factor_data, price_use='vwap', holding_period=1, universe=universe,
#                 benchmark=benchmark, segment_num=10,
#                 handle_insufficient=False, handle_return_outlier=False, return_bucket_ic=False,
#                 transaction_cost=transaction_cost, max_quantile=None, by_industry=by_industry, industry_type='CITIC_I')
#                 print(res)
#  -----------------------------------------------------------------------
# # factor_segment_performance_measure
# count = 0
# for universe in ['alpha_universe', 'hs300']:
#     for benchmark in [None, 'hs300']:
#         for transaction_cost in [0, 0.0013]:
#             for by_industry in [False, True]:
#                 for interest_type in ['SAMPLE', 'cumprod']:
#                     count += 1
#                     print('序号：{}，参数组合：universe-{}, benchmark-{}, transaction_cost-{}, by_industry-{}, interest_type-{}'
#                     .format(count, universe, benchmark, transaction_cost, by_industry, interest_type))
#                     res = factor_segment_performance_measure(factor_pd=factor_data, price_use='vwap', holding_period=1, universe=universe,
#                                                         benchmark=benchmark, segment_num=10,
#                                                         handle_insufficient=False, handle_return_outlier=False,
#                                                         transaction_cost=transaction_cost, max_quantile=None,
#                                                         by_industry=by_industry, industry_type='CITIC_I', interest_type=interest_type)
#                     print(res)
#  -----------------------------------------------------------------------
# factor_winsorized_mean
# data1 = pd.Series(np.random.randint(1,10,1000)).tolist()
# data2 = data1 + [10000]*3
# print(round(np.mean(data1),3))
# print(round(np.mean(data2),3))
# res = factor_winsorized_mean(data=data2, cut_range=(3, 97))
# print(res)

#  -----------------------------------------------------------------------
# factor_distribution_calc
# count = 0
# for universe in ['alpha_universe', 'hs300', 'sz50']:
#     for seg_benchmark in ['alpha_universe', 'hs300', 'sz50']:
#         count += 1
#         print('序号：{}，参数组合：universe-{}, seg_benchmark-{}'
#             .format(count, universe, seg_benchmark))
#         res = factor_distribution_calc(factor_data=factor_data, universe='alpha_universe', seg_benchmark='alpha_universe' )
#         print(res.head())
#  -----------------------------------------------------------------------
