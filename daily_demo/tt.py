from xquant.funddata import FundData
fd = FundData()
result_1 = fd.get_fund_data("518800.SH", "20200202 090000000", "20200302 200000000", 'K_DAY')
print(result_1.head())
