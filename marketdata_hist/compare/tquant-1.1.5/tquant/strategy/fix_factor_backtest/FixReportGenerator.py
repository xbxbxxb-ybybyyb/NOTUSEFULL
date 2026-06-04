import os
os.environ['DSWMAP_envTag'] = 'uat'
os.environ['ENV_VERSION'] = ''
import sys
sys.path.append("../")
import datetime as dt
import pickle
from fix_factor_backtest.backtest.test_data_loader import adapt_for_symbol
from fix_factor_backtest.backtest.FactorTest.SingleIntraFactorTest import SingleFactorTest

"""
用于回测日频日内固定时点因子
"""
# FIX因子值路径
factor = 'NewCorrHighVol'
factor_path = '/'.join(os.path.abspath(__file__).split('/')[:-2]) + '/data/{0}.pkl'.format(factor)
report_address = "/home/appadmin/"

# SJL 请确保check_date_list和检测区间匹配；check_date_list的第1天应该是start_date对应的2年后
#日期格式是pd.Timestamp
check_date_list = [20191231]
holding_period = 1
intraday_price_type = 'twap_30_5'
universe = 'alpha_universe'  # 目前可选范围：alpha_universe, risk_universe, index_300, index_500, index_800或index_50
outlier_filter_method = 'MAD'  # "3Std"或"MAD"
stock_cost_rate = 4e-4  # 交易成本
factor_need_report = []
tick_time_list = [1000, 1030, 1100, 1300, 1330, 1400, 1430]

# 在生成报告前需先生成因子数据，FIX因子有7个时间点需要测试
# 因子文件里应存储一个有所有时间点因子值DataFrame的Dictionary 如:{Fix1300_factorname: dataframe}
with open(factor_path, 'rb') as f:
    factor_dataset = pickle.load(f)

print(len(factor_dataset))  # factor_dataset是一个长度为时点数的Dictionary, 输出7

# 目前只能对每个时间点生成一份独立的因子报告，共需生成7份报告
for factor_name, factor_value in factor_dataset.items():
    # 转换因子值格式
    factor_value, start_date, end_date = adapt_for_symbol(factor_name, factor_value, check_date_list,
                                                          is_day_factor=False)
    # group_num = 20
    # 测试时将股票依因子值分成10层
    group_num = 10
    is_day_factor = False
    neutral_factors = {'size', 'industry3'}
    print("Start single factor backtest", factor_name)
    singleFactorTest = SingleFactorTest(factor_name, factor_value, start_date, end_date, check_date_list,
                                        report_address, holding_period=holding_period, group_num=group_num,
                                        intraday_price_type=intraday_price_type, universe=universe,
                                        neutral_factor_set=neutral_factors,
                                        outlier_filtering_method=outlier_filter_method, stock_cost_rate=stock_cost_rate)
    t1 = dt.datetime.now()
    # 运行报告生成程序
    singleFactorTest.launch_test()
    t2 = dt.datetime.now()
    print("Single factor backtest", factor_name, "costs", t2 - t1)
    raise Exception()
