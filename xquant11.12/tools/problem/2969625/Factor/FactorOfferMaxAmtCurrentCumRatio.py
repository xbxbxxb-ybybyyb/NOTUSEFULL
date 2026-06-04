from System.Factor import Factor
import numpy as np


class FactorOfferMaxAmtCurrentCumRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__slag = self._getParameter("SmoothLag")

        self._addIntermediate("CurrentMaxAmountList", [])
        self._addIntermediate("CumMaxAmountList", [])

    def calculate(self):
        cmas = self.getIntermediate("CurrentMaxAmountList")
        cummas = self.getIntermediate("CumMaxAmountList")

        coqty = self._getAllTodayTickData("OfferQty")
        oqty = np.clip(np.hstack((0, np.diff(coqty))), a_min=0, a_max=np.inf)
        avgop = self._getAllTodayTickData("AvgOfferPrice")

        cmas.append(np.nanmax(np.multiply(oqty[-self.__lag:], avgop[-self.__lag:])))
        if len(cummas) == 0:
            cummas.append(oqty[-1] * avgop[-1])
        else:
            cummas.append(max(oqty[-1] * avgop[-1], cummas[-1]))

        if cummas[-1] > 1e-4:
            r = (cmas[-1] / cummas[-1])
        else:
            r = 0.

        factorValue = self.__ema(r, self.getFactorValueList(), self.__slag)

        self._addFactorValue(factorValue)

    def __ema(self, value, ema_list, n):
        if len(ema_list) == 0:
            return value
        else:
            para = 2.0 / (min(len(ema_list), n) + 1)
            return ema_list[-1] + para * (value - ema_list[-1])
