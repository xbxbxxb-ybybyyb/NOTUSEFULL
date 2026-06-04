# _*_ coding:utf-8 _*_

from Data_utils import data_interface
from db import OPMysql
import datetime as dt
pool = OPMysql().get_pool()
conn = pool.connection()
DI  = data_interface(conn)

# get_prices
t1 = dt.datetime.now()
result = DI.get_prices(['000010.SZ','000014.SZ'],count=3000,end_date='20180121')

print(result)#.loc['open'].loc[:,'000010.SZ']
t2 = dt.datetime.now()
print("查询时间：%s "%(t2-t1))


