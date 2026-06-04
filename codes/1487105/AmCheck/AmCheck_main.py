import os
import sys
import numpy as np
import pandas as pd
import scipy.io as spio
import sys
sys.path.insert(0,'AmCheck/')
import pf_generator_helper #import *
import update_portfolio
import datetime
import time
import config_path
from xquant.factordata import FactorData
from xquant.xqutils.helper import link
import update_valid_stock

lm = link.LinkMessage()

today_ = datetime.datetime.today().strftime('%Y%m%d')

s = FactorData()
result1 = s.tradingday(today_,10)
today = [i for i in result1 if i>today_][0]

print(today)    

transaction_time = '1500'
update_valid_stock.update_valid_stock(today,transaction_time,pool_stock_path=config_path.pool_stock_path)
lm.sendMessage("@1500 Valid Stock Updated done")

times=['0930vwap','0930','0930vwap300','0930lf']#

    
#time = times[1]
#pf_code = '5160803'
#capital_fake = 80e7
#update_portfolio.update_portfolio(capital_fake,config_path.reb_path,today,time,pf_code,True,mode=1)
#act_vwap_str = pf_generator_helper.get_act_stat(today,time)
#lm.sendMessage("@Test %s act&weight stat:  %s" % (time,act_vwap_str)+','+today)    

time = times[0]
pf_code = '5160503'
capital_fake = 60e7
update_portfolio.update_portfolio(capital_fake,config_path.reb_path,today,time,pf_code,True,mode=1)
act_vwap_str = pf_generator_helper.get_act_stat(today,time)
lm.sendMessage("@Test %s act&weight stat:  %s" % (time,act_vwap_str)+','+today)      

#time = times[2]
#pf_code = '5160304'
#capital_fake = 40e7
#update_portfolio.update_portfolio(capital_fake,config_path.reb_path,today,time,pf_code,True,mode=1,benchmark='300')
#act_vwap_str = pf_generator_helper.get_act_stat(today,time,benchmark='300')
#lm.sendMessage("@Test %s act&weight stat:  %s" % (time,act_vwap_str)+','+today)     

time = times[-1]
pf_code = '5161003'
capital_fake = 6e8
update_portfolio.update_portfolio(capital_fake,config_path.reb_path,today,time,pf_code,True,mode=1)
act_vwap_str = pf_generator_helper.get_act_stat(today,time)
lm.sendMessage("@Test %s act&weight stat:  %s" % (time,act_vwap_str)+','+today)   