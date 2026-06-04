from System.Factor import Factor
import numpy as np


class FactorTripleRelativeReturns(Factor):
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
        rtns_g = lastp_g[-1] / lastp_g[0] if len(lastp_g) > 0 else 0.
        rtns = lastp[-1] / lastp[0]
        rtns_i = lastp_i[-1] / lastp_i[0]

        if np.abs(rtns_g) < 1e-7:
            factorValue = 0.
        else:
            factorValue = ((rtns / rtns_g - 1) + (rtns_g / rtns_i - 1)) * 1e2

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)
