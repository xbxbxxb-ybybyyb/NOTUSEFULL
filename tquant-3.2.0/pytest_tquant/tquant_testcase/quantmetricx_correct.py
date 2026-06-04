"""
测试逻辑
1.调用旧接口DayFactorBacktest，接口文档地址http://168.61.114.19:8888/HTAI/v2/help/doc/quant/factor_research/#51
2.新旧接口入参调一致。有的参数不在DayFactorBacktest函数中，如ret_shift，需到FactorBacktest.py实例化时修改；
3.DayFactorBacktest运行过程中，导出因子数据factor_data存到本地，作为新接口入参。导出因子数据在factor_test.py中。
  举例，DayFactorBacktest运行之前，在factor_test.py第646行计算IC时，将self.data['factor_data']存为本地pickle文件，作为新接口factor_ic_calc入参。
4.DayFactorBacktest运行结束后，自动生成excel文件存到本地，包含各个接口输出结果数据，不同接口结果在不同sheet中。
5.调用新接口。将老接口导出的factor_data作为新接口因子值入参，输出结果。
6.比对新旧接口输出结果是否一致。对比调整数据格式一致。
7.已把旧接口因子值和旧接口结果导出，准确性测试时，不用重新执行旧接口，直接读取导出的数据文件。
8.因子评价路径
/opt/anaconda3/lib/python3.6/site-packages/tquant/strategy/day_factor_backtest/FactorBacktest.py
/opt/anaconda3/lib/python3.6/site-packages/tquant/strategy/day_factor_backtest/backtest/factor_test.py
/opt/anaconda3/lib/python3.6/site-packages/tquant/strategy/day_factor_backtest/backtest/segment_test.py
/opt/anaconda3/lib/python3.6/site-packages/tquant/strategy/day_factor_backtest/backtest/utility.py
"""
import numpy as np
import pandas as pd
import time
from datetime import datetime as dt
from tquant.strategy.day_factor_backtest_new.QuantMetricx import *
from tquant.strategy.day_factor_backtest.FactorBacktest import DayFactorBacktest
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
factor_name = 'nw_total_share_pct'
start_date = '20190102'
end_date = '20190331'
data_path = '/app/mount/code/CGW/DayFactorBacktest_test/nw_total_share_pct.pkl'
result_folder = '/app/mount/code/CGW/DDDDD'
factor_data = pd.read_pickle(data_path)
factor_data.index.names = ['mddate', 'stock']
factor_data = factor_data.sort_index()
factor_data = factor_data.loc[start_date:end_date, :]
factor_data.rename(columns={'NW_total_share_pct':'nw_total_share_pct'}, inplace=True)

factor_data_ori = factor_data
factor_data_new = factor_data['nw_total_share_pct'].unstack()

#  -----------------------------------------------------------------------
# # factor_ic_calc---original
# # 导出旧接口factor_test.py--646行factor_data: self.data['factor_data'].to_pickle('/app/mount/code/CGW/DayFactorBacktest_test/test_datas/mid_factor_data_factor_ic_calc.pkl')

# # 老接口
# DayFactorBacktest(start_date, end_date, factor_name, factor_data_ori, result_folder, universe='alpha_universe',
#                     benchmark='alpha_universe', transaction_cost=0.0013, holding_period=1, segment_number=10,
#                     median=True, standard=True, fillna=False, seg_by_industry=False, industry_type='CITIC_I')
# ori_res_path = '/app/mount/code/CGW/DDDDD/nw_total_share_pct/FactorBacktest_nw_total_share_pct.xlsx'
# ic_original = pd.read_excel(ori_res_path, sheet_name='ic_ts_combined')['IC Original']
# print('----------')
# print(ic_original.head())

# # 新接口
# factor_data_new = pd.read_pickle('/app/mount/code/CGW/DayFactorBacktest_test/test_datas/mid_factor_data_factor_ic_calc.pkl')
# factor_data_new.index = [dt.strftime(x, '%Y%m%d') for x in factor_data_new.index]
# res = factor_ic_calc(factor_data=factor_data_new, price_use='vwap', universe='alpha_universe',
#                     holding_period=1, ret_shift=True, ic_type='original', )
# print(res.head())

# # 新旧结果比较
# ic_original.fillna(0, inplace=True)
# res.fillna(0, inplace=True)
# ic_original = round(ic_original, 8)
# res = round(res, 8)
# print((ic_original.values == res.values).all())
#  -----------------------------------------------------------------------
# # factor_ic_by_industry_calc
# # 导出旧接口factor_test.py--684行factor_data: factor_data.to_pickle('/app/mount/code/CGW/DayFactorBacktest_test/test_datas/mid_factor_data_factor_ic_by_industry_calc.pkl')

# # 老接口
# DayFactorBacktest(start_date, end_date, factor_name, factor_data_ori, result_folder, universe='alpha_universe',
#                     benchmark='alpha_universe', transaction_cost=0, holding_period=1, segment_number=10,
#                     median=True, standard=True, fillna=False, seg_by_industry=True, industry_type='CITIC_I')
# ori_res_path = '/app/mount/code/CGW/DDDDD/nw_total_share_pct/FactorBacktest_nw_total_share_pct.xlsx'
# ic_by_industry_calc = pd.read_excel(ori_res_path, sheet_name='ic_by_industry')
# print('----------')
# ic_by_industry_calc.set_index('mddate', inplace=True)
# print(ic_by_industry_calc.head())

# # 新接口
# factor_data = pd.read_pickle('/app/mount/code/CGW/DayFactorBacktest_test/test_datas/mid_factor_data_factor_ic_by_industry_calc.pkl')
# factor_data.index = [dt.strftime(x, '%Y%m%d') for x in factor_data.index]
# res = factor_ic_by_industry_calc(factor_data=factor_data, price_use='vwap', universe='alpha_universe',
#                     holding_period=1, ret_shift=True, ic_type='original', )
# print(res.head())

# # 新旧结果比较
# ic_by_industry_calc.fillna(0, inplace=True)
# res.fillna(0, inplace=True)
# ic_by_industry_calc = round(ic_by_industry_calc, 8)
# res = round(res, 8)
# print((ic_by_industry_calc == res).all().all())
#  -----------------------------------------------------------------------
# # factor_ic_duration_calc
# # 导出旧接口factor_test.py--635行factor_data: factor_data.to_pickle('/app/mount/code/CGW/DayFactorBacktest_test/test_datas/mid_factor_data_calc_ic_duration_test.pkl')

# # 老接口
# DayFactorBacktest(start_date, end_date, factor_name, factor_data_ori, result_folder, universe='alpha_universe',
#                     benchmark='alpha_universe', transaction_cost=0.0013, holding_period=1, segment_number=10,
#                     median=True, standard=True, fillna=False, seg_by_industry=False, industry_type='CITIC_I')
# ori_res_path = '/app/mount/code/CGW/DDDDD/nw_total_share_pct/FactorBacktest_nw_total_share_pct.xlsx'
# ic_duration = pd.read_excel(ori_res_path, sheet_name='ic_duration')['IC Duration']
# print('----------')
# print(ic_duration)

# # 新接口
# factor_data_new = pd.read_pickle('/app/mount/code/CGW/DayFactorBacktest_test/test_datas/mid_factor_data_calc_ic_duration_test.pkl')
# factor_data_new.index = [dt.strftime(x, '%Y%m%d') for x in factor_data_new.index]
# res = factor_ic_duration_calc(factor_data=factor_data_new, price_use='vwap', universe='alpha_universe',
#                     ic_type='original', ret_shift=True)
# print('----------')
# print(res)

# # 新旧结果比较
# ic_duration.fillna(0, inplace=True)
# res.fillna(0, inplace=True)
# ic_duration = round(ic_duration, 8)
# res = round(res, 8)
# print((ic_duration.values == res.values.flatten()).all())
#  -----------------------------------------------------------------------
# # factor_alpha_decay_calc
# # 导出旧接口factor_test.py--633行factor_data: factor_data.to_pickle('/app/mount/code/CGW/DayFactorBacktest_test/test_datas/mid_factor_data_alpha_decay_test.pkl')

# # 老接口
# DayFactorBacktest(start_date, end_date, factor_name, factor_data_ori, result_folder, universe='alpha_universe',
#                     benchmark='alpha_universe', transaction_cost=0.0013, holding_period=1, segment_number=10,
#                     median=True, standard=True, fillna=False, seg_by_industry=False, industry_type='CITIC_I')
# ori_res_path = '/app/mount/code/CGW/DDDDD/nw_total_share_pct/FactorBacktest_nw_total_share_pct.xlsx'
# ic_decay = pd.read_excel(ori_res_path, sheet_name='ic_decay')['IC Decay']
# print('----------')
# print(ic_decay)

# # 新接口
# factor_data_new = pd.read_pickle('/app/mount/code/CGW/DayFactorBacktest_test/test_datas/mid_factor_data_alpha_decay_test.pkl')
# factor_data_new.index = [dt.strftime(x, '%Y%m%d') for x in factor_data_new.index]
# res = factor_alpha_decay_calc(factor_data=factor_data_new, price_use='vwap', universe='alpha_universe',max_lag=5, holding_period=1,
#                     ic_type='original',ret_shift=True)
# print('----------')
# print(res)

# # 新旧结果比较
# ic_decay.fillna(0, inplace=True)
# res.fillna(0, inplace=True)
# ic_decay = round(ic_decay, 8)
# res = round(res, 8)
# print((ic_decay.values == res.values.flatten()).all())
#  -----------------------------------------------------------------------
# # factor_regression_analysis
# 原接口regression_analysis，原接口中没有被调用，输出excel里没数据
# res = factor_regression_analysis(factor_data=factor_data,price_use='close', holding_period=1, ret_shift=True,
#                                universe='alpha_universe', params_of_regressor=None)
# print(res)
#  -----------------------------------------------------------------------
# factor_neutralization_calc
# 输出excel里没有该数据
# res = factor_neutralization_calc(factor_data=factor_data, universe='alpha_universe', params_of_regressor=None)
# print(res)
#  -----------------------------------------------------------------------
# factor_standard_process_calc
# 输出excel里没有该数据
# res = factor_standard_process_calc(factor_data=factor_data, universe='alpha_universe', industry_type='CITIC_I', fillna=False,
#                                  median=False, standard=False)
# print(res)
#  -----------------------------------------------------------------------
# # factor_segment_test
# # 导出旧接口factor_test.py--670行factor_data: factor_data.to_pickle('/app/mount/code/CGW/DayFactorBacktest_test/test_datas/mid_factor_data_segment_test.pkl')

# # 老接口
# DayFactorBacktest(start_date, end_date, factor_name, factor_data_ori, result_folder, universe='alpha_universe',
#                     benchmark='alpha_universe', transaction_cost=None, holding_period=1, segment_number=10,
#                     median=False, standard=False, fillna=True, seg_by_industry=False, industry_type='CITIC_I')
# ori_res_path = '/app/mount/code/CGW/DDDDD/nw_total_share_pct/FactorBacktest_nw_total_share_pct.xlsx'
# segment_test = pd.read_excel(ori_res_path, sheet_name='seg_return')
# print('----------')
# segment_test.set_index('mddate', inplace=True)
# print(segment_test)

# # 新接口
# factor_data_new = pd.read_pickle('/app/mount/code/CGW/DayFactorBacktest_test/test_datas/mid_factor_data_segment_test.pkl')
# factor_data_new.index = [dt.strftime(x, '%Y%m%d') for x in factor_data_new.index]
# res = factor_segment_test(factor_pd=factor_data_new, price_use='vwap', holding_period=1, universe='alpha_universe',
#                         benchmark='alpha_universe', segment_num=10,
#                         handle_insufficient=False, handle_return_outlier=False, return_bucket_ic=False,
#                         transaction_cost=None, max_quantile=None, by_industry=False, industry_type='CITIC_I')
# print(res)

# # 新旧结果比较
# segment_test.fillna(0, inplace=True)
# res.fillna(0, inplace=True)
# print((segment_test.index == res.index).all().all())
#  -----------------------------------------------------------------------
# # factor_segment_performance_measure
# # 导出旧接口factor_test.py--671行factor_data: factor_data.to_pickle('/app/mount/code/CGW/DayFactorBacktest_test/test_datas/mid_factor_data_factor_segment_performance_measure.pkl')

# # 老接口
# DayFactorBacktest(start_date, end_date, factor_name, factor_data_ori, result_folder, universe='alpha_universe',
#                     benchmark='alpha_universe', transaction_cost=0.0013, holding_period=1, segment_number=10,
#                     median=True, standard=True, fillna=False, seg_by_industry=False, industry_type='CITIC_I')
# ori_res_path = '/app/mount/code/CGW/DDDDD/nw_total_share_pct/FactorBacktest_nw_total_share_pct.xlsx'
# seg_return_after_cost_stat = pd.read_excel(ori_res_path, sheet_name='seg_return_after_cost_stat')
# print('----------')
# seg_return_after_cost_stat.set_index('Unnamed: 0', inplace=True)
# print(seg_return_after_cost_stat.head())

# # 新接口
# factor_data = pd.read_pickle('/app/mount/code/CGW/DayFactorBacktest_test/test_datas/mid_factor_data_factor_segment_performance_measure.pkl')
# factor_data.index = [dt.strftime(x, '%Y%m%d') for x in factor_data.index]
# res = factor_segment_performance_measure(factor_pd=factor_data, price_use='vwap', holding_period=1, universe='alpha_universe',
#                                        benchmark='alpha_universe', segment_num=10,
#                                        handle_insufficient=False, handle_return_outlier=False,
#                                        transaction_cost=0.0013, max_quantile=None,
#                                        by_industry=False, industry_type='CITIC_I', interest_type='cumprod')
# print(res.head())

# # # 新旧结果比较
# seg_return_after_cost_stat.fillna(0, inplace=True)
# res.fillna(0, inplace=True)
# seg_return_after_cost_stat = round(seg_return_after_cost_stat, 8)
# res = round(res, 8)
# print((seg_return_after_cost_stat.values == res.values).all())
#  -----------------------------------------------------------------------
# factor_winsorized_mean
# data1 = pd.Series(np.random.randint(1,10,1000)).tolist()
# data2 = data1 + [10000]*3
# print(round(np.mean(data1),3))
# print(round(np.mean(data2),3))
# res = factor_winsorized_mean(data=data2, cut_range=(3, 97))
# print(res)

#  -----------------------------------------------------------------------
# # factor_distribution_calc
# # 导出旧接口factor_test.py--597行factor_data: self.data['factor_data'].to_pickle('/app/mount/code/CGW/DayFactorBacktest_test/test_datas/mid_factor_data_factor_distribution_calc.pkl')

# # 老接口
# DayFactorBacktest(start_date, end_date, factor_name, factor_data_ori, result_folder, universe='alpha_universe',
#                     benchmark='alpha_universe', transaction_cost=0.0013, holding_period=1, segment_number=10,
#                     median=True, standard=True, fillna=False, seg_by_industry=False, industry_type='CITIC_I')
# ori_res_path = '/app/mount/code/CGW/DDDDD/nw_total_share_pct/FactorBacktest_nw_total_share_pct.xlsx'
# distribution = pd.read_excel(ori_res_path, sheet_name='distribution')
# print('----------')
# print(distribution)

# # 新接口
# factor_data = pd.read_pickle('/app/mount/code/CGW/DayFactorBacktest_test/test_datas/mid_factor_data_factor_distribution_calc.pkl')
# factor_data.index = [dt.strftime(x, '%Y%m%d') for x in factor_data.index]
# res = factor_distribution_calc(factor_data=factor_data, universe='alpha_universe', seg_benchmark='alpha_universe' )
# print(res)

# # 新旧结果比较
# distribution.fillna(0, inplace=True)
# res.fillna(0, inplace=True)
# distribution = round(distribution, 8)[0]
# res = round(res, 8)[0]
# print((distribution.values == res.values).all())
#  -----------------------------------------------------------------------
