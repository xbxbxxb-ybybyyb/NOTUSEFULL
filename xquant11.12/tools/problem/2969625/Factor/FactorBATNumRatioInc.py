import numpy as np
from System.Factor import Factor


class FactorBATNumRatioInc(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        weightRatio = np.array([0.8**i for i in range(10)])
        self.weightRatio = weightRatio / np.sum(weightRatio)
        self.lag = self._getParameter("Lag")

        self._addIntermediate("RatioList", [])

    def calculate(self):
        ratioList = self.getIntermediate("RatioList")
        bidArray = self._getLastTickData("BidNum")
        askArray = self._getLastTickData("AskNum")
        bid = np.nansum(bidArray * self.weightRatio)
        ask = np.nansum(askArray * self.weightRatio)
        total = bid + ask

        if total > 1e-4:
            ratio = bid / total - 0.5
        else:
            if len(ratioList) > 0:
                ratio = ratioList[-1]
            else:
                ratio = 0.

        ratioList.append(ratio)

        factorValue = (ratioList[-1] - np.nanmean(ratioList[-self.lag:])) * 1000

        self._addFactorValue(factorValue)



