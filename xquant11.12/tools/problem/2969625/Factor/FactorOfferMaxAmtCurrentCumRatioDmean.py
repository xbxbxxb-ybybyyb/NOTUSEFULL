from System.Factor import Factor
import numpy as np

class FactorOfferMaxAmtCurrentCumRatioDmean(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        coqty = self._getAllTodayTickData("OfferQty")
        oqty = np.clip(np.hstack((0, np.diff(coqty))), a_min=0, a_max=np.inf)
        avgop = self._getAllTodayTickData("AvgOfferPrice")

        factorValue = (oqty[-1] * avgop[-1] - np.sum(np.multiply(oqty[-self.__lag:], avgop[-self.__lag:]))) / 1000
        self._addFactorValue(factorValue)
