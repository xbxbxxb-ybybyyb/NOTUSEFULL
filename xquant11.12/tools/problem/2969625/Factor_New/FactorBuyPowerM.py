import math
import numpy as np
from System.Factor import Factor


class FactorBuyPowerM(Factor):
    # 买入额占交易总额的比例
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
        BidAmountList = self.__orderEvaluate.getFactorValueList()[-200:]
        accBidAmountList = []
        for i in BidAmountList:
            accBidAmountList.append(i[0])
        accBidAmountList = np.array(accBidAmountList)
        medianValue = np.median(accBidAmountList)
        accBidAmount = self.__orderEvaluate.getLastFactorValue()[0]
        if accBidAmount == medianValue:
            new_list = accBidAmountList[accBidAmountList != medianValue]
            if new_list != []:
                accBidAmount = new_list[-1]
            else:
                accBidAmount = 0

        MAAmount = np.nanmean(self._getLastNTickData("Amount", self.__MAAmountLag))

        if accBidAmount < 0 or MAAmount <= 0 or len(BidAmountList) <= 10:
            factorValue = -3.5
        else:
            factorValue = math.log(accBidAmount / MAAmount + self.__eps)

        self._addFactorValue(factorValue)
