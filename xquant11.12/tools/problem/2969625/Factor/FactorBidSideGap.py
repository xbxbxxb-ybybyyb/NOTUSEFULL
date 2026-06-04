import numpy as np
from System.Factor import Factor


class FactorBidSideGap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        weightRatio = np.array([0.8**i for i in range(10)])
        self.weightRatio = weightRatio / np.sum(weightRatio)
        self.lag = self._getParameter("Lag")

        self._addIntermediate("GapList", [])

    def calculate(self):
        gapList = self.getIntermediate("GapList")
        basePrice = self._getLastTickData("MinPrice")
        price = self._getLastTickData("BidPrice")
        volume = self._getLastTickData("BidVolume")
        amount = price * volume
        volSum = np.nansum(volume * self.weightRatio)

        vwap = np.nansum(amount * self.weightRatio) / volSum if volSum > 1e-4 else basePrice
        P0 = price[0] if price[0] > 1e-4 else basePrice
        gap = (vwap / P0 - 1) * 1000
        gapList.append(gap)

        factorValue = (gapList[-1] - np.nanmean(gapList[-self.lag:])) * 100

        self._addFactorValue(factorValue)
