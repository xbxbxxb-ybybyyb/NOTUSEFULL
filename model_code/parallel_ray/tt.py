from xquant.factordata import FactorData
s = FactorData()
#默认查全市场股票
df1 = s.get_factor_value('Basic_factor', stock = [], mddate = ['20180808', '20180809'], factor_names = ['pre_close', 'open', 'high'])
print(df1)