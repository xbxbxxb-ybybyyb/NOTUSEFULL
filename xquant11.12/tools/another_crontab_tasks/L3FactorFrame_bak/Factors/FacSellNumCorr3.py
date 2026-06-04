import numpy as np
from FactorBase import FactorBase
from tools.regression import simpleRegression


class FacSellNumCorr3(FactorBase):
    def __init__(self, config, marketDataManager):
        super().__init__(config, marketDataManager)
        self.lag = config.get("lag", 3)*10
        self.num_asks_sec_list = []

    def calculate(self):
        value = 0
        sample_1s_flag = self.getPrevTick("sample_1s_flag")
        if sample_1s_flag == 1:
            order_time = self.getPrevOrder("Timestamp")
            order_bs = self.getPrevOrder("BSFlag")
            bs_flags = self.getPrevSecOrder("BSFlag", 1+order_time-int(order_time))
            sell_num = bs_flags[bs_flags==2].sum()-1 if order_bs==2 else bs_flags[bs_flags==2].sum()
            self.num_asks_sec_list.append(sell_num)
            if len(self.num_asks_sec_list) > 10:
                y = np.array(self.num_asks_sec_list[-self.lag:])
                X = np.arange(1, len(y)+1)
                value = simpleRegression(y, X)

        self.addFactorValue(value)
