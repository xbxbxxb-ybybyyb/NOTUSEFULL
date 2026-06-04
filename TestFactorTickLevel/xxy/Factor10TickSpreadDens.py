"""
011477

"""
from Factor.FactorBase import  FactorBase
#import numpy as np

class Factor10TickSpreadDens(FactorBase):
    def single_stock_factor_generator(self, code, date):
        Tick_data = self.load_data(code, date)
        Tick_data = Tick_data.set_index(['T_Date', 'T_Time'])
#        print(Tick_data.keys())
        #################
        #以下为因子计算逻辑
        spread = Tick_data['T_LastPrice'].rolling(10, min_periods=3).max()-Tick_data['T_LastPrice'].rolling(10, min_periods=3).min()
        vol_mean= Tick_data['T_Volume'].rolling(10, min_periods=3).mean()

        ans = (spread)/vol_mean
#        ans = ans.replace(np.inf, 0)
#        print(ans)

        #返回一个4731行，一列的DataFrame,index为双索引，columns为code
        #################
        ans = ans.to_frame(code)
        ans.index = Tick_data.index

        return ans