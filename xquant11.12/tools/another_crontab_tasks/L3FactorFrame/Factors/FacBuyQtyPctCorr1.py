import numpy as np
from L3FactorFrame.FactorBase import FactorBase
from L3FactorFrame.tools.regression import simpleRegression


class FacBuyQtyPctCorr1(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        self.lag = config.get("lag", 1)*10
        self.bid_qtys_list = []
        self.ask_qtys_list = []
        self.ratio_list = []

    def calculate(self):
        bid_qtys = self.getPrevTick("BidVolume")
        ask_qtys = self.getPrevTick("AskVolume")
        self.bid_qtys_list.append(bid_qtys.sum())
        self.ask_qtys_list.append(ask_qtys.sum())
        if(len(self.ask_qtys_list)<5):
            value = 0
            self.ratio_list.append(0)
        else:
            bid_qty_sum = self.bid_qtys_list[-1]
            ask_qty_sum = self.ask_qtys_list[-1]
            ratio = bid_qty_sum/(bid_qty_sum+ask_qty_sum) if bid_qty_sum+ask_qty_sum!=0 else 0
            self.ratio_list.append(ratio)

            y = np.array(self.ratio_list[-self.lag:])
            X = np.arange(1, len(y)+1)
            value = simpleRegression(X, y)

        # print(value)
        self.addFactorValue(value)
