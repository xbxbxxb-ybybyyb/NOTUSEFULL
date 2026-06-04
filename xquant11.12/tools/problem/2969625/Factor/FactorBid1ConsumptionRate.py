from System.Factor import Factor
import numpy as np


class FactorBid1ConsumptionRate(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__askPVolume = self._getFactor(
            {
                "ClassName": "AskPVolume",
            }
        )
        self._addIntermediate("BidConsumpVolumeList", [])
        self._addIntermediate("Bid1VolumeList", [])

    def calculate(self):

        bcv_list = self.getIntermediate("BidConsumpVolumeList")
        bidv_list = self.getIntermediate("Bid1VolumeList")
        tsp = self._getAllTodayTickData("Timestamp")
        bid1v = self._getLastTickData("BidVolume")[0]

        if len(tsp) == 1:
            factorValue = 0
            bcv_list.append(np.nan)
            bidv_list.append(np.nan)
        else:
            bidp = self._getLastNTodayTickData("BidPrice", 2)[0][0]
            askpv_dict = self.__askPVolume.getLastFactorValue()
            if askpv_dict is not None and bidp in askpv_dict:
                bcv = askpv_dict[bidp]
            else:
                bcv = 0
            bcv_list.append(bcv)
            bidv_list.append(bid1v)

            bcv_mean = np.nanmean(bcv_list[-self.__lag:])  # 平均消耗速度
            bidv_mean = np.nanmean(bidv_list[-self.__lag:])  # 平均买一挂单量

            if (bidv_mean != 0) and not np.isnan(bidv_mean) and not np.isnan(bcv_mean):
                factorValue = bcv_mean / bidv_mean
            else:
                lastValue = self.getLastFactorValue()
                if lastValue is not None:
                    factorValue = lastValue
                else:
                    factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
