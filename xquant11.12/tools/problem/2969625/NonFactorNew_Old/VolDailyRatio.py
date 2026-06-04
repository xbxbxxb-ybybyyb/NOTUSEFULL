"""成交量放大倍数"""

import numpy as np
from System.Factor import Factor


class VolDailyRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.lag_min = self._getParameter("LagMin")
        self.lag_day = self._getParameter("LagDay")

    def calculate(self):
        # lag1 > lag2
        vol_day_array = self._getLastNHistoricalDailyData("Volume", self.lag_day)
        vol_min_array = self._getLastNTickData("Volume", self.lag_min)
        if np.nanmean(vol_day_array) > 0:
            factorValue = np.nanmean(vol_min_array) / np.nanmean(vol_day_array)
        else:
            factorValue = 0

        self._addFactorValue(factorValue)
