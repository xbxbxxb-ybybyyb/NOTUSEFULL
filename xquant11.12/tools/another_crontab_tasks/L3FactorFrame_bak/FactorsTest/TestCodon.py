from FactorBase import FactorBase
import numpy as np
from xquant.xqutils.perf_profile import profile
from numba import jit
import codon


# @jit(nopython=False)
def func(ask_price_v, ask_qty_v, bid_price_v, bid_qty_v, max_price, min_price):
    ask_v_sum = np.sum(ask_price_v)
    ask_amount = np.sum(ask_price_v * ask_qty_v)
    ask_vwap = ask_amount / ask_v_sum if ask_v_sum > 0 else max_price
    # 第2大索引
    top_idx = np.argsort(bid_qty_v)[-2:]
    bid_v_sum = 0
    bid_amount = 0
    for idx in top_idx:
        bid_v_sum += bid_qty_v[idx]
        bid_amount += bid_price_v[idx] * bid_qty_v[idx]

    bid_top_price = bid_amount / bid_v_sum if bid_v_sum > 1e-4 else min_price

    ratio = (ask_vwap / bid_top_price - 1) * 1000 if bid_top_price > 1e-4 else 0.0
    return ratio


class TestCodon(FactorBase):
    def __init__(self, config, marketDataManager):
        super().__init__(config, marketDataManager)
        self.lag = 40
        self.level = 2
        self.ratio_arr = []

    def calculate(self):
        max_price = self.getPrevTick("high_price")
        min_price = self.getPrevTick("low_price")
        ask_price_v = self.getPrevTick("AskPrice")
        ask_qty_v = self.getPrevTick("AskVolume")
        bid_qty_v = self.getPrevTick("BidVolume")
        bid_price_v = self.getPrevTick("BidPrice")

        ratio_sum = 0
        # TODO: 可优化卖方vwap加权价
        ratio = func(ask_price_v, ask_qty_v, bid_price_v, bid_qty_v, max_price, min_price)
        self.ratio_arr.append(ratio)
        ratio_mean = sum(self.ratio_arr[-self.lag:])
        factor_value = (ratio - ratio_mean/min(self.lag, len(self.ratio_arr))) * 100
        self.addFactorValue(factor_value)

