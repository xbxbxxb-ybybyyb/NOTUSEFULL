import math
from collections import namedtuple
from L3FactorFrame.FactorBase import FactorBase
import numpy as np


class FacBuySideGap(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        self.lag = 20
        self.weight_ratios = [0] * 10

        sum_val = 0
        for i in range(10):
            sum_val += 0.8 ** i
            self.weight_ratios[i] = 0.8 ** i

        for i in range(10):
            self.weight_ratios[i] = np.array(self.weight_ratios[i] / sum_val)

    def calculate(self):
        low_price = self.getPrevTick("low_price")
        bid_qty_v = self.getPrevNTick("BidVolume", self.lag)
        bid_price_v = self.getPrevNTick("BidPrice", self.lag)


        size = len(bid_qty_v)
        if size == 0:
            return 0

        gap_sum = 0
        for i in range(len(bid_qty_v)):
            vol_sum = np.sum(bid_qty_v[i] * self.weight_ratios)
            amt_sum = np.sum(bid_qty_v[i] * bid_price_v[i] * self.weight_ratios)

            vwap = amt_sum / vol_sum if vol_sum > 1e-4 else low_price
            gap = (vwap / bid_price_v[i][0] if bid_price_v[i][0] > 1e-4 else low_price - 1) * 1000 #过去n秒平均价格相对1档价格的差距
            gap_sum += gap
        value = (gap - gap_sum / size) * 100

        # print(self.__class__.__name__, value)
        self.addFactorValue(value)
