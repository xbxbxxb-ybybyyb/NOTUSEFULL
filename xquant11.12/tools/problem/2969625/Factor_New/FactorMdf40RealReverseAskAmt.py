from System.Factor import Factor
import numpy as np


class FactorMdf40RealReverseAskAmt(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")

        self.__askAmtPerTrade = self._getFactor(
            {
                "ClassName": "AskAmtPerTrade"
            }
        )
        self.__MidPrice = self._getFactor(
            {
                "ClassName":"MidPrice"
            }
        )

    def calculate(self):
        priceList = np.array(self.__MidPrice.getFactorValueList()[-(self.__window + 1):])
        if len(priceList) < 5:
            factorValue = 0
        else:
            tick_ret = (priceList[1:] / priceList[:-1] - 1) * 1000
            askAmtPerTradeList = self.__askAmtPerTrade.getFactorValueList()
            long_amt = np.array(askAmtPerTradeList[-len(tick_ret):])
            if len(long_amt) == len(tick_ret):
                bottom_pct = np.nansum(tick_ret[long_amt < np.nanpercentile(long_amt, 30)])
                top_pct = np.nansum(tick_ret[long_amt > np.nanpercentile(long_amt, 70)])
                factorValue = bottom_pct - top_pct
            else:
                factorValue = 0

        self._addFactorValue(factorValue)