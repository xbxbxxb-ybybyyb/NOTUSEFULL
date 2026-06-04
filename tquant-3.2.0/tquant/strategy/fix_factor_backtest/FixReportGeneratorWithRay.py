import os
os.environ['DSWMAP_envTag'] = 'uat'
os.environ['ENV_VERSION'] = ''
import sys
sys.path.append('..')
sys.path.append("../..")
import ray

CUR_PATH = os.path.abspath(os.path.dirname(__file__))
ROOT_PATH = os.path.split(CUR_PATH)[0]
sys.path.append(ROOT_PATH)
import pickle
import pandas as pd
import datetime as dt
from fix_factor_backtest.backtest.test_data_loader import adapt_for_symbol
from fix_factor_backtest.backtest.FactorTest.SingleIntraFactorTest import SingleFactorTest as FixFactorTest


"""
并行回测日内固定时点因子，需要机器至少8核，内存32GB
"""
sys.path.insert(0, '/data/group/800080/factor_pkl_data/FIX/')

# FIX因子值路径
factor = 'SampleMinuteFactor'
factor_path = '/data/group/800080/factor_pkl_data/FIX/{0}.pkl'.format(factor)
report_address = "/data/group/800080/factor_report/FIX/"

# 请确保check_date_list和检测区间匹配；check_date_list的第1天应该是start_date对应的2年后
holding_period = 1
intraday_price_type = 'twap_30_5'
check_date_list = [20160630, 20161231, 20170630, 20171231, 20180630, 20181231, 20190630]
universe = 'alpha_universe'  # 目前可选范围：alpha_universe, risk_universe, index_300, index_500, index_800或index_50
outlier_filter_method = 'MAD'  # "3Std"或"MAD"
stock_cost_rate = 4e-4  # 交易成本
# 测试时将股票依因子值分成10层
group_num = 10
neutral_factors = {'size', 'industry3'}

# 在生成报告前需先生成因子数据，FIX因子有7个时间点需要测试
# 因子文件里应存储一个有所有时间点因子值DataFrame的Dictionary 如:{Fix1300_factorname: dataframe}
with open(factor_path, 'rb') as f:
    factor_dataset = pickle.load(f)
print(len(factor_dataset))  # factor_dataset是一个长度为时点数的Dictionary, 输出7


@ray.remote
def generate_fix_report(factor_name, factor_value):
    factor_value, start_date, end_date = adapt_for_symbol(factor_name, factor_value, check_date_list,
                                                          is_day_factor=False)
    print("Start fix factor backtest", factor_name)
    fix_factor_test = FixFactorTest(factor_name, factor_value, start_date, end_date, check_date_list, report_address,
                                    holding_period=holding_period, group_num=group_num,
                                    intraday_price_type=intraday_price_type, universe=universe,
                                    neutral_factor_set=neutral_factors, outlier_filtering_method=outlier_filter_method,
                                    stock_cost_rate=stock_cost_rate)
    t1 = dt.datetime.now()
    # 运行报告生成程序
    fix_factor_test.launch_test()
    t2 = dt.datetime.now()
    print("fix factor backtest", factor_name, "costs", t2 - t1)


# 目前只能对每个时间点生成一份独立的因子报告，共需生成7份报告
ray.init(num_cpus=8)
task_ids = []
for factor_name, factor_value in factor_dataset.items():
    task_ids.append(generate_fix_report.remote(factor_name, factor_value))

task_results = ray.get(task_ids)
ray.shutdown()
