import math
import numpy as np
from System.Factor import Factor


class AveOrderAmountWeighted(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__numOrderMax = self._getParameter("NumOrderMax")
        self.__numOrderMin = self._getParameter("NumOrderMin")
        self.__weightDecay = self._getParameter("WeightDecay")

    def calculate(self):
        lastAskVolume = self._getLastTickData("AskVolume")
        lastAskPrice = self._getLastTickData("AskPrice")
        lastAskPrice = lastAskPrice[lastAskVolume > 0]
        lastAskVolume = lastAskVolume[lastAskVolume > 0]
        numOrderMax = min(lastAskVolume.shape[0], self.__numOrderMax)
        if numOrderMax == 0 or lastAskVolume.shape[0] < self.__numOrderMin:
            lastAveAskAmount = 0
        else:
            volumeArray = lastAskVolume[self.__numOrderMin - 1:numOrderMax]
            priceArray = lastAskPrice[self.__numOrderMin - 1:numOrderMax]
            weightsArray = np.array([math.pow(self.__weightDecay, i) for i in range(volumeArray.shape[0])])
            lastAveAskAmount = np.sum(volumeArray * priceArray * weightsArray) / volumeArray.shape[0]

        lastBidVolume = self._getLastTickData("BidVolume")
        lastBidPrice = self._getLastTickData("BidPrice")
        lastBidPrice = lastBidPrice[lastBidVolume > 0]
        lastBidVolume = lastBidVolume[lastBidVolume > 0]
        numOrderMax = min(lastBidVolume.shape[0], self.__numOrderMax)
        if numOrderMax == 0 or lastBidVolume.shape[0] < self.__numOrderMin:
            lastAveBidAmount = 0
        else:
            volumeArray = lastBidVolume[self.__numOrderMin - 1:numOrderMax]
            priceArray = lastBidPrice[self.__numOrderMin - 1:numOrderMax]
            weightsArray = np.array([math.pow(self.__weightDecay, i) for i in range(volumeArray.shape[0])])
            lastAveBidAmount = np.sum(volumeArray * priceArray * weightsArray) / volumeArray.shape[0]

        factorValue = [lastAveBidAmount, lastAveAskAmount]

        self._addFactorValue(factorValue)
