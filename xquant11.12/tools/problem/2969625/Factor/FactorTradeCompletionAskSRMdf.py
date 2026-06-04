from System.Factor import Factor
import numpy as np
from itertools import groupby
from operator import itemgetter


class FactorTradeCompletionAskSRMdf(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

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
            volume = self._getTransactionData("Volume", trade_matrix_select)

            x = sorted(list(zip(ask_order, volume)), key=itemgetter(0))
            p = groupby(x, key=itemgetter(0))
            completion_rate = []
            for _, p_sub in p:
                c_ = [p_sub_value[1] for p_sub_value in p_sub]
                if len(c_) > 1:
                    c_sum = sum(c_)
                    if c_sum != 0:
                        completion_rate += [x_ / c_sum for x_ in c_]
                else:
                    completion_rate += [1.0]
            factor_value = -np.nanmean(completion_rate) / np.nanstd(completion_rate) if np.nanstd(completion_rate) > 0.01 else 0

        self._addFactorValue(factor_value)
