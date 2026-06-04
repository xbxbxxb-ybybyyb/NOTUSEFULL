"""
011477

"""
from Factor.FactorBase import  FactorBase

class Factor5TickAskVolDens(FactorBase):
    def single_stock_factor_generator(self, code, date):
        Tick_data = self.load_data(code, date)
        Tick_data = Tick_data.set_index(['T_Date', 'T_Time'])
#        print(Tick_data.keys())
        #################
        #以下为因子计算逻辑
        ans = Tick_data['T_Volume'].rolling(5, min_periods=3).sum()/Tick_data['T_AskVolume'][-1][-1]


        #返回一个4731行，一列的DataFrame,index为双索引，columns为code
        #################
        ans = ans.to_frame(code)
        ans.index = Tick_data.index

        return ans