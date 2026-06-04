import pandas as pd

from tquant.strategy.day_factor_backtest.backtest.segment_test import segment_test
from tquant.strategy.day_factor_backtest.backtest.utility import align_data_inner
from tquant import StockData
from tquant import BasicData

# 回测开始日期
start_date = 20180102

# 回测截至日期
end_date = 20190630

data_dict = {}

sd = StockData()
bd = BasicData()
tradingdate = bd.get_trading_day(end_date, -5)[-1]
stock_list = sd.get_plate_info('MARKET', tradingdate, 'ALLA_HIS')['stock'].tolist()
factor_name = "barra_cne6_size"
factor_data = sd.get_factor_barrarisk6(stock_list, (str(start_date), str(end_date)), [factor_name])
factor_data.reset_index(inplace=True)
factor_data['mddate'] = factor_data['mddate'].apply(pd.Timestamp)
factor_data.set_index(['mddate', 'stock'], inplace=True)
factor_data = factor_data[factor_name].unstack()
data_dict['factor_data'] = factor_data

holding_period = 3
segment_number = 10
robust_segment = True
transaction_cost = 0.0003
md_dict = {}
md_list = ['close', 'adjfactor']

sub_df = sd.get_factor_price_daily(stock_list, (str(start_date), str(end_date)), ['close', 'adjfactor'], fill_na=True)

sub_close = sub_df['close'].unstack()
sub_adj = sub_df['adjfactor'].unstack()
sub_close_adj = sub_close * sub_adj

price_use = sub_close_adj.shift(-1)
price_use.index = pd.DatetimeIndex(price_use.index)
data_dict['price_use'] = price_use

index_list = ['000300.SH', '000905.SH', '000016.SH']
e_date = str(end_date)
index_price = sd.get_factor_price_daily(index_list, (start_date, e_date), ['close'], fill_na=True)
index_price.reset_index(inplace=True)
index_price.rename(columns={'mddate': 'dt', 'stock': 'Ticker'}, inplace=True)
index_price['dt'] = index_price['dt'].apply(pd.Timestamp)
index_price.set_index(['dt', 'Ticker'], inplace=True)
benchmark_price = index_price.unstack()['close']['000300.SH']
bmk_use = benchmark_price.shift(-1)
data_dict['bmk_use'] = bmk_use

data_dict = align_data_inner(data_dict)

seg_return, seg_return_after_cost = segment_test(data_dict['factor_data'],
                                                 data_dict['price_use'], holding_period,
                                                 data_dict['bmk_use'], segment_number,
                                                 handle_return_outlier=robust_segment,
                                                 transaction_cost=transaction_cost)

print(seg_return)
print(seg_return_after_cost)
