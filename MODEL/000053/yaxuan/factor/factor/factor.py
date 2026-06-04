import pandas as pd
import numpy as np
from multiprocessing.pool import Pool
from utils import *
from data_prepare import *
    

def tick_trend(df_tick,PDM=None):
    df_tick['OpenProfit'] = df_tick['T_PreviousClose']/df_tick['T_OpenPrice']  
    df_tick['IndayPriceMean'] = df_tick['T_LastPrice'].rolling(min_periods=1,window=len(df_tick)).mean()
    df_tick['Trend'] = np.sign(df_tick['T_LastPrice']-df_tick['IndayPriceMean'])
    df_tick['Trend'] = df_tick['Trend'].rolling(min_periods=1,window=len(df_tick)).sum()/np.arange(len(df_tick))
    df_tick['Trend_UpBar'] = (df_tick['T_LastPrice']-df_tick['IndayPriceMean'])*2*(df_tick['Trend']<0)/df_tick['T_LastPrice']
    df_tick['Trend_DownBar'] = (df_tick['IndayPriceMean']-df_tick['T_LastPrice'])*2*(df_tick['Trend']>0)/df_tick['T_LastPrice']
    
    cols_1 = ['Trend','Trend_UpBar','Trend_DownBar']
    df_tick[cols_1] = df_tick[cols_1].fillna(1)
    return df_tick[['T_Time']+cols_1]
                