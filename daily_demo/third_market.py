from xquant.thirdpartydata.marketdata import MarketData
import pandas as pd
import time
#pd.set_option('display.max_columns', None)
#pd.set_option('display.max_rows',None)
ma = MarketData()

df = ma.getMDSecurityTickDataFrame("00001.HK","20230411090000","20230411160000", QueryType = 1) 
print(df)
df.to_csv("00001.csv")
raise Exception()

df1 = ma.getMDOrderDataFrame("430047.BJ","20230411090000","20230411150000")
print(df1)

df = ma.getMDTransactionDataFrame("430047.BJ","20230411093000","20230411100000")
print(df1)   

raise Exception()

#df1 = ma.getMDSecurityTickDataFrame("MO2210-C-5300.CF","20221011090000","20221011150000")
#print(df1)

#print("=========================")
#df = ma.getMDSecurityKLineDataFrame("IO2210-C-3300.CF","20221011090000","20221011150000",10,20)
#print(df)

df = ma.getMDSecurityKLineDataFrame("SCHKSBSZ.HT","20230130090000","20230130150000",10,20)
print(df)
raise Exception()

df = ma.getMDOrderDataFrame("000001.SZ","20190701090000","20190701100000")
print(df)
raise Exception()

df1 = ma.getMDOrderDataFrame("101000.SH","20220527090000","20220527150000")
print(df1)
raise Exception()
df = ma.getMDTransactionDataFrame("601688.SH","20210726093000","20210726100000")
print(df1)
print(df)
print(df.shape)
df.to_csv("tt1.csv")
#raise Exception()


df = ma.getKLine4ZTDataFrame("000001.SZ","20210322090000","20210322150000",10,20)
print(df.columns)
#df.to_csv('tmp.csv')
#raise Exception()
df = ma.getMDSecurityTickDataFrame("601688.SH","202112160930000","202112161600000",0)
#print(df.to_csv("tmp.csv"))
print(df)
raise Exception()

#raise Exception()
#t1 = time.time()
#df = ma.getMDSecurityTickDataFrame("300059.SZ","20201215150000","20201215155000",1)
#print(df)
#print(time.time()-t1)
#raise Exception()
#print(df)
#df.to_csv("20190628.csv")
#raise Exception()
#df = ma.getMDSecurityTickDataFrame("MDI801177.HT","20200610090000","20200610150000",2)
#print(df)
#print(df.to_csv("tmp.csv"))
#raise Exception()
#df =  ma.getKLine4ZTDataFrame("000001.SH","20210108090000","20210108160000",10,20)
#print(df)
#raise Exception()

#df = ma.getMDSecurityKLineDataFrame("510050.SH","20200526090000","20200526150000",10,20)
#print(df)
#df.to_csv('df.csv')
#raise Exception()


#df = ma.getMDSecurityRecordBySourceTypes(securityIDSource = 102, securityType=1)
#print(df.iloc[100:105, :])

t1 = time.time()
df = ma.getMDTransactionDataFrame("600077.SH","20200421090000","20200421160000")
print(df.shape)
print(time.time()-t1)

t1 = time.time()
df = ma.getMDTransactionDataFrame("000001.SZ","20200421090000","20200421160000")
print(time.time()-t1)

print(df.shape)
#df.to_csv("aa.csv")
raise Exception("")


#df = ma.getMDOrderDataFrame("510050.SH","20171201090000","20171201100000")
#print(df.iloc[10:])

pc = ma.getConstantRecordMdcFactor('IC00.CF')
print(pc)








