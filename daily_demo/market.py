import pandas as pd
import os
#pd.set_option('display.max_columns', None)
#from MDCDataProvider import DataProvider as MarketData
from xquant.marketdata import MarketData
from MDCDataProvider.HBaseProvider_to_MDC import HBaseProvider_to_MDC as MarketData1
#from MDCDataProvider import HBaseProvider_to_MDC as MarketData1
#from MDCDataProvider import HBaseProvider as MarketData1

import pickle


#from MDCDataProvider import HBaseProvider as MarketData
import time
ma = MarketData()
#ma1 = MarketData1()


#result_1 = ma.get_stock_data_day('SZ', '20211220', 'Order')
#print(result_1.shape)
#raise Exception()

#df =  ma.get_data_by_time_frame("Transaction", "002703.SZ", "20220228 090000000", '20220228 130000000' )
#df =  ma.get_data_by_time_frame("Order", "688001.SH", "20200101 090000000", '20200130 150000000' )
#print(df.to_parquet("/data/user/013150/tmp/688001_order.parquet"))
#print(df.shape)

#df =  ma.get_data_by_time_frame("KLine1m4zt", "601688.SH", "20220818 090000000", '20220818 150000000')

t1 = time.time()
df =  ma.get_data_by_date("STOCK", "688599.SH", '20230526')
print(df)
print(time.time()-t1)

t1 = time.time()
df =  ma.get_data_by_date("STOCK", "688599.SH", '20230526')
print(df)
print(time.time()-t1)

df.to_parquet("688599_20230526.pqt")
raise Exception()

#print(df.to_parquet("/data/user/013150/tmp/688001_trans.parquet"))
#print(df)
#print(11111111111111111111111111111111111111111111111111)
#df =  ma.get_data_by_time_frame("Transaction", "601688.SH", "20220214 090000000", '20220214 130000000' )
#print(df.shape)
#df = ma1.get_data_by_date("Stock", "000001.SZ", "20220704")
#print(df)

#pickle.dump(df, open("df.pkl", "wb"))
raise Exception()



#t1 = time.time()
#stock = '000002.SZ'
#date = '20210507'
#(pid=274431) 20200227 STOCK 600077.SH data not consist: hdfs 2657 vs hbase 2654!

#df = ma.get_data_by_date("Kline1M4ZT", stock, date)
#print(df)
#print(set(df['TradingPhaseCode'].tolist()))
#raise Exception()



#df1 = ma1.get_data_by_date("Stock", stock, date)

#df = df.reindex(columns = ["MDDate", "MDTime", "HTSCSecurityID","OpenPx","ClosePx"])
#print(df["MDTime"].iloc[0:510])
print(df.shape, df1.shape)
df.to_csv("hdfs_{}.csv".format(stock))
df1.to_csv('hbase_{}.csv'.format(stock))
os.system("""curl ftp://168.8.2.60/013150/ -T hbase_{}.csv -u 'htzq:htzq'""".format(stock))
print(time.time()-t1)
raise Exception()
#time.sleep(10)
t1 = time.time()
df = ma.get_data_by_date("Stock", "000001.SZ","20201218")
print(df.shape)
#df.to_csv("tmp.csv")
print(time.time()-t1)

t1 = time.time()
df = ma.get_data_by_date("Stock", "000001.SZ","20201218")
print(df.shape)
#df.to_csv("tmp.csv")
print(time.time()-t1)


raise Exception()



ma = MarketData()
#print(1)
#df = ma.get_data_by_date("Stock", "000001.SZ","20200819")
#print(list(df.columns))
#df["MDTime"] = df["MDTime"].apply(lambda x: x.zfill(9))
#df = df[(df["MDTime"] >= '092500000') &  (df['MDTime'] <= '1500000')]
#df = df[(df["MDTime"] <= '113000000') | (df['MDTime'] >= '1300000')]
#print(df.shape)
#df.to_csv("000001.csv")
#
#
#raise Exception()
#columns = ['HTSCSecurityID',
# 'MDTime',
# 'MDDate',
# 'OpenPx',
# 'ClosePx',
# 'HighPx',
# 'LowPx',
# 'NumTrades',
# 'TotalVolumeTrade',
# 'TotalValueTrade']
#df = df.reindex(columns=columns)
#print(df.head())
##df.to_csv("market.csv")
#print (df.loc[995:1000,])
#print([len(i.split("|"))for i in df.loc[995:1000,"Sell1OrderDetail"]])
#print("time: ", time.time()-t1)
#t1 = time.time()
#df = ma.get_data_by_date("Transaction", "000725.SZ","20190701")
#print('get_data_by_date:\n',df.head(2))
#raise Exception()
#print("time: ", time.time()-t1)
#t1 = time.time()
#new_ma = MarketData()
#df = new_ma.get_data_by_date("Index", "000905.SH","20191028")
#print(df)
#print("time: ", time.time()-t1)

#df = ma.get_data_by_date("STOCK", "601688.SH", "20170331")
#print(df)
#df.to_csv('tmp.csv')
#raise Exception()

#df = ma.get_data_by_time_frame("Stock", "603208.SH", "20200930 090000000", '20200930 160000000', trading_phase_code=["3"] )
df = ma.get_data_by_date("Stock", "603208.SH", "20200930")
print(df.iloc[10:15])
df.to_csv('stock.csv')
#raise Exception()

df = ma.get_data_by_date("Transaction", "000001.SZ", "20190107" )
print(df.iloc[10:15])
df.to_csv('transaction.csv')
raise Exception()

df = ma.get_data_by_year_month("KLINE1M4ZT", "000001.SZ", "201901")
print(df.iloc[10:15])
df.to_csv('tmp2.csv')

raise Exception()


#df1 = ma.get_data_by_time_frame('Kline1M4ZT', '000001.SZ', '20191127 092459999', '20191127 100000000')
#df2 = ma.get_data_by_time_frame('Kline1M4ZT', '000001.SZ', '20191128 092459999', '20191128 100000000')
#df1 = ma.get_data_by_time_frame("Index", "000905.SH",'20190{}01 092459999'.format(1), '20190{}31 093500000'.format(1))
#print(df1.loc[0, 'PreClosePx'])
#print('get_data_by_time_fram',df1.head())
#print(len(df1))
#print(df2.head())
#print(len(df2))

# df2 = ma.get_data_by_time_frame('Transaction','000001.SZ','20180301 093000000','20180305 150000000')
# print('Transaction',df2.head())
# 
# df3 = ma.get_data_by_time_frame('Order','000001.SZ','20180301 093000000','20180305 150000000')
# print('Order\n',df3.head())
# 
df4 = ma.get_data_by_time_frame('Stock','000001.SZ','20190701 083000000','20190701 180000000')
print('Stock',df4)

df4.loc[:, 'ClosePx'].to_csv("tt.csv")
