from System.Factor import Factor
import numpy as np


class Bid1Price(Factor):
    def calculate(self):
        bid1 = self._getLastTickData('BidPrice')[0]
        self._addFactorValue(bid1)
