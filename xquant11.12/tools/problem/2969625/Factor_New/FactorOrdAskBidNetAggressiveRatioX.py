import numpy as np
from System.Factor import Factor


class FactorOrdAskBidNetAggressiveRatioX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("sLag")

        self.__netAggressive = self._getFactor(
            {
                "ClassName": "OrdAskBidNetAggressive"
            }
        )

    def calculate(self):
        netAggressiveList = self.__netAggressive.getFactorValueList()
        if len(netAggressiveList) < min(3, self.__sLag):
            factorValue = 0.
        else:
            factorValue = self.amplify_zcore(netAggressiveList, self.__sLag, self.__lag) * 100

        self._addFactorValue(factorValue)

    @staticmethod
    def amplify_zcore(valueList, sLag, lag):
        size = len(valueList)
        sLag = min(max(1, int(size * sLag / lag)), sLag)
        std = np.nanstd(valueList)
        if std < 1e-6 or np.isnan(std):
            return 0
        else:
            return (np.nanmean(valueList[-sLag:]) - np.nanmean(valueList[-lag:])) / std






