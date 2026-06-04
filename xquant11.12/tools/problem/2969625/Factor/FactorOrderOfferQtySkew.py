from scipy.stats import skew
from System.Factor import Factor
import numpy as np


class FactorOrderOfferQtySkew(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        cqty = self._getLastNTickData("OfferQty", self.__lag + 1)
        qty = self.__process_last_n_qty(cqty, self.__lag)

        factorValue = skew(qty)

        self._addFactorValue(factorValue)

    @staticmethod
    def __process_last_n_qty(x, lag):
        x_new = np.clip(np.diff(x), a_min=0, a_max=np.inf)
        if len(x_new) < lag:
            x_new = np.hstack((0, x_new))
        return x_new

