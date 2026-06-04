from System.Factor import Factor
import numpy as np


class MidPriceWeighted(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__grade = self._getParameter("Grade")

    def calculate(self):
        askP = self._getLastTickData("AskPrice")[:self.__grade]
        bidP = self._getLastTickData("BidPrice")[:self.__grade]
        askV = self._getLastTickData("AskVolume")[:self.__grade]
        bidV = self._getLastTickData("BidVolume")[:self.__grade]
        if np.nansum(askV) + np.nansum(bidV) != 0:
            factorValue = (np.dot(askP, askV) + np.dot(bidP, bidV)) / (np.nansum(askV) + np.nansum(bidV))
        else:
            lastValue = self.getLastFactorValue()
            if lastValue is not None:
                factorValue = lastValue
            else:
                factorValue = 0.

        self._addFactorValue(factorValue)
