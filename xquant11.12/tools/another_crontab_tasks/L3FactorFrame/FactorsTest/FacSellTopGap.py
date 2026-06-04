from typing import List
from collections import namedtuple
from L3FactorFrame.FactorBase import FactorBase
import numpy as np
from xquant.xqutils.perf_profile import profile

class FacSellTopGap(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        self.lag = 40
        self.level = 2

    def calculate(self):
        max_price = self.getPrevTick("high_price")
        min_price = self.getPrevTick("low_price")
        ask_price_v = self.getPrevNTick("AskPrice", self.lag)
        ask_qty_v = self.getPrevNTick("AskVolume", self.lag)
        bid_qty_v = self.getPrevNTick("BidVolume", self.lag)
        bid_price_v = self.getPrevNTick("BidPrice", self.lag)

        ratio_sum = 0
        if len(ask_price_v) < 2:
            self.addFactorValue(0)
        else:
            ratio_sum = 0
            for i in range(len(ask_price_v)):
                bid_v_sum = np.sum(bid_price_v[i])
                bid_amount = np.sum(bid_price_v[i] * bid_qty_v[i])
                bid_vwap = bid_amount / bid_v_sum if bid_v_sum > 0 else min_price
                # 第2大索引
                top_idx = np.argsort(ask_qty_v[i])[-2:]
                ask_v_sum = 0
                ask_amount = 0
                for idx in top_idx:
                    ask_v_sum += ask_qty_v[i][idx]
                    ask_amount += ask_price_v[i][idx] * ask_qty_v[i][idx]

                ask_top_price = ask_amount / ask_v_sum if ask_v_sum > 1e-4 else max_price
                ratio = (1- bid_vwap/ask_top_price ) * 1000 if ask_top_price > 1e-4 else 0.0
                ratio_sum += ratio
            factor_value = (ratio - ratio_sum/len(ask_price_v)) * 100
            # print(factor_value)
            self.addFactorValue(factor_value)


