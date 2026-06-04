import numpy as np
from System.Factor import Factor


class FactorOrdAskBidNetAggressiveTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__netAggressive = self._getFactor(
            {
                "ClassName": "OrdAskBidNetAggressive"
            }
        )

    def calculate(self):
        netAggressiveList = self.__netAggressive.getFactorValueList()
        netAggressiveSlice = np.array(netAggressiveList[-self.__lag:])

        if len(netAggressiveSlice) > 1:
            factorValue = np.corrcoef(netAggressiveSlice, np.arange(len(netAggressiveSlice)))[0, 1]
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)






