from System.Factor import Factor
import numpy as np


class FactorBidActiveAmountRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__bidDealAmount = self._getFactor(
            {
                "ClassName": "BidDealAmount",
            }
        )
        self.__activeBidInfo = self._getFactor(
            {
                "ClassName": "ActiveBidInfoByOrder",
            }
        )

        self._addIntermediate("BidActiveDealAmountList", [])
        self._addIntermediate("BidDealAmountList", [])

    def calculate(self):

        bid_deal_amount = self.__bidDealAmount.getLastFactorValue()
        bid_active_info = self.__activeBidInfo.getLastFactorValue()
        bid_deal_amount_list = self.getIntermediate("BidDealAmountList")
        bid_active_deal_amount_list = self.getIntermediate("BidActiveDealAmountList")

        if bid_deal_amount is not None:
            bid_deal_amount_list.append(np.nanmean(list(bid_deal_amount.values())))
        else:
            bid_deal_amount_list.append(0.)

        if bid_active_info is not None:
            bid_active_deal_amount_list.append(np.nanmean([each[0] for each in bid_active_info.values()]))
        else:
            bid_active_deal_amount_list.append(0.)

        if np.nanmean(bid_deal_amount_list[-self.__lag:]) > 1e-6:
            factorValue = np.nanmean(bid_active_deal_amount_list[-self.__lag:]) / np.nanmean(bid_deal_amount_list[-self.__lag:])
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)
