from System.Factor import Factor
import numpy as np


class FactorPanFlowK(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("AskVolumeArray", [])
        self._addIntermediate("BidVolumeArray", [])

    def calculate(self):
        askVolumeArray = self.getIntermediate("AskVolumeArray")
        bidVolumeArray = self.getIntermediate("BidVolumeArray")
        askVolume = self._getLastTickData("AskVolume")
        bidVolume = self._getLastTickData("BidVolume")

        if len(askVolume) > 0:
            askVolumeArray.append(sum(askVolume))
        else:
            askVolumeArray.append(0)
        if len(bidVolume) > 0:
            bidVolumeArray.append(sum(bidVolume))
        else:
            bidVolumeArray.append(0)

        L = min(len(askVolumeArray), self.__lag)
        if L < 5:
            if len(self.getFactorValueList()) == 0:
                factorValue = 0
            else:
                factorValue = self.getLastFactorValue()
        else:
            askArray = np.array(askVolumeArray[-L:])
            bidArray = np.array(bidVolumeArray[-L:])
            flowArray = bidArray - askArray
            factorValue = self.__get_regression_params(np.arange(L), flowArray)[1] / 100

        self._addFactorValue(factorValue)

    @staticmethod
    def __get_regression_params(x, y):
        x_ = x[~(np.isnan(x) | np.isnan(y))]
        y_ = y[~(np.isnan(x) | np.isnan(y))]
        if len(x_) < 3 or len(x_) / len(x) < 0.5:
            alpha, beta = 0, 0
        else:
            beta = (np.sum(x_ * y_) - np.sum(x_) * np.mean(y_)) / np.var(x_) / len(x_)
            alpha = np.mean(y_) - beta * np.mean(x_)
        return alpha, beta
