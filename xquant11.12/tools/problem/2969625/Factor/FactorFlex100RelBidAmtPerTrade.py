from System.Factor import Factor
import numpy as np


class FactorFlex100RelBidAmtPerTrade(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")
        self.__longWindow = self._getParameter("LongWindow")

        self.__bidAmtPerTrade = self._getFactor(
            {
                "ClassName": "BidAmtPerTrade"
            }
        )
        
    def calculate(self):
        amt = self._getLastNTickData('Amount', self.__longWindow)
        avg_amt = np.nanmean(amt)
        bidAmtPerTradeList = self.__bidAmtPerTrade.getFactorValueList()
        avg_tickamt = np.nanmean(np.array(bidAmtPerTradeList[-self.__window:]))
        if avg_amt == 0:
            rel_value = 0
        else:
            rel_value = avg_tickamt / avg_amt * 10
        if np.isnan(rel_value):
            rel_value = 0

        self._addFactorValue(rel_value)

