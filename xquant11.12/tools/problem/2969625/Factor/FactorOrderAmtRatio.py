from System.Factor import Factor
import numpy as np


class FactorOrderAmtRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self._addIntermediate("amt_ratio", [])

    def calculate(self):
        bid0_price = self._getLastTickData("BidPrice")[0]
        ask0_price = self._getLastTickData("AskPrice")[0]
        order_array = self._getLastTickData('Orders')
        if order_array is not None:
            order_price = self._getOrderData('Price', order_array)
            order_vol = self._getOrderData('Volume', order_array)
            order_dir = self._getOrderData('BSFlag', order_array)

            sell_price = order_price[order_dir == 2.0]
            sell_vol = order_vol[order_dir == 2.0]
            sell_price[sell_price < bid0_price * 0.99] = bid0_price * 0.99
            sell_vol[sell_price > ask0_price * 1.01] = 0
            sell_amt_total = np.nansum(sell_price * sell_vol)

            buy_price = order_price[order_dir == 1.0]
            buy_vol = order_vol[order_dir == 1.0]
            buy_price[buy_price < bid0_price * 0.99] = bid0_price * 0.99
            buy_vol[buy_price > ask0_price * 1.01] = 0
            buy_amt_total = np.nansum(buy_price * buy_vol)

            amt_ratio = buy_amt_total / sell_amt_total if sell_amt_total > 1e-6 else 0.

        else:
            amt_ratio = 0.
        amt_ratio_list = self.getIntermediate("amt_ratio")
        amt_ratio_list.append(amt_ratio)
        factor_value = np.nanmean(amt_ratio_list[-self.__lag:])
        self._addFactorValue(factor_value)
