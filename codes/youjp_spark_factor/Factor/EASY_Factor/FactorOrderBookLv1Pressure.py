import numpy as np
from System.Factor import Factor


class FactorOrderBookLv1Pressure(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__emaLag = self._getParameter("EMALag")

    def calculate(self):
        factorValueList = self.getFactorValueList()

        pressure = self._calculate_pressure()
        value = self._EMA_calculate(pressure, factorValueList, self.__emaLag)

        self._addFactorValue(value)

    def _calculate_pressure(self):
        ask_price_order_book = self._getLastTickData("AskPrice")
        ask_vol_order_book = self._getLastTickData("AskVolume")
        bid_price_order_book = self._getLastTickData("BidPrice")
        bid_vol_order_book = self._getLastTickData("BidVolume")

        if len(ask_vol_order_book) == 0 or len(bid_vol_order_book) == 0 or len(ask_price_order_book) == 0 or len(bid_price_order_book) == 0:
            return 0.
        bid_amount = bid_price_order_book[0] * bid_vol_order_book[0]
        ask_amount = ask_price_order_book[0] * ask_vol_order_book[0]
        if bid_amount == 0 or ask_amount == 0:
            return 0.
        return (bid_amount - ask_amount) / (bid_amount + ask_amount)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])

