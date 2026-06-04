from System.Factor import Factor
import numpy as np


class Factor40BidAmtPerTradeStd(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")

        self.__bidAmtPerTrade = self._getFactor(
            {
                "ClassName": "BidAmtPerTrade"
            }
        )
        self._addIntermediate("AmountRatioList", [])

    def calculate(self):
        amountRatioList = self.getIntermediate("AmountRatioList")
        value = self.__bidAmtPerTrade.getLastFactorValue()
        amt = self._getLastTickData('Amount')
        if amt == 0:
            amountRatioList.append(0)
        else:
            amountRatioList.append(value / amt)
        std_value = np.nanstd(np.array(amountRatioList[-self.__window:])) * 1e2
        if np.isnan(std_value):
            std_value = 0

        self._addFactorValue(std_value)











