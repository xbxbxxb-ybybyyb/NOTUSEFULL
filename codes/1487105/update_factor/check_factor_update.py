import pandas as pd 
import datetime
import time 
from xquant.compute.aimr import AIMR
import sys 
sys.path.insert(0,'update_factor/')
from update_factor_exector import *
from config_path import *

from xquant.xqutils.helper import link
lm = link.LinkMessage()
#today = '20210720'
start_date = today
end_date = today

f_types = ['daily', 'longterm20', 'fundamental_tmp', 'barra']
for f_type in f_types:
    need_factor_list = os.listdir(factor_data_path+'/%s/' % f_type) 
    need_factor_list = [f[:-4] for f in need_factor_list if f.endswith('.pkl')]
    success_update_factors,fail_update_factors = check_factor_update_success(need_factor_list,f_type,start_date,end_date)
    lm.sendMessage('%s Failed factor:%s' % (f_type,str(fail_update_factors)))
    
    
    