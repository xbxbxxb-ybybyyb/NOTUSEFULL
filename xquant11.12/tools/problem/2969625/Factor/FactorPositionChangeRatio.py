from System.Factor import Factor
import numpy as np


class FactorPositionChangeRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("PriceDiff", [])

    def calculate(self):

        askp = self._getLastTickData("AskPrice")
        askv = self._getLastTickData("AskVolume")
        bidp = self._getLastTickData("BidPrice")
        bidv = self._getLastTickData("BidVolume")
        pdiff = self.getIntermediate("PriceDiff")
        np.place(askv, askp == 0, 0.)  # 深交所转债历史行情有问题，需要处理一下
        np.place(bidv, bidp == 0, 0.)

        if (np.nansum(askv) != 0) and (np.nansum(bidv) != 0):
            askpw = np.nansum(askp * askv / np.nansum(askv))
            bidpw = np.nansum(bidp * bidv / np.nansum(bidv))
            pdiff.append(askpw - bidpw)
            filter_pdiff = list(filter(lambda x: x is not None, pdiff))
            pdiff_sub = filter_pdiff[-self.__lag:]
            factorValue = pdiff_sub[-1] / pdiff_sub[0] - 1 if pdiff_sub[0] != 0 else 0.
        else:
            pdiff.append(None)
            lastv = self.getLastFactorValue()
            if lastv is not None:
                factorValue = lastv
            else:
                factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

