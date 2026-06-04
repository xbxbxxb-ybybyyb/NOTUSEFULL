import numpy as np
from System.Factor import Factor


class Factor40PVMove(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("WindowLong")
        self.__shortWindow = self._getParameter("WindowShort")

    def calculate(self):
        vol_list = self._getAllTodayTickData('Volume')
        price_list = self._getAllTodayTickData('LastPrice')
        price_move = (self.rel(price_list, self.__shortWindow, self.__window) - 1) * 100
        vol_move = self.rel(vol_list, self.__shortWindow, self.__window)
        factorValue = price_move * vol_move * 100

        self._addFactorValue(factorValue)

    def rel(self, ema_list, short_length, length):
        if len(ema_list) <= short_length:
            short_ma = np.nanmean(np.array(ema_list[-int(len(ema_list)/2):]))
            long_ma = np.nanmean(np.array(ema_list))
        elif len(ema_list) < length:
            short_ma = np.nanmean(np.array(ema_list[-short_length:]))
            long_ma = np.nanmean(np.array(ema_list))
        else:
            short_ma = np.nanmean(np.array(ema_list[-short_length:]))
            long_ma = np.nanmean(np.array(ema_list[-length:]))
        if long_ma == 0:
            return 0
        else:
            return short_ma / long_ma