from System.Factor import Factor
import numpy as np


class FactorAsk1ConsumptionRate(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__bidPVolume = self._getFactor(
            {
                "ClassName": "BidPVolume",
            }
        )
        self._addIntermediate("AskConsumpVolumeList", [])
        self._addIntermediate("Ask1VolumeList", [])

    def calculate(self):

        acv_list = self.getIntermediate("AskConsumpVolumeList")
        askv_list = self.getIntermediate("Ask1VolumeList")
        tsp = self._getAllTodayTickData("Timestamp")
        ask1v = self._getLastTickData("AskVolume")[0]

        if len(tsp) == 1:
            factorValue = 0.
            acv_list.append(np.nan)
            askv_list.append(np.nan)
        else:
            askp = self._getLastNTodayTickData("AskPrice", 2)[0][0]
            bidpv_dict = self.__bidPVolume.getLastFactorValue()
            if bidpv_dict is not None and askp in bidpv_dict:
                acv = bidpv_dict[askp]
            else:
                acv = 0.
            acv_list.append(acv)
            askv_list.append(ask1v)

            acv_mean = np.nanmean(acv_list[-self.__lag:])  # 平均消耗速度
            askv_mean = np.nanmean(askv_list[-self.__lag:])  # 平均卖一挂单量

            if (askv_mean != 0) and not np.isnan(acv_mean) and not np.isnan(askv_mean):
                factorValue = acv_mean / askv_mean
            else:
                lastValue = self.getLastFactorValue()
                if lastValue is not None:
                    factorValue = lastValue
                else:
                    factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
