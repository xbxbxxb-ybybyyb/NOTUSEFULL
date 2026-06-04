from System.Factor import Factor
import numpy as np


class FactorOrderBuyCancelRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self._addIntermediate("order_cancel_list", [])

    def calculate(self):
        order_array = self._getLastTickData('Orders')
        cancel_array = self._getLastTickData('Cancellations')

        if order_array is not None:
            order_vol = self._getOrderData('Volume', order_array)
            order_dir = self._getOrderData('BSFlag', order_array)
            order_vol_buy = np.nansum(order_vol[order_dir == 1.0])
        else:
            order_vol_buy = 0.

        if cancel_array is not None:
            cancel_vol = self._getCancellationData('Volume', cancel_array)
            cancel_dir = self._getCancellationData('BSFlag', cancel_array)
            cancel_vol_buy = np.nansum(cancel_vol[cancel_dir == 1.0])
        else:
            cancel_vol_buy = 0.

        order_cancel_list = self.getIntermediate("order_cancel_list")
        order_cancel_list.append([order_vol_buy, cancel_vol_buy])
        order_cancel_list = order_cancel_list[-self.__lag:]
        total_order_vol_buy = np.nansum([x[0] for x in order_cancel_list])
        total_cancel_vol_buy = np.nansum([x[1] for x in order_cancel_list])
        if total_order_vol_buy > 1e-6:
            factor_value = total_cancel_vol_buy / total_order_vol_buy
        else:
            factor_value = 0.0
        self._addFactorValue(factor_value)
