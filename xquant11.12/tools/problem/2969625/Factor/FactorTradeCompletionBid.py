from System.Factor import Factor
import numpy as np
from itertools import groupby
from operator import itemgetter


class FactorTradeCompletionBid(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        trade_matrix = self._getLastNTodayTickData("Transactions", self.__lag)
        trade_matrix_select = [x for x in trade_matrix if x is not None]
        if len(trade_matrix_select) > 0:
            trade_matrix_select = np.concatenate(trade_matrix_select)
            bid_order = self._getTransactionData("BidOrder", trade_matrix_select)
            volume = self._getTransactionData("Volume", trade_matrix_select)

            x = sorted(list(zip(bid_order, volume)), key=itemgetter(0))
            p = groupby(x, key=itemgetter(0))
            completion_rate = []
            for _, p_sub in p:
                c_ = [p_sub_value[1] for p_sub_value in p_sub]
                if len(c_) > 1:
                    c_sum = sum(c_)
                    if c_sum != 0:
                        completion_rate += [x_ / c_sum for x_ in c_]
            if len(completion_rate) > 0:
                factor_value = np.nanmean(completion_rate)
            else:
                factor_value = 0
        else:
            factor_value = 0

        if np.isnan(factor_value):
            factor_value = 0
        self._addFactorValue(factor_value)
