import numpy as np
from L3FactorFrame.FactorBase import FactorBase
from L3FactorFrame.tools.DecimalUtil import isEqual, notEqual

class FactorBuyWillingByPrice(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        self.nonfactor = self.get_factor_instance("FactorSecTradeAgg")

    def calculate(self):
        sample_1s_flag = self.getPrevTick("sample_1s_flag")
        if sample_1s_flag == 1:
            buy_money = self.nonfactor.trade_buy_money_list[-1]
            sell_money = self.nonfactor.trade_sell_money_list[-1]
            buy_num = self.nonfactor.trade_buy_num_list[-1]
            sell_num = self.nonfactor.trade_sell_num_list[-1]

            diff_v = (buy_money)/(buy_num+1)-(sell_money)/(sell_num+1)
            sum_v = (buy_money)/(buy_num+1)+(sell_money)/(sell_num+1)
            if sum_v>0:
                self.addFactorValue(diff_v/sum_v)
            else:
                self.addFactorValue(0.0)
        else:
            self.addFactorValue(0.0)


