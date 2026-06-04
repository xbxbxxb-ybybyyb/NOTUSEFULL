from System.Factor import Factor
import numpy as np


class FactorOrderExcessSellRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self._addIntermediate("vol_ratio", [])

    def calculate(self):
        bid0 = self._getLastNTickData('BidPrice', 2)[0][0]
        order_array = self._getLastTickData('Orders')
        vol_ratio = self.getIntermediate("vol_ratio")
        if order_array is not None:
            order_price = self._getOrderData('Price', order_array)
            order_vol = self._getOrderData('Volume', order_array)
            order_dir = self._getOrderData('BSFlag', order_array)
            order_vol_buy = np.nansum(order_vol[order_dir == 2.0])
            order_vol_excess = np.nansum(order_vol[(order_dir == 2.0) & (order_price <= bid0)])
            vol_ratio.append(order_vol_excess / order_vol_buy if order_vol_buy > 1e-6 else 0.)
        else:
            vol_ratio.append(0.)
        vol_ratio = vol_ratio[-self.__lag:]
        factor_value = np.nanmean(vol_ratio)
        self._addFactorValue(factor_value)
