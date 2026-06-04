from System.Factor import Factor
import numpy as np


class FactorTripleMaxDistanceToIndex(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__wlag = self._getParameter("WideIndexLag")
        self.__ilag = self._getParameter("IndIndexLag")
        self.__wIndexName = self._getParameter("WideIndexName")
        self.__indIndexName = self._getParameter("IndIndexName")

    def calculate(self):

        lastp = self._getLastNTickData("LastPrice", self.__lag)
        lastp_g = self._getLastNINFTickData(self.__indIndexName, "LastPrice", self.__ilag)
        lastp_i = self._getLastNIndexTickData(self.__wIndexName, "LastPrice", self.__wlag)
        rtns = lastp[-1] / lastp[0] - 1
        rtns_g = lastp_g[-1] / lastp_g[0] - 1 if len(lastp_g) > 0 else 0.
        rtns_i = lastp_i[-1] / lastp_i[0] - 1

        if np.abs(rtns - rtns_g) > np.abs(rtns - rtns_i):
            factorValue = (rtns_g - rtns) * 1e3
        else:
            factorValue = (rtns_i - rtns) * 1e3

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
