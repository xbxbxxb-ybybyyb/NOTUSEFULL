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
def wcx_tick_tradelogic_10_3(DMGRs,PARAs=[]):
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
    
  ##condition
  MDTime=data_big['MDTime'].groupby(data_big['TradeBuyNo']).mean()
  
  MDTime_rank=MDTime.rank(pct=True)
  
  condition_ch=MDTime[MDTime_rank>=0.7]
  
  
  if not gpu:
      index_con1=[x for x in data_big_return.index if x in condition_ch.index]

      ans=(data_big_return[index_con1]>0).sum()/len(index_con1)
  else:

      ans=(data_big_return[data_big_return.index.isin(condition_ch.index)]>0).mean()

  return ans


wcx_tick_tradelogic_10_3(DMGRs, None)
