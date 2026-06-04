from System.Factor import Factor
import numpy as np


class FactorOrderBSRatioGap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self._addIntermediate("order_bs_ratio", [])

    def calculate(self):
        trade_vol = self._getLastTickData("Volume")
        order_array = self._getLastTickData('Orders')
        if order_array is not None:
            order_vol = self._getOrderData('Volume', order_array)
            order_dir = self._getOrderData('BSFlag', order_array)
            order_vol_buy = np.nansum(order_vol[order_dir == 1.0])
            order_vol_sell = np.nansum(order_vol[order_dir == 2.0])
            order_vol_gap = order_vol_buy - order_vol_sell
            bs_ratio = order_vol_gap / trade_vol if trade_vol > 1e-6 else 0.
        else:
            bs_ratio = 0
        order_bs_ratio = self.getIntermediate("order_bs_ratio")
        order_bs_ratio.append(bs_ratio)
        factor_value = np.nanmean(order_bs_ratio[-self.__lag:])
        self._addFactorValue(factor_value)
