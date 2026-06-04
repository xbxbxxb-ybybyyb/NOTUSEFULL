import numpy as np
from System.Factor import Factor


class FactorCMCorr(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lookback = self._getParameter("LookBack")
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("CorrList", [])

    def calculate(self):
        priceList = self._getLastNTickData("LastPrice", self.__lookback)
        volumeList = self._getLastNTickData("Volume", self.__lookback)

        zipList = sorted(list(zip(volumeList, priceList)))
        priceList = [c[1] for c in zipList]

        if len(np.unique(priceList)) > 1:  # 不能全部一样
            corr = np.corrcoef(priceList, np.arange(len(priceList)))[0, 1]
        else:
            corr = 0.
        corrList = self.getIntermediate("CorrList")
        corrList.append(corr)

        factorValue = np.nanmean(corrList[-self.__lag:])

        self._addFactorValue(factorValue)
