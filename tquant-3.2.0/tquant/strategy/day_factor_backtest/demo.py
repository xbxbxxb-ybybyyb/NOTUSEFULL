
import time
import tquant
print(tquant)
import pandas as pd
from tquant.strategy.day_factor_backtest.FactorBacktest import DayFactorBacktest

# 回测开始日期
start_date = '20191001'

# 回测截至日期
end_date = '20191231'

# 因子名称和数据文件
from tquant import StockData
from tquant import BasicData
sd = StockData()
bd = BasicData()
tradingdate = bd.get_trading_day(end_date, -5)[-1]
stock_list = sd.get_plate_info('MARKET', tradingdate, 'ALLA_HIS')['stock'].tolist()
factor_name = "ZaoYinTrader"
factor_data  = pd.read_pickle("../data/ZaoYinTrader.pkl").sort_index()#sd.get_factor_valuation_metrics(stock_list, (str(start_date), str(end_date)), [factor_name])
print(factor_data)
factor_data = factor_data[(factor_data.index > pd.Timestamp(start_date)) & (factor_data.index<pd.Timestamp(end_date))]
print(factor_data)

# 回测结果路径
result_folder = './'
t_start = time.time()
DayFactorBacktest(start_date, end_date, factor_name, factor_data, result_folder)
print('backtest time cost: ', str(time.time() - t_start))
