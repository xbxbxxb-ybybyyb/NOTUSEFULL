from System.Factor import Factor
import numpy as np


class FactorTrackVolatility(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__mlag = self._getParameter("MinLag")

    def calculate(self):

        tclose = self._getLastNTickData("LastPrice", 20 * self.__mlag)

        trtns = tclose[1:] - tclose[:-1]
        if np.nansum(np.abs(trtns)) > 0:
            factorValue = np.nansum(trtns[trtns > 0]) / np.nansum(np.abs(trtns))
        else:
            factorValue = 0.5

        if np.isnan(factorValue):
            factorValue = 0.5

        self._addFactorValue(factorValue)
