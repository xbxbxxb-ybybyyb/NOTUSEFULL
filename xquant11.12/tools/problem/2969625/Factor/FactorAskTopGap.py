import numpy as np
from System.Factor import Factor


class FactorAskTopGap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.level = self._getParameter("Level")
        self.lag = self._getParameter("Lag")

        self._addIntermediate("RatioList", [])

    def calculate(self):
        ratioList = self.getIntermediate("RatioList")
        askPrice = self._getLastTickData("AskPrice")
        bidPrice = self._getLastTickData("BidPrice")
        askVolume = self._getLastTickData("AskVolume")
        bidVolume = self._getLastTickData("BidVolume")
        maxPrice = self._getLastTickData("MaxPrice")
        minPrice = self._getLastTickData("MinPrice")

        bidVSum = bidVolume[:self.level].sum()
        bidVWAP = (bidPrice[:self.level] * bidVolume[:self.level]).sum() / bidVSum if bidVSum > 1e-4 else minPrice

        topIdx = self.get_top_index(askVolume)
        askTopVolume = askVolume[topIdx]
        askTopPrice = askPrice[topIdx]

        askVSum = askTopVolume.sum()
        askTopPrice = (askTopPrice * askTopVolume).sum() / askVSum if askVSum > 1e-4 else maxPrice

        ratio = (1 - bidVWAP / askTopPrice) * 1000 if askTopPrice > 1e-4 else 0.0
        ratioList.append(ratio)

        factorValue = (ratioList[-1] - np.nanmean(ratioList[-self.lag:])) * 100

        self._addFactorValue(factorValue)

    @staticmethod
    def get_top_index(x):
        if x[0] > x[1]:
            vmax = [x[0], x[1]]
            imax = [0, 1]
        else:
            vmax = [x[1], x[0]]
            imax = [1, 0]

        for i in range(2, len(x)):
            if x[i] > vmax[0]:
                vmax[1] = vmax[0]
                imax[1] = imax[0]
                vmax[0] = x[i]
                imax[0] = i
            elif x[i] > vmax[1]:
                vmax[1] = x[i]
                imax[1] = i
        return imax
