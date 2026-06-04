from System.Factor import Factor
import numpy as np


class FactorOrderSellExcessRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__order_ask_vwap = self._getFactor(
            {
                "ClassName": "AskOrderVwap",
                "Parameters": {
                    "percentile": 0.01
                }
            }
        )
        self._addIntermediate("sell_excess_ratio", [])

    def calculate(self):
        bid0_price = self._getLastTickData("BidPrice")[0]
        order_sell_price_vwap = self.__order_ask_vwap.getLastFactorValue()
        if order_sell_price_vwap != 0 and bid0_price != 0:
            sell_excess_ratio = (order_sell_price_vwap / bid0_price - 1) * 1000
        else:
            sell_excess_ratio = 0.
        sell_excess_ratio_list = self.getIntermediate("sell_excess_ratio")
        sell_excess_ratio_list.append(sell_excess_ratio)
        factor_value = np.nanmean(sell_excess_ratio_list[-self.__lag:])
        self._addFactorValue(factor_value)
