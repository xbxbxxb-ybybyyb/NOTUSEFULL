import numpy as np
from System.Factor import Factor


class FactorVolatilityRank(Factor):
    def __init__(self, config, dataManager):
        super().__init__(config, dataManager)
        self.__lag = self._getParameter("Lag")

    def _calculateIntermediate(self):
        historicalLastPrice = self._getLastNTickData("LastPrice", self.__lag)
        historicalLastPriceArray = self._getLastNTickDataForStockGroup("LastPrice", self.__lag)

        volatility = np.std(historicalLastPrice)
        volatilityGroup = np.std(historicalLastPriceArray, axis=0)

        volatilityRank = np.sum(volatilityGroup < volatility) + 1

        self._addIntermediate(
            {
                "HistoricalLastPriceVolatilityRank": volatilityRank,
                "GroupSize": volatilityGroup.shape[0]}
        )

    def _calculateFactor(self):
        historicalLastPriceVolatilityRank = self._getIntermediate("HistoricalLastPriceVolatilityRank")[-1]
        groupSize = self._getIntermediate("GroupSize")[-1]

        value = historicalLastPriceVolatilityRank / (groupSize + 1)

        self._addFactorValue(value)
