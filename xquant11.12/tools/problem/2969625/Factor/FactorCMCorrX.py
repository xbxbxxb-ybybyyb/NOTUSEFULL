import numpy as np
from System.Factor import Factor


class FactorCMCorrX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("sLag")

        self._addIntermediate("CorrList", [])

    def calculate(self):
        corrList = self.getIntermediate("CorrList")
        priceList = self._getLastNTickData("LastPrice", self.__lag)
        volumeList = self._getLastNTickData("Volume", self.__lag)

        zipList = sorted(list(zip(volumeList, priceList)))
        priceList = [c[1] for c in zipList]

        if len(priceList) < 5:
            corr = 0.
        else:
            corr = - np.corrcoef(priceList, np.arange(len(priceList)))[0, 1] * 100
            if np.isnan(corr):
                corr = 0.

        corrList.append(corr)

        factorValue = np.nanmean(corrList[-self.__sLag:])

        self._addFactorValue(factorValue)
