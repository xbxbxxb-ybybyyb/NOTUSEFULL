from System.Factor import Factor
import numpy as np


class FactorBidDistanceMulRetMdf(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwap"
            }
        )
        self._addIntermediate("bid_distance", [])

    def calculate(self):
        bid_price = self._getLastTickData("BidPrice")
        bid_price_adjust = self.__bid_vwap.getFactorValueList()[-self.__lag:]
        bid_price_adjust = [x for x in bid_price_adjust if not np.isnan(x) and x != 0]
        factor_value = 10
        if len(bid_price_adjust) > 0:
            bid_distance = self.getIntermediate("bid_distance")
            bidd = bid_price_adjust[-1] / bid_price[0] - 1 if bid_price[0] != 0 else np.nan
            bid_distance.append(bidd)
            bid_distance_sub = bid_distance[-self.__lag:]
            if bid_price[0] != 0:
                factor_value = np.nanmean(bid_distance_sub) * (1 - bid_price_adjust[0] / bid_price[0]) * 1000000
            else:
                lastv = self.getLastFactorValue()
                if lastv is not None:
                    factor_value = lastv

        self._addFactorValue(factor_value)
