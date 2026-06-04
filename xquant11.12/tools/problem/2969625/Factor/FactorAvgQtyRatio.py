from System.Factor import Factor
import numpy as np
import copy

class FactorAvgQtyRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        askQty = self._getLastTickData("OfferQty")
        bidQty = self._getLastTickData("BidQty")
        askPrice = copy.deepcopy(self._getLastTickData("AskPrice"))
        bidPrice = copy.deepcopy(self._getLastTickData("BidPrice"))
        maxPrice = self._getLastTickData("MaxPrice")
        minPrice = self._getLastTickData("MinPrice")
        askPrice[askPrice == 0] = maxPrice
        bidPrice[bidPrice == 0] = minPrice
        askP0 = askPrice[0]
        bidP0 = bidPrice[0]
        basePrice = (maxPrice + minPrice) / 2
        askTopGap = (maxPrice - askP0) / basePrice * 10000
        bidTopGap = (bidP0 - minPrice) / basePrice * 10000

        if askTopGap == 0:
            factorValue = 0.0
        elif bidTopGap == 0:
            factorValue = 0.0
        else:
            avgAskQtyPerP = askQty / askTopGap
            avgBidQtyPerP = bidQty / bidTopGap
            factorValue = avgBidQtyPerP / (avgAskQtyPerP + avgBidQtyPerP)

        if np.isnan(factorValue):
            factorValue = 0.5

        self._addFactorValue(factorValue)