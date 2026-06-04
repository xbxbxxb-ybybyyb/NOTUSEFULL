import numpy as np
from System.Factor import Factor


class FactorOrdAskBidNetAggressiveQuantileX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")
        self.__lag = self._getParameter("Lag")

        self.__netAggressive = self._getFactor(
            {
                "ClassName": "OrdAskBidNetAggressive"
            }
        )
        self._addIntermediate("QuantileList", [])

    def calculate(self):
        netAggressiveList = self.__netAggressive.getFactorValueList()

        netAggressiveSlice = np.array(netAggressiveList[-self.__window:])

        if len(netAggressiveSlice) < 5:
            quantile = 0
        else:
            quantile = np.sum(netAggressiveSlice < netAggressiveSlice[-1]) / len(netAggressiveSlice) - 0.5

        quantileList = self.getIntermediate("QuantileList")
        quantileList.append(quantile)

        factorValue = np.nanmean(quantileList[-self.__lag:])

        self._addFactorValue(factorValue)








