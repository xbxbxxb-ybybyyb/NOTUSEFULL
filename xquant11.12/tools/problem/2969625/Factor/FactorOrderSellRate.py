from System.Factor import Factor
import numpy as np


class FactorOrderSellRate(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self._addIntermediate("order_bs_ratio", [])

    def calculate(self):
        bid0_price = self._getLastTickData("BidPrice")[0]
        ask0_price = self._getLastTickData("AskPrice")[0]
        trade_vol = self._getLastTickData("Volume")
        order_array = self._getLastTickData('Orders')
        if order_array is not None:
            order_price = self._getOrderData('Price', order_array)
            order_vol = self._getOrderData('Volume', order_array)
            order_dir = self._getOrderData('BSFlag', order_array)
            order_vol_sell1 = np.nansum(order_vol[(order_dir == 2.0) & (order_price >= bid0_price)])
            order_vol_sell2 = np.nansum(order_vol[(order_dir == 2.0) & (order_price <= ask0_price)])
            bs_ratio = (order_vol_sell1 - order_vol_sell2) / trade_vol if trade_vol > 1e-6 else 0.
        else:
            bs_ratio = 0.
        order_bs_ratio = self.getIntermediate("order_bs_ratio")
        order_bs_ratio.append(bs_ratio)
        factor_value = np.nanmean(order_bs_ratio[-self.__lag:])
        self._addFactorValue(factor_value)
