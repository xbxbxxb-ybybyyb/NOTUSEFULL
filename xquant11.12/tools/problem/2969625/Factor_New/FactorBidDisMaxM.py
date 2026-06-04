from System.Factor import Factor
import numpy as np


class FactorBidDisMaxM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__lag2 = self._getParameter("Lag2")
        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwap"
            }
        )
        self._addIntermediate("bid_max", [])

    def calculate(self):

        bid_price_list = self.__bid_vwap.getFactorValueList()[-self.__lag:]
        bid_price_max = np.nanmax(bid_price_list)
        bid_price_min = np.nanmin(bid_price_list)

        if bid_price_max - bid_price_min > 1e-3:
            bid_max_value = (bid_price_max - bid_price_list[-1]) / (bid_price_max - bid_price_min)
        else:
            bid_max_value = 1

        bid_max_list = self.getIntermediate("bid_max")
        bid_max_list.append(bid_max_value)

        if len(bid_max_list) > 5:
            factor_value = np.nanmean(bid_max_list[-self.__lag2:])
        else:
            factor_value = 0.5

        self._addFactorValue(factor_value)
