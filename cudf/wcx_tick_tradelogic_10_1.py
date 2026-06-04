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
def wcx_tick_tradelogic_10_1(DMGRs,PARAs=[]):
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
    
  ans=(data_big_return>0).sum()/data_big_return.shape[0]

  return ans


wcx_tick_tradelogic_10_1(DMGRs, None)
