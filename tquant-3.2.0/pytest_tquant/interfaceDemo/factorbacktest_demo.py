
import time
import pandas as pd
from tquant.strategy.day_factor_backtest.FactorBacktest import DayFactorBacktest
from tquant import StockData
from tquant import BasicData
# 回测开始日期
start_date = 20180102

# 回测截至日期
end_date = 20190630


sd = StockData()
bd = BasicData()
tradingdate = bd.get_trading_day(end_date, -5)[-1]
stock_list = sd.get_plate_info('MARKET', tradingdate, 'ALLA_HIS')['stock'].tolist()
factor_name = "barra_cne6_size"
factor_data =sd.get_factor_barrarisk6(stock_list, (str(start_date), str(end_date)), [factor_name])

# 回测结果路径
result_folder = '/home/appadmin/'
t_start = time.time()
DayFactorBacktest(start_date, end_date, factor_name, factor_data, result_folder)
print('backtest time cost: ', str(time.time() - t_start))
