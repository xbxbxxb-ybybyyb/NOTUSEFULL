
import time
import pandas as pd
from tquant.strategy.day_factor_backtest.AlgoSingleFactorBacktest import AlgoSingleFactorBacktest

# 回测开始日期
start_date = 20180102

# 回测截至日期
end_date = 20190630

# 因子名称和数据文件
# # 1. 读取本地pkl文件的因子数据
# factor_name = 'AlphaFactor'
# factor_data = pd.read_pickle('../backtest_data/{}.pkl'.format(factor_name))
# factor_data = factor_data[
#     (factor_data.index >= pd.Timestamp(str(start_date))) & (factor_data.index <= pd.Timestamp(str(end_date)))]

# 2. 通过tquant接口取因子数据
from tquant import StockData
from tquant import BasicData
sd = StockData()
bd = BasicData()
tradingdate = bd.get_trading_day(end_date, -5)[-1]
stock_list = sd.get_plate_info('MARKET', tradingdate, 'ALLA_HIS')['stock'].tolist()
factor_name = "ev2"
factor_data =sd.get_factor_valuation_metrics(stock_list, (str(start_date), str(end_date)), [factor_name])
factor_data.reset_index(inplace=True)
factor_data['mddate'] = factor_data['mddate'].apply(pd.Timestamp)
factor_data.set_index(['mddate', 'stock'],inplace=True)
factor_data = factor_data.unstack()[factor_name]

# 回测结果路径
result_folder = '/home/appadmin/'
t_start = time.time()
AlgoSingleFactorBacktest(start_date, end_date, factor_name, factor_data, result_folder)
print('backtest time cost: ', str(time.time() - t_start))
