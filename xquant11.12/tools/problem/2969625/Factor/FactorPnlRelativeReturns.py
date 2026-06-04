from System.Factor import Factor
import numpy as np


class FactorPnlRelativeReturns(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__ilag = self._getParameter("IndexLag")
        self.__index_name = self._getParameter("IndexName")

    def calculate(self):

        lastp = self._getLastNTickData("LastPrice", self.__lag)
        if self.__index_name == "000300.SH" or self.__index_name == "000905.SH":
            lastp_g = self._getLastNIndexTickData(self.__index_name, "LastPrice", self.__ilag)
        else:
            lastp_g = self._getLastNINFTickData(self.__index_name, "LastPrice", self.__ilag)

        if len(lastp_g) > 0:
            rtns = lastp[-1] / lastp[0] - 1
            rtns_g = lastp_g[-1] / lastp_g[0] - 1
            factorValue = (rtns_g - rtns) * 1e3
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
