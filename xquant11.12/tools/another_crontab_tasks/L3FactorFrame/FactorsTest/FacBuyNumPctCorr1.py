import numpy as np
from L3FactorFrame.FactorBase import FactorBase
from L3FactorFrame.tools.regression import simpleRegression


class FacBuyNumPctCorr1(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        self.lag = config.get("lag", 1)*10
        self.bid_nums_list = []
        self.ask_nums_list = []
        self.ratio_list = []

    def calculate(self):

        bid_nums = self.getPrevTick("BidNum")
        ask_nums = self.getPrevTick("AskNum")
        self.bid_nums_list.append(bid_nums.sum())
        self.ask_nums_list.append(ask_nums.sum())
        if(len(self.bid_nums_list)<5):
            self.ratio_list.append(0)
            value = 0
        else:
            bid_num_sum = self.bid_nums_list[-1]
            ask_num_sum = self.ask_nums_list[-1]
            ratio = bid_num_sum / (bid_num_sum+ask_num_sum) if bid_num_sum+ask_num_sum!=0 else 0
            self.ratio_list.append(ratio)

            y = np.array(self.ratio_list[-self.lag:])
            X = np.arange(1, len(y)+1)
            value = simpleRegression(X, y)

        # print(value)
        self.addFactorValue(value)
