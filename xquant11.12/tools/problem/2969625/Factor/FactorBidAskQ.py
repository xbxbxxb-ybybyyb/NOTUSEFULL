import numpy as np
from System.Factor import Factor


class FactorBidAskQ(Factor):
    def calculate(self):
        bidNum = self._getLastTickData("BidNum")
        askNum = self._getLastTickData("AskNum")

        bidNum1 = bidNum[0]
        askNum1 = askNum[0]

        allNum = np.concatenate([bidNum, askNum])
        totalNum = np.sum(allNum)

        bidNum1Q = np.sum(allNum[allNum <= bidNum1]) / totalNum
        askNum1Q = np.sum(allNum[allNum <= askNum1]) / totalNum

        fv = bidNum1Q - askNum1Q
        if np.isnan(fv):
            fv = 0

        self._addFactorValue(fv)
