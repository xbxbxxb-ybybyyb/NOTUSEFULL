"""
011477

"""
from Factor.FactorBase import  FactorBase

class FactorTickAmtBid(FactorBase):
    def single_stock_factor_generator(self, code, date):
        Tick_data = self.load_data(code, date)
        Tick_data = Tick_data.set_index(['T_Date', 'T_Time'])
#        print(Tick_data.keys())
        #################
        #以下为因子计算逻辑
        ans_prior = (Tick_data['T_BidVolume'][-5][-5:-1].sum())
        ans_current= (Tick_data['T_BidVolume'][-1][-5:-1].sum())
        
        ans = ans_prior / ans_current * Tick_data['T_Volume'].rolling(5, min_periods=3).mean()
        #################
        ans = ans.to_frame(code)
        ans.index = Tick_data.index
        
        return ans