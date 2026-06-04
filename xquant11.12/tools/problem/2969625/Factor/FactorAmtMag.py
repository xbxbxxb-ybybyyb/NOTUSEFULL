from System.Factor import Factor
import numpy as np


class FactorAmtMag(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag1 = self._getParameter("Lag1")
        self.__lag2 = self._getParameter("Lag2")

    def calculate(self):
        # lag1 > lag2
        amt_list = self._getLastNTickData("Amount", self.__lag1)
        if np.nanmean(amt_list) != 0:
            factor_value = np.nanmean(amt_list[-self.__lag2:]) / np.nanmean(amt_list)
        else:
            last_value = self.getLastFactorValue()
            if last_value is not None:
                factor_value = last_value
            else:
                factor_value = 0
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
