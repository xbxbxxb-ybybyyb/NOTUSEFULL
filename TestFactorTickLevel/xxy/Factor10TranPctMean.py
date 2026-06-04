"""
011477

"""
from Factor.FactorBase import  FactorBase
import numpy as np

class Factor10TranPctMean(FactorBase):
    def single_stock_factor_generator(self, code, date):
        tick_data, tran_data = self.load_data(code, date, trans=True)
        tick_data = tick_data.set_index(['T_Date', 'T_Time'])
        
        
        #################
        #以下为因子计算逻辑
        def runner(be):
            b, e = be[0], be[1]
            data = tran_data[b:e]
            data = data[data['TR_Price'] != 0]
            if data is None:
                return np.nan
            else:
                index_a = data[data['TR_BSFlag'] == 1].index
                vol_a = data.loc[index_a, 'TR_Volume'].sum()
#                index_b = vol_a[vol_a['TR_Price'] >tran_data[b:e]['T_LastPrice']].index
#                pct = vol_a.loc[index_b,'TR_Volume'].sum()/vol_a
            return vol_a
        ans = tick_data[['T_TSIndex','T_TEIndex']].apply(runner, axis=1)/tick_data['T_Volume'].rolling(10, min_periods=5).mean()

        return ans       