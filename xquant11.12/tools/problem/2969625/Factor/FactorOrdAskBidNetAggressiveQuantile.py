import numpy as np
from System.Factor import Factor


class FactorOrdAskBidNetAggressiveQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__window = self._getParameter("Window")

        self.__netAggressive = self._getFactor(
            {
                "ClassName": "OrdAskBidNetAggressive"
            }
        )
        self._addIntermediate("QuantileList", [])

    def calculate(self):
        netAggressiveList = self.__netAggressive.getFactorValueList()

        netAggressiveSlice = np.array(netAggressiveList[-self.__lag:])

        if len(netAggressiveSlice) > 1:
            quantile = sum(netAggressiveSlice < netAggressiveSlice[-1]) / len(netAggressiveSlice)
        else:
            quantile = 0.

        quantileList = self.getIntermediate("QuantileList")
        quantileList.append(quantile)

        factorValue = np.nanmean(quantileList[-self.__window:])

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)








