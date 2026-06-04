"""
011477

"""
from Factor.FactorBase import  FactorBase

class FactorTickShiftSpreadDens(FactorBase):
    def single_stock_factor_generator(self, code, date):
        Tick_data = self.load_data(code, date)
        Tick_data = Tick_data.set_index(['T_Date', 'T_Time'])
#        print(Tick_data.keys())
        #################
        #以下为因子计算逻辑
        ans_priorAsk = Tick_data['T_AskPrice'][-5][-5]/Tick_data['T_AskPrice'][-5][-1]-1
        ans_ask= Tick_data['T_AskPrice'][-1][-5]/Tick_data['T_AskPrice'][-1][-1]-1
        
        ans_priorBid = Tick_data['T_BidPrice'][-5][-5]/Tick_data['T_BidPrice'][-5][-1]-1
        ans_bid= Tick_data['T_BidPrice'][-1][-5]/Tick_data['T_BidPrice'][-1][-1]-1
        
        ans = (ans_ask/ans_priorAsk-1) / (ans_bid/ans_priorBid-1) * Tick_data['T_Volume'].rolling(5, min_periods=3).mean()#返回一个4731行，一列的DataFrame,index为双索引，columns为code
        #################
        ans = ans.to_frame(code)
        ans.index = Tick_data.index

        return ans