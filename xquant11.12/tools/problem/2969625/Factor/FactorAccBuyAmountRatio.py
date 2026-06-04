import numpy as np
from System.Factor import Factor


class FactorAccBuyAmountRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__maLag = self._getParameter("MALag")
        self.__orderEvaluateLag = self._getParameter("OrderEvaluateLag")

        self.__orderEvaluate2 = self._getFactor(
            {
                "ClassName": "OrderEvaluate2"
            }
        )

        self._addIntermediate("emaBuyAmount", [])

    def calculate(self):
        buyAmount, sellAmount = self.__orderEvaluate2.getLastFactorValue()
        emaBuyAmountList = self.getIntermediate("emaBuyAmount")
        if len(emaBuyAmountList) > 1:
            buyAmount = self._EMA_calculate(buyAmount, emaBuyAmountList, self.__orderEvaluateLag)
        emaBuyAmountList.append(buyAmount)

        historyAmountArray = self._getAllHistoricalTickData("Amount")
        amountArray = self._getAllTodayTickData("Amount")[1:]  # in consistent with java code, why so ?
        allVolumeArray = np.append(historyAmountArray, amountArray)
        amountSum = np.nansum(allVolumeArray[-(self.__maLag + 1):-1])

        if buyAmount < 0 or amountSum <= 0:
            value = 0.0
        else:
            value = float(buyAmount * self.__maLag) / amountSum

        self._addFactorValue(value)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / min(size, n + 1)  # inconsistent with Java, not size + 1, why so ?
            return EMAList[-1] + para * (value - EMAList[-1])


