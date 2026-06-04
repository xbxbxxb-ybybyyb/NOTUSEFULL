from System.Factor import Factor
import numpy as np


class FactorBidOfferQtyGap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        cbid_vol_qty = self._getLastNTickData("BidQty", self.__lag + 1)
        bid_vol_qty = np.nansum(self.__process_last_n_qty(cbid_vol_qty, self.__lag))
        cask_vol_qty = self._getLastNTickData("OfferQty", self.__lag + 1)
        ask_vol_qty = np.nansum(self.__process_last_n_qty(cask_vol_qty, self.__lag))

        factor_value = (bid_vol_qty - ask_vol_qty) / (bid_vol_qty + ask_vol_qty) if (bid_vol_qty + ask_vol_qty) > 1e-6 else 0.

        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)

    @staticmethod
    def __process_last_n_qty(x, lag):
        x_new = np.clip(np.diff(x), a_min=0, a_max=np.inf)
        if len(x_new) < lag:
            x_new = np.hstack((0, x_new))
        return x_new
