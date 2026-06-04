import numpy as np
from System.Factor import Factor


class MA(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__originalData = self._getFactor(self._getParameter("OriginalData"))

    def calculate(self):
        dataList = self.__originalData.getFactorValueList()
        if self.__lag is None or len(dataList) <= self.__lag:
            factorValue = np.mean(dataList)
        else:
            factorValue = np.mean(dataList[-self.__lag:])

        self._addFactorValue(factorValue)
