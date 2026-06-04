from System.Factor import Factor
import numpy as np

class FactorGapRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        askPriceArray = self._getLastTickData("AskPrice")
        bidPriceArray = self._getLastTickData("BidPrice")
        askVolumeArray = self._getLastTickData("AskVolume")
        bidVolumeArray = self._getLastTickData("BidVolume")
        midPrice = (askPriceArray[0] + bidPriceArray[0])/2
        askAmountArray = np.multiply(np.array(askPriceArray), np.array(askVolumeArray))
        bidAmountArray = np.multiply(np.array(bidPriceArray), np.array(bidVolumeArray))
        askVwapPrice = 0
        bidVwapPrice = 0
        if np.sum(askVolumeArray) > 0:
            askVwapPrice = np.sum(askAmountArray) / np.sum(askVolumeArray)
        if np.sum(bidAmountArray) > 0:
            bidVwapPrice = np.sum(bidAmountArray) / np.sum(bidVolumeArray)

        factorValue = 0
        if midPrice > bidVwapPrice:
            factorValue = (askVwapPrice - midPrice) / (midPrice - bidVwapPrice)

        self._addFactorValue(factorValue)
