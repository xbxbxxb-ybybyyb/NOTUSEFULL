from xquant.funddata import FundData
fd = FundData()
result_4 = fd.get_fund_data("508066.SH", "20221117 000000000", "20221117 235900000", 'K_1MIN')
print(result_4)

raise Exception()


result4 = fd.get_fund_data("510050.SH", "20221117 000000000", "20221117 235900000", 'Tick')
print(result_4.head())

result4.to_parquet("1.parquet")



result4 = fd.get_fund_data("510050.SH", "20221117 000000000", "20221117 235900000", 'Order')
print(result_4.head())

result4.to_parquet("2.parquet")



result4 = fd.get_fund_data("510050.SH", "20221117 000000000", "20221117 235900000", 'Transaction')
print(result_4.head())


result4.to_parquet("3.parquet")




