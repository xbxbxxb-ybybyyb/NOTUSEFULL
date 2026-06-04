from System.Factor import Factor
import numpy as np


class FactorWeightedReturns(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__tags = self._getParameter("Tags")

    def calculate(self):
        last_price_list = self._getAllTodayTickData("LastPrice")
        rtns_list = []
        for i in self.__tags:
            rtns_list.append(last_price_list[-1] / last_price_list[- np.nanmin([i * 20 - 1,
                                                                                len(last_price_list)])] - 1)
        factorValue = np.dot(rtns_list, self.__tags[::-1])

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
