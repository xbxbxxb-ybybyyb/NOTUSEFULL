import numpy as np
from System.Factor import Factor
# Log:
# 2020/12/01对原Easy因子不取第一个值问题进行修正


class FactorTickSellAmountRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lookBack = self._getParameter("LookBack")

        self.__orderEvaluate2 = self._getFactor(
            {
                "ClassName": "OrderEvaluate2"
            }
        )

    def calculate(self):
        buyAmount, sellAmount = self.__orderEvaluate2.getLastFactorValue()
        historyAmountArray = self._getAllHistoricalTickData("Amount")
        amountArray = self._getAllTodayTickData("Amount")
        allAmountArray = np.append(historyAmountArray, amountArray)
        size = min(historyAmountArray.shape[0], self.__lookBack)
        amountSum = np.nansum(allAmountArray[-size:])

        if sellAmount < 0 or amountSum <= 0:
            value = 0.0
        else:
            value = float(sellAmount * size) / amountSum

        self._addFactorValue(value)