import math
import numpy as np
from System.Factor import Factor


class FactorSellPowerM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__MAAmountLag = self._getParameter("MAAmountLag")
        self.__eps = 1e-5

        self.__orderEvaluate = self._getFactor(
            {
                "ClassName": "OrderEvaluate2",
            }
        )

    def calculate(self):
        AskAmountList = self.__orderEvaluate.getFactorValueList()[-200:]
        accAskAmountList = []
        for i in AskAmountList:
            accAskAmountList.append(i[1])
        accAskAmountList = np.array(accAskAmountList)
        medianValue = np.median(accAskAmountList)
        accAskAmount = self.__orderEvaluate.getLastFactorValue()[1]
        if accAskAmount == medianValue:
            new_list = accAskAmountList[accAskAmountList != medianValue]
            if new_list != []:
                accAskAmount = new_list[-1]
            else:
                accAskAmount = -1

        MAAmount = np.nanmean(self._getLastNTickData("Amount", self.__MAAmountLag))

        if accAskAmount < 0 or MAAmount <= 0 or len(AskAmountList) <= 10:
            factorValue = 3.5
        else:
            factorValue = -math.log(accAskAmount / MAAmount + self.__eps)

        self._addFactorValue(factorValue)
