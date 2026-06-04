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
def lly_trans_8_skew(DMGRs, PARAs):
    if True:
        fac = DMGRs['TRANS']
        data_df_filter = fac.loc[(fac['TradePrice'] != 0) & (fac['MDTime'] >= 93000000)].copy()
        tmp = data_df_filter['TradeBSFlag'].copy()
        tmp.loc[tmp == 1] = 0
        tmp.loc[tmp == 2] = 1
        a = tmp
        b = a.cumsum()
        c = (b==b.shift(1))
        d = pd.Series(index=c.index)
        d.loc[c] = -1
        d = d*b
        e = d.fillna(method='ffill').fillna(0)
        f = b+e
        g = (f==1).cumsum()
        g.loc[f == 0] = np.nan
        df = pd.DataFrame({'cnt':f,'seq_num':g})
        combined_df = pd.concat([data_df_filter,df],axis=1)
        seq_max_count = combined_df.groupby('seq_num').max()['cnt']
        threshold = seq_max_count.quantile(0.9)
        max_p = combined_df.groupby('seq_num')['TradePrice'].max()
        min_p = combined_df.groupby('seq_num').min()['TradePrice']
        ret = (max_p-min_p)/max_p
        if gpu==False:
            select_idx = seq_max_count.loc[seq_max_count>=threshold].index.tolist()
            ans = ret.loc[select_idx].skew() / ret.skew()
        else:
            ans = ret.loc[seq_max_count.loc[seq_max_count>=threshold].index].skew() / ret.skew()

    else:
        ans = np.nan
    return ans


lly_trans_8_skew(DMGRs, None)
