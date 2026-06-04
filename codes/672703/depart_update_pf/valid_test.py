import time
import pandas as pd
time1 = time.time()
import datetime 
import os 
import sys
sys.path.insert(0,'am_update_pf/')
import update_basic_data
import update_tool 
import update_factor
import update_sample
import update_model_predict
import config_path 
import pf_generator_helper
import update_valid_stock
import update_portfolio
import open_portfolio
from xquant.xqutils.helper import link
lm = link.LinkMessage()

today = datetime.datetime.today().strftime('%Y%m%d')
transaction_time = '0930'

# update valid stock
update_valid_stock.update_valid_stock(today,transaction_time,pool_stock_path=config_path.pool_stock_path,label_test=True)
lm.sendMessage("@Test AM Valid Stock Updated done")

