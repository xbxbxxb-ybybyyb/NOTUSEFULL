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
def wcx_tick_tradelogic_14_6(DMGRs,PARAs=[]):
  ##
  data = DMGRs['TRANS']
  
  data=data[data['TradePrice']>0]

  trad_qty_buy=data['TradeQty'].groupby(data['TradeBuyNo']).sum()
  
  level_buy=trad_qty_buy.mean()+trad_qty_buy.std()

  data_big_buy=trad_qty_buy[trad_qty_buy>=level_buy]

  trad_qty_sell=data['TradeQty'].groupby(data['TradeSellNo']).sum()
  
  level_sell=trad_qty_sell.mean()+trad_qty_sell.std()

  data_big_sell=trad_qty_sell[trad_qty_sell>=level_sell]

  ##
  data_temp=data[['MDTime','TradePrice']].groupby(data['TradeBuyNo']).mean()

  data_temp=data_temp.sort_values(by='MDTime')

  min_iloc=data_temp['TradePrice'].values.argmin()
  max_iloc=data_temp['TradePrice'].values.argmax()

  ##
  if not gpu: 
      iloc1=np.min([min_iloc,max_iloc])
  else:
      iloc1=int(min([min_iloc,max_iloc]))
      min_iloc = iloc1
      max_iloc = iloc1
      
  print("iloc1:", type(iloc1), type(max_iloc))
  
  if iloc1==min_iloc:
     condition_ch=data_temp.iloc[:max_iloc,:]
  else:
     condition_ch=data_temp.iloc[min_iloc:,:]
  
  print(condition_ch) 
  if not gpu:
      index_con_buy=[x for x in data_big_buy.index if x in condition_ch.index]
      index_con_sell=[x for x in data_big_sell.index if x in condition_ch.index]
  
      ans=data_big_buy[index_con_buy].sum()/data_big_sell[index_con_sell].sum()
  else:
      ans=data_big_buy[data_big_buy.index.isin(condition_ch.index)].sum()/data_big_sell[data_big_sell.index.isin(condition_ch.index)].sum()

  return ans

wcx_tick_tradelogic_14_6(DMGRs, None)
