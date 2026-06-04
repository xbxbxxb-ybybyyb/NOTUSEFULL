import pandas as pd
from xquant.factordata import FactorData


fa = FactorData()
code = '000001.SZ'
sel_cols = ['D_Date', 'D_MaxPrice', 'D_MinPrice', 'D_HighPrice', 'D_LowPrice']
data = fa.get_factor_value('ZeusDataLib', code, '20200102', sel_cols)
data = data.set_index('D_Date')

print(data.shape)
