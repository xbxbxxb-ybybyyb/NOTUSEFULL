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
def wcx_tick_tradelogic_10(DMGRs,PARAs=[]):
  ##
  data = DMGRs['TRANS']
  
  data=data.iloc[np.where(data['TradePrice'].values>0)[0]]
  

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
  
  condition_ch=MDTime.iloc[np.where(MDTime_rank.values>=0.7)[0]]
  
  if not gpu:
      index_con1=[x for x in data_big_return.index if x in condition_ch.index]
      index_con2=[x for x in data_big_return.index if x not in condition_ch.index]

      ans=data_big_return[index_con1].mean()-data_big_return[index_con2].mean()
  else:
      ans=data_big_return[data_big_return.index.isin(condition_ch.index)].mean()-data_big_return[data_big_return.index.isin(condition_ch.index)].mean()

  return ans

wcx_tick_tradelogic_10(DMGRs, None)
