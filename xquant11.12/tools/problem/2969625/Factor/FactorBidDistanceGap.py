from System.Factor import Factor
import numpy as np


class FactorBidDistanceGap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__slevel = self._getParameter("ShortLevel")
        self.__llevel = self._getParameter("LongLevel")
        self.__bid_vwap_3 = self._getFactor(
            {
                "ClassName": "BidVwapNum",
                "Parameters": {
                    "n": self.__slevel,
                }
            }
        )
        self.__bid_vwap_10 = self._getFactor(
            {
                "ClassName": "BidVwapNum",
                "Parameters": {
                    "n": self.__llevel,
                }
            }
        )
        self._addIntermediate("bidDistanceList", [])

    def calculate(self):
        bid_price_adjust_3 = self.__bid_vwap_3.getLastFactorValue()
        bid_price_adjust_10 = self.__bid_vwap_10.getLastFactorValue()
        bidDistanceList = self.getIntermediate("bidDistanceList")
        bidDistanceList.append(bid_price_adjust_10 / bid_price_adjust_3 - 1 if bid_price_adjust_3 != 0 else 0.)
        factor_value = np.nanmean(bidDistanceList) * 1000

        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
