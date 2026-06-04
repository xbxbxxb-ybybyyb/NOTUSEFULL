from System.Factor import Factor
import numpy as np
from collections import Counter


class FactorTradeOnceRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        trade_matrix = self._getLastNTodayTickData("Transactions", self.__lag)
        trade_matrix_select = [x for x in trade_matrix if x is not None]
        if len(trade_matrix_select) > 0:
            trade_matrix_select = np.concatenate(trade_matrix_select)
            bid_order = self._getTransactionData("BidOrder", trade_matrix_select)

            count_map = dict(Counter(bid_order))
            count_array = np.array([count_map[x_] for x_ in bid_order])

            dir_array = self._getTransactionData("BSFlag", trade_matrix_select)
            vol_array = self._getTransactionData("Volume", trade_matrix_select)

            vol_once_sum = np.nansum(vol_array[(dir_array == 1.0) & (count_array == 1)]) + \
                           np.nansum(vol_array[(dir_array == 2.0) & (count_array == 1)])
            vol_total_sum = np.nansum(vol_array[dir_array == 1.0]) + np.nansum(vol_array[dir_array == 2.0])
            factor_value = vol_once_sum / vol_total_sum if vol_total_sum > 1e-4 else 0
        else:
            factor_value = 0

        if np.isnan(factor_value):
            factor_value = 0
        self._addFactorValue(factor_value)
