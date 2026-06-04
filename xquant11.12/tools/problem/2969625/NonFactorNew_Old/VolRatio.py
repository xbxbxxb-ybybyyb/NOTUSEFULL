"""成交量放大倍数"""

import numpy as np
from System.Factor import Factor


class VolRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.lag1 = self._getParameter("Lag1")
        self.lag2 = self._getParameter("Lag2")

    def calculate(self):
        # lag1 > lag2
        vol_list = self._getLastNTickData("Volume", self.lag1)
        if np.nanmean(vol_list) > 0:
            factorValue = np.nanmean(vol_list[-self.lag2:]) / np.nanmean(vol_list)
        else:
            factorValue = 1

        self._addFactorValue(factorValue)
