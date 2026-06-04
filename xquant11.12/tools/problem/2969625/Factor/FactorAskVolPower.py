from System.Factor import Factor
import numpy as np


class FactorAskVolPower(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__svlag = self._getParameter("LagShort")
        self.__lvlag = self._getParameter("LagLong")

        self.__ask_vwap = self._getFactor(
            {
                "ClassName": "AskVwap"
            }
        )

    def calculate(self):
        ask_price_adjust = self.__ask_vwap.getFactorValueList()[-self.__lag:]
        ask_price_pct = ask_price_adjust[-1] / ask_price_adjust[0] if ask_price_adjust[0] != 0 else 1
        last_vol1 = np.nansum(self._getLastNTickData("Volume", self.__svlag))
        last_vol2 = np.nansum(self._getLastNTickData("Volume", self.__lvlag))
        vol_ratio = last_vol1 / last_vol2 if last_vol2 != 0 else 1
        factor_value = vol_ratio / ask_price_pct if ask_price_pct != 0 else 0
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
