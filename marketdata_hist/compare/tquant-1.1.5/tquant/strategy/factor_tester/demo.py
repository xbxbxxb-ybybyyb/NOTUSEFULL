import os
import sys
import pandas as pd
import numpy as np

os.environ['DSWMAP_envTag'] = 'uat'
os.environ['DSWMAP_username'] = 'appadmin'
os.environ['ENV_VERSION'] = ''
sys.path.append('../')
sys.path.append("../..")

import tquant.strategy.factor_tester.tester_analysis as Tester

from tquant import StockData
from tquant import BasicData
from tquant.psfactor import PsFactorData
sd = StockData()
bd = BasicData()
tps = PsFactorData()

os.environ['developer'] = 'xxh001_default'
os.environ['scene'] = 'backtest'
os.environ['space_id'] = '8b0c4ac8b572464fb758883f1afdce63'
os.environ['exec_env'] = 'dev-prd'
os.environ['project_id'] = 'ae1ff591f612476f89b52a5cf3e6b8d1'
os.environ['freq'] = 'DAY'
os.environ['factor_name'] = 'alpha_bsc'

# 收益率文件路径
excess_return_path = '/app/mount/factor_return'
# 计算因子文件路径
file_path = '/app/mount/code/'


# start_date='20150102', end_date='20201231'
def factor_tester(start_date='20180102', end_date='20191231'):
    freq = os.environ.get('freq')
    factor_name = os.environ.get('factor_name')
    calc_env = 'research'  # web端检测应改用release
    library_name = '{0}_DAY'.format(os.environ.get('project_id'))
    tradingdate = bd.get_trading_day(end_date, -5)[-1]
    stock_list = sd.get_plate_info('MARKET', tradingdate, 'ALLA_HIS')['stock'].tolist()
    date_list = bd.get_trading_day(start_date, end_date)
    factor_data = tps.get_factor_value_by_library_name(library_name, date_list, [factor_name], stock_list)[
        factor_name]

    factor_data.dropna(axis=0, inplace=True, how='all')
    factor_data[~np.isfinite(factor_data)] = np.nan

    factor_result = {}
    factor_result[factor_name] = factor_data


    if freq == 'DAY':
        test_result = Tester.test(start_date, end_date, factor_result=factor_result,
                                  excess_return_path=excess_return_path)
        print("test_result: ", test_result)
    else:
        test_result = False

    return test_result


if __name__ == "__main__":
    factor_tester()
