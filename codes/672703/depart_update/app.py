import time
import pandas as pd
import datetime 
import os 
import sys
sys.path.insert(0,'depart_update/')
from update_depart_sample import *
from xquant.factordata import FactorData
s = FactorData()
today = datetime.date.today().strftime('%Y%m%d')
pre_date = s.tradingday(today,-2)[0]
start_date = pre_date
end_date = pre_date
print(pre_date)
for i in range(2,6):
    update_sample(start_date, end_date, mode=i)
