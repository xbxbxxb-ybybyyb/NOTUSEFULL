from System.Factor import Factor
import numpy as np


class FactorOrderBSRatioRadical(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self._addIntermediate("order_bs_ratio", [])

    def calculate(self):
        bid0_price = self._getLastTickData("BidPrice")[0]
        ask0_price = self._getLastTickData("AskPrice")[0]
        order_array = self._getLastTickData('Orders')
        if order_array is not None:
            order_price = self._getOrderData('Price', order_array)
            order_vol = self._getOrderData('Volume', order_array)
            order_dir = self._getOrderData('BSFlag', order_array)
            order_vol_buy_mid = np.nansum(order_vol[(order_dir == 1.0) & (order_price >= bid0_price)])
            order_vol_sell_mid = np.nansum(order_vol[(order_dir == 2.0) & (order_price <= ask0_price)])
            bs_ratio_mid = order_vol_buy_mid / order_vol_sell_mid if order_vol_sell_mid > 1e-6 else 0.
        else:
            bs_ratio_mid = 0
        order_bs_ratio = self.getIntermediate("order_bs_ratio")
        order_bs_ratio.append(bs_ratio_mid)
        factor_value = np.nanmean(order_bs_ratio[-self.__lag:])
        self._addFactorValue(factor_value)
