import numpy as np
from System.Factor import Factor


class TradeNum(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        trade_matrix = self._getLastNTodayTickData("Transactions", self.__lag)
        trade_matrix_select = [x for x in trade_matrix if x is not None]
        if len(trade_matrix_select) > 0:
            trade_matrix_select = np.concatenate(trade_matrix_select)
            bid_unique = len(set(self._getTransactionData("BidOrder", trade_matrix_select)))
            ask_unique = len(set(self._getTransactionData("AskOrder", trade_matrix_select)))
        else:
            bid_unique, ask_unique = 0, 0

        self._addFactorValue([bid_unique, ask_unique])

