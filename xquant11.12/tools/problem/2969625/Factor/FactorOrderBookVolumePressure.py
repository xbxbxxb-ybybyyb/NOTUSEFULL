import math
import numpy as np
from System.Factor import Factor


class FactorOrderBookVolumePressure(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__emaLag = self._getParameter("EMALag")
        self.__decayRatio = self._getParameter("DecayRatio")

    def calculate(self):
        factorValueList = self.getFactorValueList()

        pressure = self._calculate_pressure(self.__decayRatio)
        value = self._EMA_calculate(pressure, factorValueList, self.__emaLag)

        self._addFactorValue(value)

    def _calculate_pressure(self, decayRatio):
        askVolume = self._getLastTickData("AskVolume")
        bidVolume = self._getLastTickData("BidVolume")

        ask_vol_order_book = askVolume[np.nonzero(askVolume)]
        bid_vol_order_book = bidVolume[np.nonzero(bidVolume)]

        decay_ask = np.array( [decayRatio ** i for i in range(len(ask_vol_order_book))] )
        decay_bid = np.array( [decayRatio ** i for i in range(len(bid_vol_order_book))] )

        ask_order_book_ave_vol = 0
        bid_order_book_ave_vol = 0

        if len(ask_vol_order_book) != 0:
            ask_order_book_ave_vol = np.nanmean(ask_vol_order_book * decay_ask)

        if len(bid_vol_order_book) != 0:
            bid_order_book_ave_vol = np.nanmean(bid_vol_order_book * decay_bid)
        
        if math.isnan(ask_order_book_ave_vol):
            ask_order_book_ave_vol = 0
        
        if math.isnan(bid_order_book_ave_vol):
            bid_order_book_ave_vol = 0

        pressure_value = 0.

        if ask_order_book_ave_vol > 0 and bid_order_book_ave_vol > 0:
            pressure_value = math.log(ask_order_book_ave_vol) - math.log(bid_order_book_ave_vol)

        return pressure_value

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])

