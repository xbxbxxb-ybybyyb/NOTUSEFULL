import numpy as np
from System.Factor import Factor


class BidOrderVwap(Factor):

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

            buy_price = order_price[order_dir == 1]
            buy_vol = order_vol[order_dir == 1]
            buy_price[buy_price > ask0_price * (1 + self.__percentile)] = ask0_price * (1 + self.__percentile)
            buy_vol[buy_price < bid0_price * (1 - self.__percentile)] = 0

            buy_vol_total = np.nansum(buy_vol)
            if buy_vol_total > 1e-6 and ask0_price != 0:
                order_buy_price_vwap = np.nansum(buy_price * buy_vol) / buy_vol_total

        self._addFactorValue(order_buy_price_vwap)