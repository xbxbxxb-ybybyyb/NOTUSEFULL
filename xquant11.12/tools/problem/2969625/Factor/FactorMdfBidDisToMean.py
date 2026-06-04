from System.Factor import Factor
import numpy as np


class FactorMdfBidDisToMean(Factor):
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
        bid_price_list = self.__bid_vwap.getFactorValueList()[-self.__lag:]
        bid_price_ = np.nanmax(bid_price_list)

        if bid_price_ > 1e-6:
            factor_value = (np.nanmax(bid_price_list[-20:]) / bid_price_ - 1) * 1000
        else:
            factor_value = 0
        if np.isnan(factor_value):
            factor_value = 0
        self._addFactorValue(factor_value)
