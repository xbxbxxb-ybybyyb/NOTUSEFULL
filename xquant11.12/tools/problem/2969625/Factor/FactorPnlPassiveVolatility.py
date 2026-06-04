from System.Factor import Factor
import numpy as np


class FactorPnlPassiveVolatility(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__mlag = self._getParameter("MinLag")
        self.__lag = self._getParameter("Lag")
        self.__tnum = self._getParameter("TicksPerMin")
        self.__itnum = self._getParameter("ITicksPerMin")
        self.__index_name = self._getParameter("IndexName")

        self._addIntermediate("ReturnsStock", [])
        self._addIntermediate("ReturnsIndex", [])

    def calculate(self):

        rtns = self.getIntermediate("ReturnsStock")
        rtns_g = self.getIntermediate("ReturnsIndex")
        lastp = self._getLastNTickData("LastPrice", self.__mlag * self.__tnum)
        lastp_g = self._getLastNINFTickData(self.__index_name, "LastPrice", self.__mlag * self.__itnum)

        if len(lastp_g) > 0:
            rtns.append(lastp[-1] / lastp[0] - 1)
            rtns_g.append(lastp_g[-1] / lastp_g[0] - 1)
        else:
            rtns.append(None)
            rtns_g.append(None)

        filter_rtns_g = list(filter(lambda x: x is not None, rtns_g))
        filter_rtns = list(filter(lambda x: x is not None, rtns))

        if len(filter_rtns_g) >= 4:
            lag = np.nanmin([self.__lag, len(filter_rtns), len(filter_rtns_g)])
            factorValue = np.nanstd(np.subtract(filter_rtns[-lag:], filter_rtns_g[-lag:])) * 1e2
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)
