from System.Factor import Factor
import numpy as np


class FactorOrderAskAmountK(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self._addIntermediate("OrdersAskAmount", [])

    def calculate(self):
        ordersArray = self._getLastTickData("Orders")
        ordersAskAmount = self.getIntermediate("OrdersAskAmount")

        if ordersArray is not None:
            bsFlag = self._getOrderData("BSFlag", ordersArray)
            prices = self._getOrderData("Price", ordersArray)
            volume = self._getOrderData("Volume", ordersArray)
            ordersAskAmount.append(np.nansum(volume[bsFlag == 2]*prices[bsFlag == 2]))
        else:
            ordersAskAmount.append(0)

        L = min(len(ordersAskAmount), self.__lag)
        if L < 5:
            if len(self.getFactorValueList()) == 0:
                factorValue = 0
            else:
                factorValue = self.getLastFactorValue()
        else:
            ordersAskAmountArray = np.array(ordersAskAmount[-L:])
            if np.mean(ordersAskAmountArray) < 0.1:
                pass
            else:
                ordersAskAmountArray = ordersAskAmountArray/np.mean(ordersAskAmountArray)
            factorValue = self.__get_regression_params(np.arange(L), ordersAskAmountArray)[1] * 100

        self._addFactorValue(factorValue)

    @staticmethod
    def __get_regression_params(x, y):
        x_ = x[~(np.isnan(x) | np.isnan(y))]
        y_ = y[~(np.isnan(x) | np.isnan(y))]
        if len(x_) < 3 or len(x_) / len(x) < 0.5:
            alpha, beta = 0, 0
        else:
            beta = (np.sum(x_ * y_) - np.sum(x_) * np.mean(y_)) / np.var(x_) / len(x_)
            alpha = np.mean(y_) - beta * np.mean(x_)
        return alpha, beta
