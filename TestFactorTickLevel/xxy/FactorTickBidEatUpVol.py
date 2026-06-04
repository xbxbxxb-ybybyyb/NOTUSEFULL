"""
011477

"""
from Factor.FactorBase import  FactorBase

class FactorTickBidEatUpVol(FactorBase):
    def single_stock_factor_generator(self, code, date):
        Tick_data = self.load_data(code, date)
        Tick_data = Tick_data.set_index(['T_Date', 'T_Time'])
#        print(Tick_data.keys())
        #################
        #以下为因子计算逻辑
        ans_vol = (Tick_data['T_BidVolume'][-5][-3:-1].sum()-Tick_data['T_BidVolume'][-1][-3:-1].sum())
        ans_PxChg = Tick_data['T_LastPrice'].rolling(20, min_periods=3).max()/Tick_data['T_LastPrice'].rolling(20, min_periods=3).min()-1
        ans = ans_vol/ans_PxChg
        #返回一个4731行，一列的DataFrame,index为双索引，columns为code
        #################
        ans = ans.to_frame(code)
        ans.index = Tick_data.index

        return ans