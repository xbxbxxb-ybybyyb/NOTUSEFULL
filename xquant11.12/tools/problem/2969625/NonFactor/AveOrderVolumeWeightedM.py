import math
import numpy as np
from System.Factor import Factor


class AveOrderVolumeWeightedM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__numOrderMax = self._getParameter("NumOrderMax")
        self.__numOrderMin = self._getParameter("NumOrderMin")
        self.__weightDecay = self._getParameter("WeightDecay")

    def calculate(self):
        lastAskVolume = self._getLastTickData("AskVolume")
        lastAskVolume = lastAskVolume[lastAskVolume > 0]
        numOrderMax = min(lastAskVolume.shape[0], self.__numOrderMax)
        if numOrderMax == 0 or lastAskVolume.shape[0] < self.__numOrderMin:
            lastAveAskVolume = 0
        else:
            volumeArray = lastAskVolume[self.__numOrderMin - 1:numOrderMax]
            weightsArray = np.array([math.pow(self.__weightDecay, i) for i in range(volumeArray.shape[0])])
            lastAveAskVolume = np.sum(volumeArray * weightsArray) / volumeArray.shape[0]

        lastBidVolume = self._getLastTickData("BidVolume")
        lastBidVolume = lastBidVolume[lastBidVolume > 0]
        numOrderMax = min(lastBidVolume.shape[0], self.__numOrderMax)
        if numOrderMax == 0 or lastBidVolume.shape[0] < self.__numOrderMin:
            lastAveBidVolume = 0
        else:
            volumeArray = lastBidVolume[self.__numOrderMin - 1:numOrderMax]
            weightsArray = np.array([math.pow(self.__weightDecay, i) for i in range(volumeArray.shape[0])])
            lastAveBidVolume = np.sum(volumeArray * weightsArray) / volumeArray.shape[0]

        factorValue = [lastAveBidVolume, lastAveAskVolume]

        self._addFactorValue(factorValue)
