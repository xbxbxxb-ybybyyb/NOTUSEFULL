import numpy as np
from System.Factor import Factor


class FactorBidTopGap(Factor):
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

        askVSum = askVolume[:self.level].sum()
        askVWAP = (askPrice[:self.level] * askVolume[:self.level]).sum() / askVSum if askVSum > 0 else maxPrice

        topIdx = self.get_top_index(bidVolume)
        bidTopVolume = bidVolume[topIdx]
        bidTopPrice = bidPrice[topIdx]

        bidVSum = bidTopVolume.sum()
        bidTopPrice = (bidTopPrice * bidTopVolume).sum() / bidVSum if bidVSum > 1e-4 else minPrice

        ratio = (askVWAP / bidTopPrice - 1) * 1000 if bidTopPrice > 1e-4 else 0.0
        ratioList.append(ratio)

        factorValue = - (ratioList[-1] - np.nanmean(ratioList[-self.lag:])) * 100

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
