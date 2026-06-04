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
def buyorder_withdraw_tsstat8_v1(DMGRs, PARAs):
  '''
  主买订单撤单时的时序统计量：
  连撤单的相连数均值
  '''
  a = DMGRs['TRANS']
  if a['TradeType'].mean()<0.001:
    return np.nan
  themin = a['MDTime'].apply(lambda x: x // 100000)
  a = a[themin>=930]
  type_diff = a['TradeType'].diff()
  is_con_wd = type_diff.copy()
  is_con_wd[:] = 0
  is_con_wd[(a['TradeType'].values == 1)&(a['TradeBSFlag'].values==1)]  = 1
  is_con_wd_cum = is_con_wd.cumsum()
  is_con_wd_cum_bk = is_con_wd_cum.copy()
  is_con_wd_cum_bk[is_con_wd==1] = np.nan
  is_con_wd_cum = is_con_wd_cum-is_con_wd_cum_bk.fillna(method='ffill')
  start_of_con_wd = is_con_wd_cum==1
  start_of_con_wd[start_of_con_wd==0] = np.nan
  start_of_con_wd = start_of_con_wd.rank(method='first')
  start_of_con_wd[is_con_wd!=1] = 0
  con_wd=start_of_con_wd.fillna(method='ffill')
  con_wd[con_wd==0] = np.nan

  alpha = con_wd.groupby(con_wd).count().mean()
  return   alpha

buyorder_withdraw_tsstat8_v1(DMGRs, None)

