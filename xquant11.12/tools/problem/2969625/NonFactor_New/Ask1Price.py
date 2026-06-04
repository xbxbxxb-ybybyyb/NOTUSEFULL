from System.Factor import Factor
import numpy as np


class Ask1Price(Factor):
    def calculate(self):
        ask1 = self._getLastTickData('AskPrice')[0]
        self._addFactorValue(ask1)
