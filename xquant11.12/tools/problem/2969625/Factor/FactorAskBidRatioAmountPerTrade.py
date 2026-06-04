from System.Factor import Factor
import numpy as np


class FactorAskBidRatioAmountPerTrade(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__askDealAmount = self._getFactor(
            {
                "ClassName": "AskDealAmount",
            }
        )
        self.__bidDealAmount = self._getFactor(
            {
                "ClassName": "BidDealAmount",
            }
        )

        self._addIntermediate("AskDealAmountList", [])
        self._addIntermediate("BidDealAmountList", [])

    def calculate(self):

        ask_deal_amount = self.__askDealAmount.getLastFactorValue()
        bid_deal_amount = self.__bidDealAmount.getLastFactorValue()
        ask_deal_amount_list = self.getIntermediate("AskDealAmountList")
        bid_deal_amount_list = self.getIntermediate("BidDealAmountList")

        if ask_deal_amount is not None:
            ask_deal_amount_list.append(np.nanmean(list(ask_deal_amount.values())))
        else:
            ask_deal_amount_list.append(0.)
        if bid_deal_amount is not None:
            bid_deal_amount_list.append(np.nanmean(list(bid_deal_amount.values())))
        else:
            bid_deal_amount_list.append(0.)

        if np.nanmean(bid_deal_amount_list[-self.__lag:]) > 1e-6:
            factorValue = np.nanmean(ask_deal_amount_list[-self.__lag:]) / np.nanmean(bid_deal_amount_list[-self.__lag:])
        elif np.nanmean(bid_deal_amount_list) > 1e-6:
            factorValue = np.nanmean(ask_deal_amount_list) / np.nanmean(bid_deal_amount_list)
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)
