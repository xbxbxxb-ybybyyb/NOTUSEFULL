import numpy as np
from System.Factor import Factor


class FactorPriceDiffVolRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__lookBack = self._getParameter("LookBack")

        self.__vwapPrice = self._getFactor(
            {
                "ClassName": "VWAPPrice2"   ### 当天每TICK前所有交易的成交均价
            }
        )

        self._addIntermediate("bidPrice", [])
        self._addIntermediate("askPrice", [])

    def calculate(self):
        vwapPriceList = self.__vwapPrice.getFactorValueList()

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
            bidPDiffStd = np.nanstd((np.array(bidPriceList) - np.array(vwapPriceList))[-self.__lookBack:], ddof=1)
            askPDiffStd = np.nanstd((np.array(askPriceList) - np.array(vwapPriceList))[-self.__lookBack:], ddof=1)
            if askPDiffStd == 0:
                value = 0.
            else:
                value = bidPDiffStd / askPDiffStd

        self._addFactorValue(value)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])

