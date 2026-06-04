import numpy as np
from System.Factor import Factor


class FactorPVCorr(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")
        self.__shortWindow = self._getParameter("ShortWindow")
        
    def calculate(self):
        vol_list = self._getAllTodayTickData('Volume')
        price_list = self._getAllTodayTickData('LastPrice')
        vol_move = (self.rel(vol_list, self.__shortWindow, self.__window) - 1) * 100
        price_move = (self.rel(price_list, self.__shortWindow, self.__window) - 1) * 100
        factorValue = price_move * vol_move

        self._addFactorValue(factorValue)

    @staticmethod
    def rel(ema_list, short_length, length):
        if len(ema_list) <= short_length:
            short_ma = np.nanmean(np.array(ema_list[-int(short_length/2):]))
            long_ma = np.nanmean(np.array(ema_list))
        elif len(ema_list) < length:
            short_ma = np.nanmean(np.array(ema_list[-short_length:]))
            long_ma = np.nanmean(np.array(ema_list))
        else:
            short_ma = np.nanmean(np.array(ema_list[-short_length:]))
            long_ma = np.nanmean(np.array(ema_list[-length:]))
        if long_ma == 0:
            r = 0
        else:
            r = short_ma / long_ma
        return r
