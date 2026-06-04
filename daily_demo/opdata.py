from xquant.factordata import FactorData
import pandas as pd
import time

pd.set_option('display.max_columns', None)

fa = FactorData()
days = fa.tradingday('20190701','20191023')
stocks = fa.hset("MARKET","20191021","ALLA")["stock"].to_list()
stocks = [stock.split(".")[0] for stock in stocks]
#df = fa.get_factor_value("operation_data", stocks,['20170106'],["stock_click_num"])
#df = fa.get_factor_value("operation_data",["300129"],days[-5:],["stay_time_avg"])
#df = fa.get_factor_value("operation_data",["300129"],days[-5:],["detract_increase"])
df = fa.get_factor_value("operation_data",["300129"],days[-5:],["follow_increse"])#只有小时数据

#df = fa.get_factor_value("operation_data",["300129"],days[-5:],["stock_click_num_avg"])

print(df.head())
#print(df.loc[:, ['stock_click_num_min_15_00','stock_click_num_over5year']])

print(len(df.columns), df.columns)

