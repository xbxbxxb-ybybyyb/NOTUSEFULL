import numpy as np
from System.Factor import Factor


class FactorOrdAskBidNetAggressiveTrendX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")

        self.__netAggressive = self._getFactor(
            {
                "ClassName": "OrdAskBidNetAggressive"
            }
        )

    def calculate(self):
        netAggressiveList = self.__netAggressive.getFactorValueList()
        netAggressiveSlice = np.array(netAggressiveList[-self.__window:])

        if len(netAggressiveSlice) < 5:
            factorValue = 0
        else:
            factorValue = np.corrcoef(netAggressiveSlice, np.arange(len(netAggressiveSlice)))[0, 1] * 100

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)






