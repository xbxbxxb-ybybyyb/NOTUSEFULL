"""
011477

"""
from Factor.FactorBase import  FactorBase

class Factor5TickPriceDen(FactorBase):
    def single_stock_factor_generator(self, code, date):
        Tick_data = self.load_data(code, date)
        Tick_data = Tick_data.set_index(['T_Date', 'T_Time'])
#        print(Tick_data.keys())
        #################
        #以下为因子计算逻辑
        ans_px_mean = Tick_data['T_LastPrice'].rolling(5, min_periods=3).mean()/(Tick_data['T_AskPrice'][-1][-1] -Tick_data['T_BidPrice'][-1][-1])
        ans_px_var = Tick_data['T_LastPrice'].rolling(20, min_periods=3).var()
        ans = ans_px_mean/ans_px_var

        #返回一个4731行，一列的DataFrame,index为双索引，columns为code
        #################
        ans = ans.to_frame(code)
        ans.index = Tick_data.index

        return ans