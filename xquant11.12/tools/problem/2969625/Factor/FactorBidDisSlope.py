from System.Factor import Factor
import numpy as np


class FactorBidDisSlope(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwap"
            }
        )

    def calculate(self):
        bid_price_adjust = self.__bid_vwap.getFactorValueList()[-self.__lag:]
        if bid_price_adjust[0] != 0:
            bid_price_adjust = np.array(bid_price_adjust) / bid_price_adjust[0]
            factor_value = self.get_regression_params(bid_price_adjust, np.arange(len(bid_price_adjust)))[1] / 1e6
        else:
            factor_value = 0.

        if np.isnan(factor_value):
            factor_value = 0.
        self._addFactorValue(factor_value)

    @staticmethod
    def get_regression_params(x, y):
        x, y = np.array(x), np.array(y)
        x_ = x[~(np.isnan(x) | np.isnan(y))]
        y_ = y[~(np.isnan(x) | np.isnan(y))]
        if len(x_) / len(x) < 0.5 or len(x_) < 3:
            return np.nan, np.nan
        if np.var(x_) > 1e-6:
            beta = np.cov(y_, x_, bias=True)[0, 1] / np.var(x_)
            alpha = np.mean(y_) - beta * np.mean(x_)
        else:
            beta, alpha = np.nan, np.nan
        return alpha, beta
