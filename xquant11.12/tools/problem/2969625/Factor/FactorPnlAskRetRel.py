from System.Factor import Factor
import numpy as np


class FactorPnlAskRetRel(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__iwindow = self._getParameter("IndexWindow")
        self.__window = self._getParameter("Window")
        self.__shortWindow = self._getParameter("ShortWindow")
        self.__indexName = self._getParameter("IndexName")

        self.__askAmtPerTrade = self._getFactor(
            {
                "ClassName": "AskAmtPerTrade"
            }
        )

    def calculate(self):

        price_ind = self._getLastNINFTickData(self.__indexName, "LastPrice", self.__iwindow)
        ind_pct = np.nanmean((price_ind[1:] / price_ind[:-1] - 1)) * 100 if len(price_ind) > 1 else 0

        pre_price = self._getLastTickData('PreviousClose')
        price = self._getLastNTodayTickData('LastPrice', self.__window)
        price = np.append(pre_price, price)
        pct = (price[1:] / price[:-1] - 1) * 100
        cum_pct = np.nansum(pct)

        askAmtPerTradeList = self.__askAmtPerTrade.getFactorValueList()
        long_amt = np.nansum(askAmtPerTradeList[-self.__window:])
        short_amt = np.nansum(askAmtPerTradeList[-self.__shortWindow:])
        if long_amt == 0:
            single_pct = 0
        else:
            single_pct = (cum_pct / long_amt) * short_amt
        factorValue = single_pct - ind_pct

        self._addFactorValue(factorValue)
