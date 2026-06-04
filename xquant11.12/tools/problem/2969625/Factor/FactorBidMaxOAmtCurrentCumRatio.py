from System.Factor import Factor
import numpy as np


class FactorBidMaxOAmtCurrentCumRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("CurrentMaxAmountList", [])
        self._addIntermediate("CumMaxAmountList", [])

    def calculate(self):
        cmas = self.getIntermediate("CurrentMaxAmountList")
        cummas = self.getIntermediate("CumMaxAmountList")

        avgbp = self._getAllTodayTickData("AvgBidPrice")
        cbqty = self._getAllTodayTickData("BidQty")
        bqty = np.clip(np.hstack((0, np.diff(cbqty))), a_min=0, a_max=np.inf)

        cmas.append(np.nanmax(np.multiply(bqty[-self.__lag:], avgbp[-self.__lag:])))
        if len(cummas) == 0:
            cummas.append(bqty[-1] * avgbp[-1])
        else:
            cummas.append(max(bqty[-1] * avgbp[-1], cummas[-1]))

        if cummas[-1] > 1e-4:
            factorValue = (cmas[-1] / cummas[-1])
        else:
            factorValue = 0.

        self._addFactorValue(factorValue)
