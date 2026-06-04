from System.Factor import Factor
import numpy as np


class FactorOrderActiveSellRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self._addIntermediate("trade_order_ratio", [])

    def calculate(self):
        order_array = self._getLastTickData('Orders')
        transaction_array = self._getLastTickData("Transactions")

        trade_order_ratio_list = self.getIntermediate("trade_order_ratio")
        if transaction_array is not None and order_array is not None:
            trade_vol = self._getTransactionData('Volume', transaction_array)
            trade_dir = self._getTransactionData('BSFlag', transaction_array)
            trade_index_sell = self._getTransactionData('AskOrder', transaction_array)

            order_vol = self._getOrderData('Volume', order_array)
            order_dir = self._getOrderData('BSFlag', order_array)
            order_index = self._getOrderData('OrderIndex', order_array)
            order_vol_sell = order_vol[order_dir == 2.0]
            order_index_sell = order_index[order_dir == 2.0]

            order_vol_sell = np.nansum(order_vol_sell[[x in trade_index_sell for x in order_index_sell]])
            tick_vol_sell = np.nansum(trade_vol[(trade_dir == 2.0) & np.array([x in order_index_sell for x in trade_index_sell])])

            buy_trade_order_ratio = tick_vol_sell / order_vol_sell if order_vol_sell > 1e-6 else 0
            trade_order_ratio_list.append(buy_trade_order_ratio)
        else:
            trade_order_ratio_list.append(None)

        filter_trade_order_ratio_list = list(filter(lambda x: x is not None, trade_order_ratio_list))

        if len(filter_trade_order_ratio_list) > 0:
            factor_value = np.nanmean(filter_trade_order_ratio_list[-self.__lag:])
        else:
            factor_value = 0.

        self._addFactorValue(factor_value)
