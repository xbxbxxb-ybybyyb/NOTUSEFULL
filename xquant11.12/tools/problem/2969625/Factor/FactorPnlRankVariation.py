from System.Factor import Factor
import numpy as np


class FactorPnlRankVariation(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__tlag = self._getParameter("TrendLag")
        self.__index_name = self._getParameter("IndexName")

    def calculate(self):

        rank_pct_list = self._getLastNINFTickData(self.__index_name, "MidPriceReturnsRank_{}".format(self.__lag), self.__tlag)

        if len(rank_pct_list) > 5:
            x = np.array(range(len(rank_pct_list)))
            y = np.array(rank_pct_list)
            beta = self.__get_regression_beta(x, y)
            if beta is not None:
                factorValue = beta * 10
            else:
                lastValue = self.getLastFactorValue()
                if lastValue is not None:
                    factorValue = lastValue
                else:
                    factorValue = 0
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    @staticmethod
    def __get_regression_beta(x, y):
        x, y = np.array(x), np.array(y)
        x_ = x[~(np.isnan(x) | np.isnan(y))]
        y_ = y[~(np.isnan(x) | np.isnan(y))]
        if len(x_) < 3 or len(x_) / len(x) < 0.5:
            beta = np.nan
        else:
            beta = np.cov(y_, x_, bias=True)[0, 1] / np.var(x_)
        return beta
