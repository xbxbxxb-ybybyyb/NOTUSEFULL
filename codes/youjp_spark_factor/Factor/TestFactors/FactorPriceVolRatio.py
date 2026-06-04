import numpy as np
from System.Factor import Factor


class FactorPriceVolRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__lookBack = self._getParameter("LookBack")

        self._addIntermediate("bidPrice", [])
        self._addIntermediate("askPrice", [])

    def calculate(self):
        bidP0 = self._getLastTickData("BidPrice")[0]
        askP0 = self._getLastTickData("AskPrice")[0]

        bidPriceList = self.getIntermediate("bidPrice")
        #bidPrice = self._EMA_calculate(bidP0, bidPriceList, self.__lag)
        bidPriceList.append(bidP0)
        askPriceList = self.getIntermediate("askPrice")
        #askPrice = self._EMA_calculate(askP0, askPriceList, self.__lag)
        askPriceList.append(askP0)

        if len(bidPriceList) <= 1:
            value = 0.
        else:
            bidP0Std = np.nanstd(bidPriceList[-self.__lookBack:], ddof=1)
            askP0Std = np.nanstd(askPriceList[-self.__lookBack:], ddof=1)
            if askP0Std == 0:
                value = 0.
            else:
                value = bidP0Std / askP0Std

        self._addFactorValue(value)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])

