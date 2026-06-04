"""
013542

"""
from Factor.FactorBase import  FactorBase

class FactorLast10TickVolPct(FactorBase):
    def single_stock_factor_generator(self, code, date):
        Tick_data = self.load_data(code, date)
        Tick_data = Tick_data.set_index(['T_Date', 'T_Time'])
#        print(Tick_data.keys())
        #################
        #以下为因子计算逻辑
        T_vol = Tick_data['T_Volume']
        ans = T_vol.rolling(10, min_periods=5).mean()/T_vol.rolling(100, min_periods=20).mean()

        #返回一个4731行，一列的DataFrame,index为双索引，columns为code
        #################
        ans = ans.to_frame(code)
        ans.index = Tick_data.index

        return ans

