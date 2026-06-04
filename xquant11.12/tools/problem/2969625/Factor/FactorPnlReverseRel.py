from System.Factor import Factor
import numpy as np


class FactorPnlReverseRel(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")
        self.__shortWindow = int(self.__window / 2)
        self.__indexName = self._getParameter("IndexName")

    def calculate(self):
        volume_ind = self._getAllTodayINFTickData(self.__indexName, 'Volume')
        volume_ratio = self.rel(volume_ind, self.__shortWindow, self.__window) if len(volume_ind) > 0 else 0.

        price_list = self._getAllTodayTickData('LastPrice')
        price_move = (self.rel(price_list, self.__shortWindow, self.__window) - 1) * 10000

        factorValue = price_move * volume_ratio

        self._addFactorValue(factorValue)

    def rel(self, ema_list, short_length, length):
        if len(ema_list) <= short_length:
            short_ma = np.nanmean(np.array(ema_list[-int(len(ema_list) / 2):]))
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











