import pandas as pd
import numpy as np
from utils import *
        

def read_tick(p):
    try:
        df_tick = pd.read_pickle(p)
        df_tick['tagShort'] = -df_tick['tagShort']
        df_tick['T_Time'] = np.around(df_tick['T_Time'].astype('float64')/1000)
        df_tick['T_Volume_60'] = df_tick['T_Volume'].rolling(min_periods=1,window=60).sum()
        df_tick['T_LastPrice_60'] = df_tick['T_LastPrice'].rolling(min_periods=1,window=60).mean()
        time_dct = {i:1 for i in range(91500,93000)}
        time_dct.update({i:1 for i in range(93000,100000)})
        time_dct.update({i:2 for i in range(100000,113000)})
        time_dct.update({i:3 for i in range(113000,143000)})
        time_dct.update({i:4 for i in range(143000,150001)})
        df_tick['T_TimeSlot'] = df_tick['T_Time'].map(lambda x:time_dct[x])
        return df_tick
    except OSError:
        print(p, ' bad address')
        return pd.DataFrame()
    
def read_order(p):
    try:
        df_order = pd.read_pickle(p)
        df_order['O_Time'] = df_order['O_Time'].astype('float64')
        df_order['T_Time'] = np.floor(df_order['O_Time']/1000)
        df_order['O_AskVolume'] = df_order['O_Volume']*(df_order['O_BSFlag']==2)
        df_order['O_BidVolume'] = df_order['O_Volume']*(df_order['O_BSFlag']==1)
        df_order['O_AskAmount'] = df_order['O_Price']*df_order['O_AskVolume']
        df_order['O_BidAmount'] = df_order['O_Price']*df_order['O_BidVolume']        
        df_order['T_Code'] = p[-31:-25]+'.SZ'
        df_order.rename(columns={'O_Date':'T_Date'},inplace=True)
        return df_order
    except OSError:
        print(p, ' bad address')
        return pd.DataFrame()
    
def read_trade(p):
    try:
        df_trade = pd.read_pickle(p)
        df_trade['TR_Time'] = df_trade['TR_Time'].astype('float64')
        df_trade['T_Time'] = np.floor(df_trade['TR_Time']/1000)
        df_trade['L_Time'] = np.ceil(df_trade['TR_Time']/1000)
        df_trade['T_Code'] = p[-31:-25]+'.SZ'
        df_trade['Traded_Volume'] = df_trade['TR_Volume']*(df_trade['TR_TradeType']==0)
        df_trade['WD_Volume'] = df_trade['TR_Volume']*(df_trade['TR_TradeType']==1)
        df_trade['Traded_AskVolume'] = df_trade['Traded_Volume']*(df_trade['TR_BSFlag']==2)
        df_trade['Traded_BidVolume'] = df_trade['Traded_Volume']*(df_trade['TR_BSFlag']==1)
        df_trade['Traded_PureBidVolume'] = df_trade['Traded_BidVolume']-df_trade['Traded_AskVolume']
        df_trade['WD_AskVolume'] = df_trade['WD_Volume']*(df_trade['TR_BSFlag']==2)
        df_trade['WD_BidVolume'] = df_trade['WD_Volume']*(df_trade['TR_BSFlag']==1)
        df_trade['WD_PureBidVolume'] = df_trade['WD_BidVolume']-df_trade['WD_AskVolume']
        df_trade.rename(columns={'TR_Date':'T_Date','TR_Amount':'Traded_Amount'},inplace=True)
        
        drop_cols = ['TR_Volume', 'TR_Timestamp', 'TR_TradeIndex']
        save_cols = [i for i in df_trade.columns if i not in drop_cols]
        return df_trade[save_cols]
    except OSError:
        print(p, ' bad address')
        return pd.DataFrame()

def read_data(p,PDM=None,PTM=None,YDM=None):
    p1,p2,p3 = p
    df_tick = read_tick(p1)
    df_order = read_order(p2)
    df_trade = read_trade(p3)
    
    return list_df
    
