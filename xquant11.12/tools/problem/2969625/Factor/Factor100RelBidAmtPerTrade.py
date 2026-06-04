from System.Factor import Factor
import numpy as np


class Factor100RelBidAmtPerTrade(Factor):
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
        rel_value = self.rel(bidAmtPerTradeList, self.__shortWindow, self.__window)
        if np.isnan(rel_value):
            rel_value = 0

        self._addFactorValue(rel_value)

    def rel(self, ema_list, short_length, length):
        if len(ema_list) <= short_length:
            short_ma = np.nanmean(np.array(ema_list[-int(len(ema_list) / 2):]))
            long_ma = np.nanmean(np.array(ema_list))
        elif len(ema_list) < length:
            short_ma = np.nanmean(np.array(ema_list[-short_length:]))
            long_ma = np.nanmean(np.array(ema_list))
        else:
            short_ma = np.nanmean(np.array(ema_list[-short_length:]))
            long_ma = np.nanmean(np.array(ema_list[-length:]))
        if long_ma == 0:
            return 0
        else:
            return short_ma / long_ma

