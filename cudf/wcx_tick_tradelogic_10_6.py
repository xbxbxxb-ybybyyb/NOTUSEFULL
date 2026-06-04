# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import pandas as pds
import sys
from xquant.xqutils.perf_profile import profile

gpu = True if len(sys.argv)>1 else False
df = pds.read_pickle("./000008.SZ_trade.pkl")
if gpu == True:
    import cudf as pd
    df = pd.from_pandas(df)

DMGRs = {}
DMGRs["TRANS"] = df
@profile
def wcx_tick_tradelogic_10_6(DMGRs,PARAs=[]):
  ##
  data = DMGRs['TRANS']
  
  data=data[data['TradePrice']>0]
  

  data['num']=1
  data['flag']=np.arange(0,data.shape[0])
  num_sum=data['num'].groupby(data['TradeBuyNo']).sum()

  num_sum_big=num_sum[num_sum>=3]
  
  data.index=data['TradeBuyNo'] 

  data_big=data.loc[num_sum_big.index,:]
  
  data_big_return=data_big['TradePrice'].groupby(data_big['TradeBuyNo']).apply(lambda x:x.iloc[-1]/x.iloc[0]-1)
  
  ##big    
  trad_qty=data['TradeQty'].groupby(data['TradeBuyNo']).sum()
  
  level=trad_qty.mean()+trad_qty.std()

  data_big_level=trad_qty[trad_qty>=level]  

  data_big_return_ch=data_big_return.iloc[np.where(data_big_return.values>0)[0]] 
  
  ans1=[x for x in data_big_return_ch.index if x in data_big_level.index]
  
  ans=len(ans1)/len(data_big_return_ch.index)
  return ans


wcx_tick_tradelogic_10_6(DMGRs, None)
