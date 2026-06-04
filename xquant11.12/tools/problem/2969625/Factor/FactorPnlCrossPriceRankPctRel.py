from System.Factor import Factor
import numpy as np


class FactorPnlCrossPriceRankPctRel(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")
        self.__iwindow = self._getParameter("IndexWindow")
        self.__indexName = self._getParameter("IndexName")

    def calculate(self):

        price_ind = self._getAllTodayINFTickData(self.__indexName, 'LastPrice')
        price = self._getAllTodayTickData('LastPrice')

        # 指数刚开始Tick可能取不到
        if len(price_ind) > 0:
            rank_ind = self.rankpercentile(price_ind, price_ind[-1], self.__iwindow)
            rank = self.rankpercentile(price, price[-1], self.__window)
            factorValue = rank - rank_ind
        else:
            factorValue = 0

        self._addFactorValue(factorValue)
    
    def rankpercentile(self, origin_list, a, window):
        array = np.array(origin_list[-window:])
        return np.sum((array < a)) / len(array)

