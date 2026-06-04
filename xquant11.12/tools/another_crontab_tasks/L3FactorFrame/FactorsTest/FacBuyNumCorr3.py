import numpy as np
from L3FactorFrame.FactorBase import FactorBase
from L3FactorFrame.tools.regression import simpleRegression


class FacBuyNumCorr3(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        self.lag = config.get("lag", 3)*10
        self.num_bids_sec_list = []

    def calculate(self):
        value = 0
        sample_1s_flag = self.getPrevTick("sample_1s_flag")
        if sample_1s_flag == 1:
            order_time = self.getPrevOrder("Timestamp")
            order_bs = self.getPrevOrder("BSFlag")
            bs_flags = self.getPrevSecOrder("BSFlag", 1+order_time-int(order_time))
            bid_num = bs_flags[bs_flags==1].sum()-1 if order_bs==1 else bs_flags[bs_flags==1].sum()
            self.num_bids_sec_list.append(bid_num)
            if len(self.num_bids_sec_list) > 10:
                y = np.array(self.num_bids_sec_list[-self.lag:])
                X = np.arange(1, len(y)+1)
                value = simpleRegression(y, X)

        self.addFactorValue(value)
