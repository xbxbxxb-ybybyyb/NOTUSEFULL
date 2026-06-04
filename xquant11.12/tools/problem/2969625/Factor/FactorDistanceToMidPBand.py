from System.Factor import Factor
import numpy as np


class FactorDistanceToMidPBand(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__mlag = self._getParameter("MinLag")
        self.__vlag = self._getParameter("VolLag")
        self.__vscale = self._getParameter("VolScale")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice",
                "SplitAdjusted": True
            }
        )

    def calculate(self):
        bid_price_1 = self._getLastTickData("BidPrice")[0]  # buy1
        ask_price_1 = self._getLastTickData("AskPrice")[0]  # sell1
        mid_price_list = self.__midPrice.getFactorValueList()

        itv = np.nanmin([20 * self.__mlag, len(mid_price_list)])
        mid_price_pre = mid_price_list[-itv]
        mid_price = mid_price_list[-1]
        mclose = self._getLastNMinuteData("ClosePrice", self.__vlag * 240)
        mrtns = (mclose[self.__mlag:] / mclose[:-self.__mlag] - 1) * itv * 3 / 60 / self.__mlag
        mvolatility = np.nanstd(mrtns)
        expt_high = mid_price_pre * (1 + mvolatility * self.__vscale)
        expt_low = mid_price_pre * (1 - mvolatility * self.__vscale)

        if ask_price_1 < expt_low:
            if ask_price_1 != 0:
                factorValue = (expt_low / ask_price_1 - 1) * 1e3
            else:
                lastValue = self.getLastFactorValue()
                if lastValue is not None:
                    factorValue = lastValue
                else:
                    factorValue = 0
        elif bid_price_1 > expt_high:
            if bid_price_1 != 0:
                factorValue = (expt_high / bid_price_1 - 1) * 1e3
            else:
                lastValue = self.getLastFactorValue()
                if lastValue is not None:
                    factorValue = lastValue
                else:
                    factorValue = 0
        else:
            factorValue = mid_price / mid_price_pre - 1

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
