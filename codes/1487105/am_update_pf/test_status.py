import numpy as np
import pandas as pd
import datetime
from xquant.thirdpartydata.marketdata import MarketData

curr_time = datetime.datetime.now()
time_str = datetime.datetime.strftime(curr_time,'%Y-%m-%d %H:%M:%S')

ma = MarketData()
df = ma.get_am_mdc_constant()
# print(df.head())
today_date = datetime.date.today().strftime('%Y%m%d')
#today_date='20201214'
adj_today=df['mdc_trade_status'][today_date].to_frame()
adj_today.dropna(inplace=True)
trade_stk = adj_today[np.array(adj_today['mdc_trade_status']!='8') \
                & np.array(adj_today['mdc_trade_status']!='6')\
                & np.array(adj_today['mdc_trade_status']!='')].index.tolist()  
print(trade_stk)  
pd.to_pickle(df,'/data/user/012620/AlphaData2/trade_stk_df_%s.pkl' % time_str)                              
pd.to_pickle(trade_stk,'/data/user/012620/AlphaData2/trade_stk_%s.pkl' % time_str)                 