from System.Factor import Factor
import numpy as np


class FactorBidBigDealAmountRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__slag = self._getParameter("ShortLag")
        self.__llag = self._getParameter("LongLag")
        self.__transBOI = self._getFactor(
            {
                "ClassName": "TransActiveBidOrderInfo"
            }
        )
        self._addIntermediate("BidOrderInfoList", [])

    def calculate(self):

        boi_list = self.getIntermediate("BidOrderInfoList")
        boi = self.__transBOI.getLastFactorValue()
        if boi is not None:
            boi_list.append(list(boi.values()))
        else:
            boi_list.append(None)

        filter_boi_list = list(filter(lambda x: x is not None, boi_list))

        if len(filter_boi_list) == 0:
            factorValue = 0.
        elif len(filter_boi_list) <= self.__slag:
            bigd_amt = np.nanmax(filter_boi_list[-1])
            bamt_mean = np.nanmean([each_j for each_i in filter_boi_list for each_j in each_i])
            factorValue = bigd_amt / bamt_mean
        else:
            bigd_amt = np.nanmax([each_j for each_i in filter_boi_list[-self.__slag:] for each_j in each_i])
            bamt_mean = np.nanmean([each_j for each_i in filter_boi_list[-self.__llag:] for each_j in each_i])
            factorValue = bigd_amt / bamt_mean

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

