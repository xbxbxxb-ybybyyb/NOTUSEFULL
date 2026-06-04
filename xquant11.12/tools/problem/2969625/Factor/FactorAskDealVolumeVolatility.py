from System.Factor import Factor
import numpy as np


class FactorAskDealVolumeVolatility(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__askDealVolume = self._getFactor(
            {
                "ClassName": "AskDealVolume",
            }
        )

    def calculate(self):
        vol_mean = np.nanmean(self._getAllTodayTickData("Volume")[:10])
        ask_deal = self.__askDealVolume.getFactorValueList()[-self.__lag:]

        ask_deal_vol = []
        for each in ask_deal:
            if each is not None:
                ask_deal_vol.extend(list(each.values()))

        if (vol_mean > 0) and (len(ask_deal_vol) > 0):
            factorValue = np.nanstd(ask_deal_vol) / vol_mean / 10
        else:
            lastValue = self.getLastFactorValue()
            if lastValue is not None:
                factorValue = lastValue
            else:
                factorValue = 0

        self._addFactorValue(factorValue)
