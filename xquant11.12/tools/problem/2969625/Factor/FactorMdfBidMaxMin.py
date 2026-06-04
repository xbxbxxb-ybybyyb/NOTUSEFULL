from System.Factor import Factor
import numpy as np


class FactorMdfBidMaxMin(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwapAdj",
                "Parameters": {
                    "percentile": 0.005
                }
            }
        )

    def calculate(self):
        bid_price_list = self.__bid_vwap.getFactorValueList()[-self.__lag:][::-1]
        bid_price_list = [x for x in bid_price_list if not np.isnan(x) and x != 0]
        factor_value = 0
        if len(bid_price_list) > 0:
            bid_price_max = np.nanmax(bid_price_list)
            bid_price_min = np.nanmin(bid_price_list)
            max_pos = np.argmax(bid_price_list)
            min_pos = np.argmin(bid_price_list)

            if max_pos > min_pos and bid_price_min > 1e-6:
                factor_value = (bid_price_max / bid_price_min - 1) * 1000
            elif max_pos < min_pos and bid_price_max > 1e-6:
                factor_value = (bid_price_min / bid_price_max - 1) * 1000

        self._addFactorValue(factor_value)
