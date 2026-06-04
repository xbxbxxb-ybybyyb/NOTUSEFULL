from L3FactorFrame.FactorBase import FactorBase
import numpy as np
from xquant.xqutils.perf_profile import profile
from numba import jit


class FacBuyTopGap(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        self.lag = 40
        self.level = 2

    # @profile
    def calculate(self):
        max_price = self.getPrevTick("high_price")
        min_price = self.getPrevTick("low_price")
        ask_price_v = self.getPrevNTick("AskPrice", self.lag)
        ask_qty_v = self.getPrevNTick("AskVolume", self.lag)
        bid_qty_v = self.getPrevNTick("BidVolume", self.lag)
        bid_price_v = self.getPrevNTick("BidPrice", self.lag)

        # TODO: 可优化卖方vwap加权价
        if len(ask_qty_v)<0:
            self.addFactorValue(0)
        else:
            ratio_sum = 0
            for i in range(len(ask_qty_v)):
                ask_v_sum = np.sum(ask_price_v[i])
                ask_amount = np.sum(ask_price_v[i] * ask_qty_v[i])
                ask_vwap = ask_amount / ask_v_sum if ask_v_sum > 0 else max_price
                # 第2大索引
                top_idx = np.argsort(bid_qty_v[i])[-2:]
                bid_v_sum = 0
                bid_amount = 0
                for idx in top_idx:
                    bid_v_sum += bid_qty_v[i][idx]
                    bid_amount += bid_price_v[i][idx] * bid_qty_v[i][idx]

                bid_top_price = bid_amount / bid_v_sum if bid_v_sum > 1e-4 else min_price
                ratio = (ask_vwap / bid_top_price - 1) * 1000 if bid_top_price > 1e-4 else 0.0
                ratio_sum +=ratio
            factor_value = (ratio_sum/len(ask_qty_v)-ratio) * 100
            self.addFactorValue(factor_value)

