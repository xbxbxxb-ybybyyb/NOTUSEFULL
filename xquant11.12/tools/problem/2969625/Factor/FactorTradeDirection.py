from System.Factor import Factor
import numpy as np


class FactorTradeDirection(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self._addIntermediate("trade_ratio", [])

    def calculate(self):
        transaction_array = self._getLastTickData("Transactions")

        trade_ratio_list = self.getIntermediate("trade_ratio")
        if transaction_array is not None:
            trade_vol = self._getTransactionData('Volume', transaction_array)
            trade_dir = self._getTransactionData('BSFlag', transaction_array)
            tick_vol_buy = np.nansum(trade_vol[trade_dir == 1.0])
            tick_vol = np.nansum(trade_vol)
            buy_trade_order_ratio = tick_vol_buy / tick_vol if tick_vol > 1e-6 else 0
            trade_ratio_list.append(buy_trade_order_ratio)
        else:
            trade_ratio_list.append(None)

        filter_trade_ratio_list = list(filter(lambda x: x is not None, trade_ratio_list))

        if len(filter_trade_ratio_list) > 0:
            factor_value = np.nanmean(filter_trade_ratio_list[-self.__lag:])
        else:
            factor_value = 0.

        self._addFactorValue(factor_value)
