from System.Factor import Factor
import numpy as np


class FactorOrderActiveBuyRatio(Factor):
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
            trade_index_buy = self._getTransactionData('BidOrder', transaction_array)

            order_vol = self._getOrderData('Volume', order_array)
            order_dir = self._getOrderData('BSFlag', order_array)
            order_index = self._getOrderData('OrderIndex', order_array)
            order_vol_buy = order_vol[order_dir == 1.0]
            order_index_buy = order_index[order_dir == 1.0]

            order_vol_buy = np.nansum(order_vol_buy[[x in trade_index_buy for x in order_index_buy]])
            tick_vol_buy = np.nansum(trade_vol[(trade_dir == 1.0) & np.array([x in order_index_buy for x in trade_index_buy])])

            buy_trade_order_ratio = tick_vol_buy / order_vol_buy if order_vol_buy > 1e-6 else 0.
            trade_order_ratio_list.append(buy_trade_order_ratio)
        else:
            trade_order_ratio_list.append(None)

        filter_trade_order_ratio_list = list(filter(lambda x: x is not None, trade_order_ratio_list))

        if len(filter_trade_order_ratio_list) > 0:
            factor_value = np.nanmean(filter_trade_order_ratio_list[-self.__lag:])
        else:
            factor_value = 0.

        self._addFactorValue(factor_value)
