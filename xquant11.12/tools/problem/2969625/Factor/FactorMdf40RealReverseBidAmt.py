from System.Factor import Factor
import numpy as np


class FactorMdf40RealReverseBidAmt(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")

        self.__bidAmtPerTrade = self._getFactor(
            {
                "ClassName": "BidAmtPerTrade"
            }
        )

    def calculate(self):
        priceList = self._getLastNTickData("LastPrice", self.__window + 1)
        if len(priceList) < 5:
            factorValue = 0
        else:
            tick_ret = (priceList[1:] / priceList[:-1] - 1) * 1000
            bidAmtPerTradeList = self.__bidAmtPerTrade.getFactorValueList()
            long_amt = np.array(bidAmtPerTradeList[-len(tick_ret):])
            bottom_pct = np.nansum(tick_ret[long_amt < np.nanpercentile(long_amt, 20)])
            top_pct = np.nansum(tick_ret[long_amt > np.nanpercentile(long_amt, 80) ])

            factorValue = top_pct - bottom_pct

        self._addFactorValue(factorValue)