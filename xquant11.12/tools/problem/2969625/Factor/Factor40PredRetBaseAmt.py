import numpy as np
from System.Factor import Factor


class Factor40PredRetBaseAmt(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("WindowLong")
        self.__shortWindow = self._getParameter("WindowShort")

    def calculate(self):
        amt = self._getLastNTickData('Amount', self.__window)
        pre_price = self._getLastTickData('PreviousClose')
        price = self._getLastNTickData('LastPrice', self.__window)
        price = np.append(pre_price, price)
        pct = (price[1:] / price[:-1] - 1) * 100
        cum_pct = np.nansum(pct)

        long_amt = np.nansum(amt)
        short_amt = np.nansum(amt[-self.__shortWindow:])
        if long_amt == 0:
            factorValue = 0
        else:
            factorValue = (cum_pct / long_amt) * short_amt
        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
