from System.Factor import Factor
import numpy as np


class FactorBidOfferQtyRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BOQtyRatio", [])

    def calculate(self):
        qtyratio = self.getIntermediate("BOQtyRatio")
        cbid_vol_qty = self._getLastNTickData("BidQty", 2)
        bid_vol_qty = self.__process_last_n_qty(cbid_vol_qty, 1)[-1]
        cask_vol_qty = self._getLastNTickData("OfferQty", 2)
        ask_vol_qty = self.__process_last_n_qty(cask_vol_qty, 1)[-1]

        vol_trade = self._getLastTickData("Volume")

        qtyratio.append((bid_vol_qty - ask_vol_qty) / vol_trade if vol_trade > 1e-6 else 0.)
        factor_value = np.nanmean(qtyratio[-self.__lag:])

        if np.isnan(factor_value):
            factor_value = 0.

        self._addFactorValue(factor_value)

    @staticmethod
    def __process_last_n_qty(x, lag):
        x_new = np.clip(np.diff(x), a_min=0, a_max=np.inf)
        if len(x_new) < lag:
            x_new = np.hstack((0, x_new))
        return x_new
