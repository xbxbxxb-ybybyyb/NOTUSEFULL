from System.Factor import Factor
import numpy as np


class FactorAskActiveAmountRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__askDealAmount = self._getFactor(
            {
                "ClassName": "AskDealAmount",
            }
        )
        self.__activeAskInfo = self._getFactor(
            {
                "ClassName": "ActiveAskInfoByOrder",
            }
        )

        self._addIntermediate("AskActiveDealAmountList", [])
        self._addIntermediate("AskDealAmountList", [])

    def calculate(self):

        ask_deal_amount = self.__askDealAmount.getLastFactorValue()
        ask_active_info = self.__activeAskInfo.getLastFactorValue()
        ask_deal_amount_list = self.getIntermediate("AskDealAmountList")
        ask_active_deal_amount_list = self.getIntermediate("AskActiveDealAmountList")

        if ask_deal_amount is not None:
            ask_deal_amount_list.append(np.nanmean(list(ask_deal_amount.values())))
        else:
            ask_deal_amount_list.append(0.)

        if ask_active_info is not None:
            ask_active_deal_amount_list.append(np.nanmean([each[0] for each in ask_active_info.values()]))
        else:
            ask_active_deal_amount_list.append(0.)

        if np.nanmean(ask_deal_amount_list[-self.__lag:]) > 1e-6:
            factorValue = np.nanmean(ask_active_deal_amount_list[-self.__lag:]) / np.nanmean(ask_deal_amount_list[-self.__lag:])
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)
