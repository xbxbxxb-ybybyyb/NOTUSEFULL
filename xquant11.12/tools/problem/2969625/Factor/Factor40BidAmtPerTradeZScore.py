from System.Factor import Factor
import numpy as np


class Factor40BidAmtPerTradeZScore(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")
        self.__shortWindow = min(int(self.__window / 2), 20)

        self.__bidAmtPerTrade = self._getFactor(
            {
                "ClassName": "BidAmtPerTrade"
            }
        )

    def calculate(self):
        bidAmtPerTradeList = self.__bidAmtPerTrade.getFactorValueList()
        short_ma = np.nanmean(np.array(bidAmtPerTradeList[-self.__shortWindow:]))
        long_ma = np.nanmean(np.array(bidAmtPerTradeList[-self.__window:]))
        std_value = np.nanstd(np.array(bidAmtPerTradeList[-self.__window:]))
        if std_value == 0:
            res = 0
        else:
            res = (short_ma - long_ma) / std_value
        if np.isnan(res):
            res = 0

        self._addFactorValue(res)











