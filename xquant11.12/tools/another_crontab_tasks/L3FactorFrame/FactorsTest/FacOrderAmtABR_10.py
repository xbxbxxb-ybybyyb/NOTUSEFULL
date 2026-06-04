import numpy as np
import math
from collections import namedtuple
from L3FactorFrame.FactorBase import FactorBase


class FacOrderAmtABR_10(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        self.lag = 100
        self.spTime = np.float(marketDataManager.date + "093000000")
        self.validStartIndex = -1

    def calculate(self):
        side = self.getPrevNOrder("BSFlag", self.lag)
        order_price = self.getPrevNOrder("Price", self.lag)
        order_qty = self.getPrevNOrder("Volume", self.lag)

        maskb = (side == 1) & (order_price>0.01)
        maska = (side == 2) & (order_price>0.01)

        vb1 = np.sum(order_qty[side==1])
        mb1 = np.sum(order_price[maskb]*order_qty[maskb])
        mb2 = np.sum(order_qty[(side==1) & (order_price<0.01)])
        vs1 = np.sum(order_qty[side==2])
        ms1 = np.sum(order_price[maska]*order_qty[maska])
        ms2 = np.sum(order_qty[(side==2) & (order_price<0.01)])


        if vb1 > 0.01:
            vwap_b = mb1 / vb1
        else:
            last_price_v = self.getPrevNTick("last_price", self.lag)
            vwap_b = np.mean(last_price_v)

        mb2 = mb2 * vwap_b
        mb = mb1 + mb2

        if vs1 > 0.01:
            vwap_s = ms1 / vs1
        else:
            last_price_v = self.getPrevNTick("last_price", self.lag)
            vwap_s = np.mean(last_price_v)

        ms2 = ms2 * vwap_s
        ms = ms1 + ms2

        factorValue = 0
        if mb > 0 and ms > 0:
            factorValue = math.log(mb / ms)
            factorValue = max(min(factorValue, 5), -5)

        # print(self.__class__.__name__, factorValue)
        self.addFactorValue(factorValue)
