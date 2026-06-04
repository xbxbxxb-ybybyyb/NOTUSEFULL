from xquant.futuredata import FutureData
import pandas as pd
pd.set_option('display.max_columns', None)
fd = FutureData()



result = fd.get_change_date('IC','20230130','ZL00', data_source = "MYSQL")
print(result)
raise Exception()

df = fd.get_contract_zl_info('IF','20200224', '20230111','ZL00')
print(df)
df.to_csv("result.csv")
raise Exception()

result = fd.get_contract_zl_info('TS', '20200624', '20230110', 'ZL00')
result.to_csv("result.csv")
print(result)

result = fd.get_contract_zl_info('T', '20200624', '20230110', 'ZL00')
result.to_csv("result1.csv")
print(result)

raise Exception()

result = fd.get_change_date('IC','20200630','ZL00')
print(result)
raise Exception()


#result = fd.get_instrument_all('ICZL',20161101, "ZL00")
#print(result)
#raise Exception()


result4_0 = fd.get_future_data("ICZL", "20210702 000000000", "20210702 235000000", 'K_1MIN')
print(result4_0)
result4_0.to_csv("result.csv")
#print(result4_0.columns)
raise Exception(0)

result4_1 = fd.get_future_data("TS1912", "20191111 000000000", "20200101 000000000", 'K_1MIN')
result4_1.to_csv("tmp.csv")
print(result4_1.head())
raise Exception()

result4_2 = fd.get_future_data("WHZL", "20180122 000000000", "20180123 000000000", 'TICK')
#result4_2 = fd.get_future_data("IF1803.CF", "20180122 000000000", "20180123 000000000", 'TICK')

print(result4_2.head())
print(result4_2)
print(result4_2.columns)
raise Exception()


#result4_3 = fd.get_future_data("ICZL", "20190101 000000000", "20190201 000000000", 'K_DAY', method=True)
#print(result4_3.head())
result4_4 = fd.get_future_data("IC2003.CF", "20200324 080000000", "20200324 220000000", 'TICK')
print(result4_4.head())

