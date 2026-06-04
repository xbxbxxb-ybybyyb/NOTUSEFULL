from System.Factor import Factor
import numpy as np


class Factor200ReverseM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("WindowLong")
        self.__shortWindow = self._getParameter("WindowShort")

    def calculate(self):
        price = self._getLastNTickData('LastPrice', self.__window)
        pre_price = self._getLastTickData('PreviousClose')
        price = np.append(pre_price, price)

        pct = (price[1:] / price[:-1] - 1) * 100
        wt = self.__getWeight(window=self.__window, half_life=self.__shortWindow)
        res = -np.nansum(pct * wt[-len(pct):]) / np.nansum(wt[-len(pct):])

        self._addFactorValue(res)

    def __getWeight(self, window, half_life):
        t = np.power(1 / 2, 1 / half_life)
        wt = np.power(t, np.arange(window - 1, -1, -1))
        return wt











