from System.Factor import Factor
import numpy as np
import datetime as dt


class FactorPnlHighDistance(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__ilag = self._getParameter("IndexLag")
        self.__index_name = self._getParameter("IndexName")

    def calculate(self):

        lastp = self._getLastNTickData("LastPrice", self.__lag)
        tsp = self._getLastNTickData("Timestamp", self.__lag)
        if self.__index_name == "000300.SH" or self.__index_name == "000905.SH":
            lastp_g = self._getLastNIndexTickData(self.__index_name, "LastPrice", self.__ilag)
            tsp_g = self._getLastNIndexTickData(self.__index_name, "Timestamp", self.__ilag)
        else:
            lastp_g = self._getLastNINFTickData(self.__index_name, "LastPrice", self.__ilag)
            tsp_g = self._getLastNINFTickData(self.__index_name, "Timestamp", self.__ilag)

        if len(lastp_g) > 0:
            factorValue = self.__getTimeDiff(tsp[np.nanargmax(lastp)], tsp_g[np.nanargmax(lastp_g)])
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    @staticmethod
    def __getTimeDiff(time1, time2):
        hour1 = dt.datetime.fromtimestamp(time1).hour
        hour2 = dt.datetime.fromtimestamp(time2).hour

        if hour1 > 12:
            time1 -= 5400
        if hour2 > 12:
            time2 -= 5400
        return time2 - time1

