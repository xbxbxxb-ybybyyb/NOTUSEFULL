from System.Factor import Factor
import numpy as np


class FactorSR(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):

        lastp = self._getLastNTickData("LastPrice", self.__lag)

        if len(lastp) >= 5:
            if np.nanmax(lastp) == np.nanmin(lastp):
                factorValue = 0.
            else:
                rtns = lastp[1:] / lastp[:-1] - 1
                factorValue = np.nanmean(rtns) / np.nanstd(rtns) * 10
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
