import numpy as np
from System.Factor import Factor


class FactorBOVwapGap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        weightRatio = np.array([0.8**i for i in range(10)])
        self.weightRatio = weightRatio / np.sum(weightRatio)

    def calculate(self):
        AvgOfferPrice = self._getLastTickData("AvgOfferPrice")
        AvgBidPrice = self._getLastTickData("AvgBidPrice")
        maxPrice = self._getLastTickData("MaxPrice")
        minPrice = self._getLastTickData("MinPrice")

        BidPrice = self._getLastTickData("BidPrice")
        BidVolume = self._getLastTickData("BidVolume")
        BidAmount = BidPrice * BidVolume
        BidVol = np.nansum(BidVolume * self.weightRatio)
        AskPrice = self._getLastTickData("AskPrice")
        AskVolume = self._getLastTickData("AskVolume")
        AskAmount = AskPrice * AskVolume
        AskVol = np.nansum(AskVolume * self.weightRatio)

        AskVwap = np.nansum(AskAmount * self.weightRatio) / AskVol if AskVol > 1e-4 else maxPrice
        BidVwap = np.nansum(BidAmount * self.weightRatio) / BidVol if BidVol > 1e-4 else minPrice

        priceDist = AvgOfferPrice - AvgBidPrice
        if priceDist > 1e-4:
            factorValue = - (AskVwap - BidVwap) / priceDist * 100
        else:
            factorValue = 0.

        self._addFactorValue(factorValue)



