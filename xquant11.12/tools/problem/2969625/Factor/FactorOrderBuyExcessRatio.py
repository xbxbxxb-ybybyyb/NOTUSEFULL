from System.Factor import Factor
import numpy as np


class FactorOrderBuyExcessRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__order_bid_vwap = self._getFactor(
            {
                "ClassName": "BidOrderVwap",
                "Parameters": {
                    "percentile": 0.01
                }
            }
        )
        self._addIntermediate("buy_excess_ratio", [])

    def calculate(self):
        ask0_price = self._getLastTickData("AskPrice")[0]
        order_buy_price_vwap = self.__order_bid_vwap.getLastFactorValue()
        if order_buy_price_vwap != 0 and ask0_price != 0:
            buy_excess_ratio = (order_buy_price_vwap / ask0_price - 1) * 1000
        else:
            buy_excess_ratio = 0.
        buy_excess_ratio_list = self.getIntermediate("buy_excess_ratio")
        buy_excess_ratio_list.append(buy_excess_ratio)
        factor_value = np.nanmean(buy_excess_ratio_list[-self.__lag:])
        self._addFactorValue(factor_value)
