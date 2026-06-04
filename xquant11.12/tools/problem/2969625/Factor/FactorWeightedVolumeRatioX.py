import numpy as np
from System.Factor import Factor


class FactorWeightedVolumeRatioX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("RatioList", [])

    def calculate(self):
        ratioList = self.getIntermediate("RatioList")
        askVolume = self._getLastTickData("AskVolume")
        askPrice = self._getLastTickData("AskPrice")
        bidVolume = self._getLastTickData("BidVolume")
        bidPrice = self._getLastTickData("BidPrice")

        askWeightedVolume = self.get_weighted_volume(askPrice, askVolume)
        bidWeightedVolume = self.get_weighted_volume(bidPrice, bidVolume)

        if askWeightedVolume > 1e-4:
            ratio = np.log((bidWeightedVolume + 1e-4) / (askWeightedVolume + 1e-4))
            ratio = np.clip(ratio, -2, 2)
        else:
            if len(ratioList) > 0:
                ratio = ratioList[-1]
            else:
                ratio = 0.
        ratioList.append(ratio)

        factorValue = (ratioList[-1] - np.nanmean(ratioList[-self.__lag:])) * 100

        self._addFactorValue(factorValue)

    @staticmethod
    def get_weighted_volume(priceList, volumeList):
        weightedVolume = 0.
        priceDiffSum = 0.
        for i in range(len(priceList) - 1):
            priceDiff = np.abs(priceList[i+1] - priceList[i])
            priceDiffSum += priceDiff
            weightedVolume += priceDiff * volumeList[i]
        if priceDiffSum > 1e-4:
            weightedVolume = weightedVolume / (priceDiffSum / len(priceList))
        return weightedVolume



