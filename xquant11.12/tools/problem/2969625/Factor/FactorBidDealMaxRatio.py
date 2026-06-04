from System.Factor import Factor
import numpy as np


class FactorBidDealMaxRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__bidDealVolume = self._getFactor(
            {
                "ClassName": "BidDealVolume",
            }
        )
        self._addIntermediate("BidDealMaxList", [])
        self._addIntermediate("VolList", [])

    def calculate(self):
        bid_deal_max_list = self.getIntermediate("BidDealMaxList")
        vol_list = self.getIntermediate("VolList")
        bid_deal = self.__bidDealVolume.getLastFactorValue()
        vol = self._getLastTickData("Volume")

        if bid_deal is not None:
            bid_deal_max_list.append(np.nanmax(list(bid_deal.values())))
            vol_list.append(vol)
        else:
            bid_deal_max_list.append(None)
            vol_list.append(None)

        filter_bid_deal_max_list = list(filter(lambda x: x is not None, bid_deal_max_list))
        filter_vol_list = list(filter(lambda x: x is not None, vol_list))

        if np.nansum(filter_vol_list[-self.__lag:]) != 0:
            factorValue = np.nansum(filter_bid_deal_max_list[-self.__lag:]) / np.nansum(filter_vol_list[-self.__lag:])
        else:
            lastValue = self.getLastFactorValue()
            if lastValue is not None:
                factorValue = lastValue
            else:
                factorValue = 0

        self._addFactorValue(factorValue)
