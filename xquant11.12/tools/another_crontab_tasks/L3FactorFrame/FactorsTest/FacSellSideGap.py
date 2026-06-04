import math
from collections import namedtuple
from typing import List
from L3FactorFrame.FactorBase import FactorBase
from xquant.xqutils.perf_profile import profile
import numpy as np

class FacSellSideGap(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        self.lag = 20

        weightRatio = [0.0] * 10

        sum_val = 0

        for i in range(10):
            tmp = pow(0.8, i)
            weightRatio[i] = tmp
            sum_val += tmp

        for i in range(10):
            weightRatio[i] /= sum_val

        self.weightRatio = np.array(weightRatio)

    # @profile
    def calculate(self):
        ask_price_v = self.getPrevNTick("AskPrice", self.lag)
        ask_qty_v = self.getPrevNTick("AskVolume", self.lag)
        maxPrice = self.getPrevTick("high_price")

        gap = 0
        gapSum = 0

        for i in range(len(ask_price_v)):
            volSum = np.sum(ask_qty_v[i]*self.weightRatio)
            amtSum = np.sum(ask_qty_v[i]*ask_price_v[i]*self.weightRatio)

            vwap = amtSum / volSum if volSum > 1e-4 else maxPrice
            gap = (vwap / (ask_price_v[i][0] if ask_price_v[i][0] > 1e-4 else maxPrice) - 1) * 1000
            gapSum += gap

        value = (gap - gapSum / len(ask_price_v)) * 100

        # print(self.__class__.__name__, value)
        self.addFactorValue(value)
