import datetime 
import pandas as pd
import sys
import update_sample
from xquant.factordata import FactorData
s = FactorData()
today = datetime.date.today().strftime('%Y%m%d')
today = s.tradingday(today,-1)[0]
#today = '20211029'
print('update team sample',today)
start_date = today 
end_date = today 
update_sample.update_sample(start_date,end_date,1)
update_sample.update_lf_sample(start_date,end_date)