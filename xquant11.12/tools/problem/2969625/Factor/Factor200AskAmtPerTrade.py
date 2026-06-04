from System.Factor import Factor
import numpy as np


class Factor200AskAmtPerTrade(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")

        self.__askAmtPerTrade = self._getFactor(
            {
                "ClassName": "AskAmtPerTrade"
            }
        )
        self._addIntermediate("AmountRatioList", [])

    def calculate(self):
        amountRatioList = self.getIntermediate("AmountRatioList")
        non_value = self.__askAmtPerTrade.getLastFactorValue()
        amt = self._getLastTickData('Amount')
        if amt == 0:
            value = 0
        else:
            value = non_value / amt
        emw_value = self.ema(value, amountRatioList, self.__window)
        amountRatioList.append(emw_value)
        emw_value = emw_value * 1e2
        if np.isnan(emw_value):
            emw_value = 0

        self._addFactorValue(emw_value)

    def ema(self, input_value, ema_list, length):
        if len(ema_list) == 0:
            return input_value
        elif len(ema_list) < length:
            para = 2.0 / (len(ema_list) + 1)
            value = ema_list[-1] + para * (input_value - ema_list[-1])
            return value
        elif len(ema_list) >= length:
            para = 2.0 / (length + 1)
            value = ema_list[-1] + para * (input_value - ema_list[-1])
            return value

