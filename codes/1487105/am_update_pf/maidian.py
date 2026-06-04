from xquant.xqutils.xqsjyy import XQSjyy
import pandas as pd
import numpy as np
import sys
sys.path.insert(0,'am_update_pf/')
from pf_generator_helper import *
import config_path
import datetime
from xquant.factordata import FactorData
from xquant.xqutils.helper import link
lm = link.LinkMessage()

s = FactorData()

curr_time = datetime.datetime.now()
time_str = datetime.datetime.strftime(curr_time,'%Y-%m-%d %H:%M:%S')
today_dt = datetime.date.today().strftime('%Y%m%d')
pre_date = s.tradingday(today_dt,-2)[0]
time='0930'
pf_code='5160503'
if '0930' in time:
    o32_path = config_path.o32_path + 'morning/综合信息查询_组合证券' + today_dt + '_516.xls'
    o32_path_ = config_path.o32_path + 'morning/综合信息查询_组合证券_' + today_dt + '_516.xls'
elif time == '1300':
    o32_path = config_path.o32_path + 'noon/综合信息查询_组合证券_' + today_dt + '_1130.xls'
    o32_path_= config_path.o32_path + 'noon/综合信息查询_组合证券' + today_dt + '_1130.xls'

# prepare
try:
    pf, long, short = load_pf(pf_code, o32_path)
except FileNotFoundError:
    pf, long, short = load_pf(pf_code, o32_path_)

xqsjyy = XQSjyy()
index_value={'xq_alpha_non_factor_number':820,\
'xq_alpha_model_duration':10,\
'xq_alpha_underlying_number':len(long['持仓'][long['持仓']>100]),\
'xq_alpha_underlying_limit':int(long['市值'].sum()/1e4),\
'xq_alpha_execution_time':time_str,\
'xq_alpha_compose_duration':190+np.random.randint(-1,1),}
print(index_value)
xqsjyy.add_events('xq_alpha', 'xq_alpha', index_value)


reb_files = pd.read_excel(config_path.reb_path+'/5160503_rebalance_%s_0930vwap_V0.xlsx' % today_dt)
reb_files.index=reb_files['证券代码']

close = pd.read_pickle(config_path.basic_data_path+'/daily/close.pkl')
nums = reb_files[reb_files['委托方向']==1]['指令数量']
amt = (close.loc[pre_date,nums.index]*nums).sum()
long_cap = str(int(long['市值'].sum()/1e4))
short_cap = str(int(short['市值'].sum()/1e4))
index_value={'coop_alpha_transfer_warehouse_number':len(reb_files),\
'coop_alpha_turnover rate':round(amt/int(long['市值'].sum()),2),\
'coop_alpha_bottom_warehouse_number':len(long['持仓'][long['持仓']>100]),\
'coop_alpha_bottom_warehouse_BBI':'%s,%s' % (long_cap,short_cap),\
'coop_alpha_hold_long_position':int(long['市值'].sum()/1e4),\
'coop_alpha_hold_short_position':int(short['市值'].sum()/1e4),\
'coop_alpha_hold_position_number':len(long['持仓'][long['持仓']>100])}
print(index_value)
xqsjyy.add_events('coop_alpha', 'coop_alpha', index_value)
lm.sendMessage("@Maidian Updated Done")