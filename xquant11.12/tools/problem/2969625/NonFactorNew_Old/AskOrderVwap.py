import numpy as np
from System.Factor import Factor


class AskOrderVwap(Factor):

    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__percentile = self._getParameter("percentile")

    def calculate(self):
        bid0_price = self._getLastTickData("BidPrice")[0]
        ask0_price = self._getLastTickData("AskPrice")[0]
        order_array = self._getLastTickData('Orders')
        order_buy_price_vwap = 0
        if order_array is not None:
            order_price = self._getOrderData('Price', order_array)
            order_vol = self._getOrderData('Volume', order_array)
            order_dir = self._getOrderData('BSFlag', order_array)

            sell_price = order_price[order_dir == 2]
            sell_vol = order_vol[order_dir == 2]
            # Order 极端价量调整
            sell_price[sell_price < bid0_price * (1 - self.__percentile)] = bid0_price * (1 - self.__percentile)
            sell_vol[sell_price > ask0_price * (1 + self.__percentile)] = 0

            sell_vol_total = np.nansum(sell_vol)
            if sell_vol_total > 1e-6 and ask0_price != 0:
                order_buy_price_vwap = np.nansum(sell_price * sell_vol) / sell_vol_total

        self._addFactorValue(order_buy_price_vwap)
