from System.Factor import Factor
import numpy as np


class FactorAskAmountPerTradeQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__askDealAmount = self._getFactor(
            {
                "ClassName": "AskDealAmount",
            }
        )
        self._addIntermediate("AskDealAmountList", [])
        self._addIntermediate("AskDealAmountAverageList", [])

    def calculate(self):

        ask_deal_amount = self.__askDealAmount.getLastFactorValue()
        ask_deal_amount_list = self.getIntermediate("AskDealAmountList")
        ask_deal_amount_average_list = self.getIntermediate("AskDealAmountAverageList")

        if ask_deal_amount is not None:
            ask_deal_amount_list.append(np.nanmean(list(ask_deal_amount.values())))
        else:
            ask_deal_amount_list.append(0.)

        ask_deal_amount_average_list.append(np.nanmean(ask_deal_amount_list[-self.__lag:]))

        factorValue = np.nansum(np.array(ask_deal_amount_average_list) < (ask_deal_amount_average_list[-1] - 1e-6)) / \
                      len(ask_deal_amount_average_list)

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)
