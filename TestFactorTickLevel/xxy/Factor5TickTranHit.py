"""
011477

"""
from Factor.FactorBase import  FactorBase

class Factor5TickTranHit(FactorBase):
    def single_stock_factor_generator(self, code, date):
        tick_data, tran_data = self.load_data(code, date, trans=True)
        tick_data = tick_data.set_index(['T_Date', 'T_Time'])
        print(tick_data.keys(), tran_data.keys())
        #################
        #以下为因子计算逻辑
        def runner(be, tick_data):
            b, e = be[0], be[1]
            data = tran_data[b:e]
            data = data[data['TR_Price'] != 0]
            if data is None:
                return np.nan
            else:
                index_a = data[data['TR_BSFlag'] == 1].index
                swing_a = data.loc[index_a, 'TR_Price'].max() - data.loc[index_a, 'TR_Price'].min()
            return swing_a
                


        #返回一个4731行，一列的DataFrame,index为双索引，columns为code
        #################
        ans = ans.to_frame(code)
        ans.index = tick_data.index

        return ans

