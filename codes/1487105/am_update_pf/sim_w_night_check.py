import pandas as pd
import datetime
from xquant.xqutils.helper import link
import sys
sys.path.insert(0,'am_update_pf/')
import config_path
lm = link.LinkMessage()
print(config_path.data_center_path)
today = datetime.date.today().strftime('%Y%m%d')

n = pd.read_pickle('/%s/Department/DailyWeight/benchmark_500/simulation_w_lf.pkl' % config_path.data_center_path)
try:
    lm.sendMessage('%s lf w :%s' % (today,str((n.loc[today]).sum())))
except:
    lm.sendMessage('%s lf w :%s' % (today,'Error!'))

n = pd.read_pickle('/%s/Department/DailyWeight/benchmark_500/simulation_w_vwap.pkl' % config_path.data_center_path)
try:
    lm.sendMessage('%s vwap w :%s' % (today,str((n.loc[today]).sum())))
except:
    lm.sendMessage('%s vwap w :%s' % (today,'Error!'))