from System.Factor import Factor
import numpy as np


class FactorAskDealMaxRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__askDealVolume = self._getFactor(
            {
                "ClassName": "AskDealVolume",
            }
        )
        self._addIntermediate("AskDealMaxList", [])
        self._addIntermediate("VolList", [])

    def calculate(self):
        ask_deal_max_list = self.getIntermediate("AskDealMaxList")
        vol_list = self.getIntermediate("VolList")
        ask_deal = self.__askDealVolume.getLastFactorValue()
        vol = self._getLastTickData("Volume")

        if ask_deal is not None:
            ask_deal_max_list.append(np.nanmax(list(ask_deal.values())))
            vol_list.append(vol)
        else:
            ask_deal_max_list.append(None)
            vol_list.append(None)

        filter_ask_deal_max_list = list(filter(lambda x: x is not None, ask_deal_max_list))
        filter_vol_list = list(filter(lambda x: x is not None, vol_list))

        if np.nansum(filter_vol_list[-self.__lag:]) != 0:
            factorValue = np.nansum(filter_ask_deal_max_list[-self.__lag:]) / np.nansum(filter_vol_list[-self.__lag:])
        else:
            lastValue = self.getLastFactorValue()
            if lastValue is not None:
                factorValue = lastValue
            else:
                factorValue = 0

        self._addFactorValue(factorValue)
