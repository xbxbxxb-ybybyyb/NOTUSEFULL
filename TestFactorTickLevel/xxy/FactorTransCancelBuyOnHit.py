"""
011477

"""
from Factor.FactorBase import  FactorBase
import numpy as np

class FactorTransCancelBuyOnHit(FactorBase):
    def single_stock_factor_generator(self, code, date):
        tick_data, tran_data = self.load_data(code, date, trans=True)
        tick_data = tick_data.set_index(['T_Date', 'T_Time'])
        
        
        #################
        #以下为因子计算逻辑
        def runner(be):
            b, e = be[0], be[1]
            data = tran_data[b:e]
            cancel_data = data[data['TR_TradeType'] == 0]
            trans_deal = data[data['TR_Price'] != 0]
            if data is None:
                return np.nan
            else:
                index_a = trans_deal[trans_deal['TR_BSFlag'] == 1].index
                price_a = trans_deal.loc[index_a, 'TR_Price'].max()
                
                index_b = cancel_data[cancel_data['TR_Price'] < price_a].index
                vol_b =cancel_data.loc[index_b, 'TR_Volume'].sum()
#                index_b = vol_a[vol_a['TR_Price'] >tran_data[b:e]['T_LastPrice']].index
#                pct = vol_a.loc[index_b,'TR_Volume'].sum()/vol_a
            return vol_b
        ans = tick_data[['T_TSIndex','T_TEIndex']].apply(runner, axis=1)/tick_data['T_Volume'].rolling(5, min_periods=3).sum()

        return ans       