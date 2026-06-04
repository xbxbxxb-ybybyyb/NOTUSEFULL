import numpy as np
from System.Factor import Factor

class FactorAvgTotalPriceToP0(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__lag = self._getParameter('Lag')

    def calculate(self):
        totalAmount = np.nansum(self._getLastNTickData('Amount', self.__lag))
        totalVolume = np.nansum(self._getLastNTickData('Volume', self.__lag))
        avgTotalPrice = totalAmount / totalVolume if totalVolume > 0 else 0
        if avgTotalPrice is None:
            factorValue = 0.
        else:
            ap0, bp0 = self._getLastTickData('AskPrice')[0], self._getLastTickData('BidPrice')[0]
            if ap0 < 1e-4 or bp0 < 1e-4:
                midp0 = ap0 + bp0 if (ap0 + bp0) > 1e-4 else self._getLastTickData('LastPrice')
            else:
                midp0 = (ap0 + bp0) / 2
            factorValue = - (midp0 / avgTotalPrice - 1) * 1000 if avgTotalPrice > 1e-4 else 0
        self._addFactorValue(factorValue)