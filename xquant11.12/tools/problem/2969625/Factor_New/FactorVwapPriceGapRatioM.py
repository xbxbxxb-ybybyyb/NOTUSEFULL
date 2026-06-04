from System.Factor import Factor
import numpy as np

class FactorVwapPriceGapRatioM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        askPrice = self._getLastTickData("AskPrice")
        bidPrice = self._getLastTickData("BidPrice")
        askVolume = self._getLastTickData("AskVolume")
        bidVolume = self._getLastTickData("BidVolume")
        midPrice = (askPrice[0] + bidPrice[0]) / 2

        nonzeroAskPrice = askPrice[askPrice > 0.01]
        nonzeroBidPrice = bidPrice[bidPrice > 0.01]
        nonzeroAskVolume = askVolume[askVolume > 0.01]
        nonzeroBidVolume = bidVolume[bidVolume > 0.01]


        if (len(nonzeroAskVolume) == 0) or (len(nonzeroBidVolume) == 0):
            factorValue = 0.5
        else:
            vwapAskPrice = np.sum(nonzeroAskPrice * nonzeroAskVolume) / np.sum(nonzeroAskVolume)
            vwapBidPrice = np.sum(nonzeroBidPrice * nonzeroBidVolume) / np.sum(nonzeroBidVolume)
            factorValue = (vwapAskPrice - midPrice) / (vwapAskPrice - vwapBidPrice)

        self._addFactorValue(factorValue)
