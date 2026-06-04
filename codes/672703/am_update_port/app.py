import datetime 
import pandas as pd
import sys
sys.path.insert(0,'am_update_port/')
import update_basic_data
import update_tool 
import update_factor
import update_sample
from xquant.factordata import FactorData
s = FactorData()
today = datetime.date.today().strftime('%Y%m%d')
today = s.tradingday(today,-1)[0]
print(today)
start_date = today 
end_date = today 
factor_flag = 0
mode = [1]
if factor_flag==1:
    update_basic_data.update_basic_data(start_date,end_date)
    update_tool.update_tool()
    update_factor.update_hfactor(start_date,end_date)

for m in mode:
    update_sample.update_sample(start_date,end_date,m)
