import numpy as np
from System.Factor import Factor


class FactorWeightedVolumeRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        askVolume = self._getLastTickData("AskVolume")
        askPrice = self._getLastTickData("AskPrice")
        bidVolume = self._getLastTickData("BidVolume")
        bidPrice = self._getLastTickData("BidPrice")

        askWeightedVolume = self.get_weighted_volume(askPrice, askVolume)
        bidWeightedVolume = self.get_weighted_volume(bidPrice, bidVolume)

        if bidWeightedVolume > 1e-5:
            factorValue = askWeightedVolume / bidWeightedVolume
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0.

        self._addFactorValue(factorValue)

    @staticmethod
    def get_weighted_volume(priceList, volumeList):
        weightedVolume = 0
        for i in range(len(priceList) - 1):
            weightedVolume += np.abs(priceList[i+1] - priceList[i]) * volumeList[i]
        return weightedVolume



