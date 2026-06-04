# 导入需要的包
import numpy as np
from collections import namedtuple
from L3FactorFrame.FactorBase import FactorBase


def get_delta_vol(last_price, last_qty, cur_price, cur_qty, side):
    is_buy = (side == 1)
    meet_zero_condition = (is_buy and cur_price < last_price - 0.01) or (
            not is_buy and cur_qty > last_price + 0.01)
    if meet_zero_condition:
        return 0
    else:
        if is_buy:
            if cur_price > last_price:
                return cur_qty
            else:
                return cur_qty - last_qty
        else:
            if cur_price < last_price:
                return cur_qty
            else:
                return cur_qty - last_qty

class FacVOI(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        self.lag = 10
        self.imbalance_arr = []

    def calculate(self):
        value = 0
        ask_price_v1 = self.getPrevNTick("AskP0", self.lag + 1)
        ask_qty_v1 = self.getPrevNTick("AskV0", self.lag + 1)
        bid_qty_v1 = self.getPrevNTick("BidV0", self.lag + 1)
        bid_price_v1 = self.getPrevNTick("BidP0", self.lag + 1)

        if len(ask_price_v1) >= 2:
            sum_val = 0
            for i in range(len(ask_price_v1) - 1):
                delta_vb = get_delta_vol(bid_price_v1[i],bid_qty_v1[i], bid_price_v1[i+1], bid_qty_v1[i+1], side=1)
                delta_va = get_delta_vol(ask_price_v1[i],ask_qty_v1[i], ask_price_v1[i+1], ask_qty_v1[i+1], side=2)
                delta_sum = abs(delta_va) + abs(delta_vb)
                order_imbalance = ((delta_vb - delta_va) / delta_sum) * 100 if delta_sum > 1e-6 else 0
                sum_val += order_imbalance
            value = sum_val / (len(ask_price_v1) - 1)
            if np.isnan(value):
                value = 0

        self.addFactorValue(value)
