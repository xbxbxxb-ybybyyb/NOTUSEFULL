from System.Factor import Factor
import numpy as np
from collections import Counter


class FactorTradeMultiRatioAskMdf(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self._addIntermediate("value", [])

    def calculate(self):
        trade_matrix = self._getAllTodayTickData("Transactions")
        trade_matrix_select = [x for x in trade_matrix if x is not None]
        factor_value = 0
        if len(trade_matrix_select) > 0:
            trade_matrix_select_valid = []
            total_len = 0
            for i, x in enumerate(trade_matrix_select[::-1]):
                total_len += x.shape[0]
                trade_matrix_select_valid.append(x)
                if total_len > self.__lag:
                    break
            trade_matrix_select_valid = trade_matrix_select_valid[::-1]
            trade_matrix_select = np.concatenate(trade_matrix_select_valid)[-self.__lag:, :]
            ask_order = self._getTransactionData("AskOrder", trade_matrix_select)
            count_map = dict(Counter(ask_order))
            count_array = np.array([count_map[x_] for x_ in ask_order])

            dir_array = self._getTransactionData("BSFlag", trade_matrix_select)
            vol_array = self._getTransactionData("Volume", trade_matrix_select)
            if len(dir_array) > 3:
                vol_once_sum = np.nansum(vol_array[(dir_array == 1.0) & (count_array > 5)])
                vol_total_sum = np.nansum(vol_array[dir_array == 1.0])
                factor_value = vol_once_sum / vol_total_sum if vol_total_sum > 1e-4 else 0
        value = self.getIntermediate("value")
        value.append(factor_value)
        factor_value2 = np.nanmean(value[-20:])
        self._addFactorValue(factor_value2)
