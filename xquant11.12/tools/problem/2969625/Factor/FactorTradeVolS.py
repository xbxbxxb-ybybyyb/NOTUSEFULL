import numpy as np
from System.Factor import Factor


class FactorTradeVolS(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        transaction_array = self._getLastNTickData("Transactions", self.__lag)
        transaction_array = [x for x in transaction_array if x is not None]
        factor_value = 0
        if len(transaction_array) > 0:
            transaction_array = np.concatenate(transaction_array)
            trade_price = self._getTransactionData("Price", transaction_array)
            trade_vol = self._getTransactionData("Volume", transaction_array)
            trade_dir = self._getTransactionData("BSFlag", transaction_array)

            ask_p = self._getLastTickData("AskPrice")
            bid_p = self._getLastTickData("BidPrice")
            ask0 = ask_p[0]
            bid0 = bid_p[0]
            ask0 = ask0 if ask0 > 1e-4 else bid0
            bid0 = bid0 if bid0 > 1e-4 else ask0

            buy_vol_sum = np.nansum(trade_vol[(trade_price <= bid0) & (trade_dir == 2)])
            sell_vol_sum = np.nansum(trade_vol[(trade_price >= ask0 - 0.01) & (trade_dir == 2)])

            factor_value = np.log((buy_vol_sum + 1) / (sell_vol_sum + 1))

        self._addFactorValue(factor_value)
