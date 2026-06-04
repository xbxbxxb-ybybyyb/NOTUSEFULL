from System.Factor import Factor
import numpy as np
from collections import Counter


class FactorTradeAmtOncePriceAsk(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        ask1_price = self._getLastTickData("AskPrice")[0]
        if ask1_price < 1e-4:
            ask1_price = self._getLastTickData("MaxPrice")

        trade_matrix = self._getLastNTodayTickData("Transactions", self.__lag)
        trade_matrix_select = [x for x in trade_matrix if x is not None]
        if len(trade_matrix_select) > 0:
            trade_matrix_select = np.concatenate(trade_matrix_select)
            ask_order = self._getTransactionData("AskOrder", trade_matrix_select)

            count_map = dict(Counter(ask_order))
            count_array = np.array([count_map[x_] for x_ in ask_order])

            vol_array = self._getTransactionData("Volume", trade_matrix_select)
            price_array = self._getTransactionData("Price", trade_matrix_select)

            vol_once_sum = np.nansum(vol_array[(price_array <= ask1_price) & (count_array == 1)] *
                                     price_array[(price_array <= ask1_price) & (count_array == 1)])
            vol_total_sum = np.nansum(vol_array[price_array <= ask1_price] * price_array[price_array <= ask1_price])
            factor_value = -vol_once_sum / vol_total_sum if vol_total_sum > 1e-4 else 0
        else:
            factor_value = 0.

        self._addFactorValue(factor_value)
