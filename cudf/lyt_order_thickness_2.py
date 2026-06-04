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

def inner_ret(a):
  if len(a)==1:
    return 0
  else:
    return a.iloc[-1]/a.iloc[0]-1

@profile
def lyt_order_thickness_2(DMGRs, PARAs):
  a = DMGRs['TRANS']
  a = a[a['TradeType']==0]

  a_sell = a[a['TradeBSFlag'] == 2]
  idmaxlensell = a_sell['TradePrice'].groupby(a_sell['TradeBuyNo']).apply(lambda x: inner_ret(x))
  tradepricedelta_s =idmaxlensell.mean()



  order_thickness = tradepricedelta_s
  return   order_thickness

lyt_order_thickness_2(DMGRs, None)
