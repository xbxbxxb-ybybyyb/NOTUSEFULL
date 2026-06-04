from System.Factor import Factor
import numpy as np


class FactorBidQtyRate(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        transaction_array = self._getLastTickData("Transactions")

        if transaction_array is not None:
            trade_vol = self._getTransactionData('Volume', transaction_array)
            trade_dir = self._getTransactionData('BSFlag', transaction_array)

            trade_vol_buy = np.nansum(trade_vol[trade_dir == 1.0])
        else:
            trade_vol_buy = 0.

        cbid_vol_qty = self._getLastNTickData("BidQty", self.__lag + 1)
        cbid_vol_qty = self.__process_last_n_qty(cbid_vol_qty, self.__lag)

        bid_vol_qty = np.nansum(cbid_vol_qty)

        factor_value = trade_vol_buy / bid_vol_qty if bid_vol_qty > 1e-6 else 0.

        if np.isnan(factor_value):
            factor_value = 0.

        self._addFactorValue(factor_value)

    @staticmethod
    def __process_last_n_qty(x, lag):
        x_new = np.clip(np.diff(x), a_min=0, a_max=np.inf)
        if len(x_new) < lag:
            x_new = np.hstack((0, x_new))
        return x_new
