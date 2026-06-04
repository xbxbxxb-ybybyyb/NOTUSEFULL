from System.Factor import Factor
import numpy as np


class FactorBidVolPower(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__svlag = self._getParameter("LagShort")
        self.__lvlag = self._getParameter("LagLong")

        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwap"
            }
        )

    def calculate(self):
        bid_price_adjust = self.__bid_vwap.getFactorValueList()[-self.__lag:]
        bid_price_pct = bid_price_adjust[-1] / bid_price_adjust[0] if bid_price_adjust[0] != 0 else 1
        last_vol1 = np.nansum(self._getLastNTickData("Volume", self.__svlag))
        last_vol2 = np.nansum(self._getLastNTickData("Volume", self.__lvlag))
        vol_ratio = last_vol1 / last_vol2 if last_vol2 != 0 else 1
        factor_value = bid_price_pct / vol_ratio if vol_ratio != 0 else 0
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
