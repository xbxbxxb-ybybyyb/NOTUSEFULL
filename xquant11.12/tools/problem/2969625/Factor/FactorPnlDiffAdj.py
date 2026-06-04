from System.Factor import Factor
import numpy as np


class FactorPnlDiffAdj(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__ilag = self._getParameter("IndexLag")
        self.__svlag = self._getParameter("ShortVolumeLag")
        self.__lvlag = self._getParameter("LongVolumeLag")
        self.__indexName = self._getParameter("IndexName")

        self.__volRatio = self._getFactor(
            {
                "ClassName": "VolRatio",
                "Parameters": {
                    "Lag1": self.__lvlag,
                    "Lag2": self.__svlag
                }
            }
        )

    def calculate(self):
        stock_price_list = self._getLastNTickData("LastPrice", self.__lag)
        index_price_list = self._getLastNINFTickData(self.__indexName, "LastPrice", self.__ilag)

        ret_stock = stock_price_list[-1] / stock_price_list[0] - 1
        ret_index = index_price_list[-1] / index_price_list[0] - 1 if len(index_price_list) > 0 else 0
        ret_diff = ret_stock - ret_index
        vol_ratio = self.__volRatio.getLastFactorValue()

        factorValue = ret_diff * vol_ratio * 100
        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
