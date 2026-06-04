import numpy as np
from System.Factor import Factor


class FactorBoll(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__bollLag = self._getParameter("BollLag")
        self.__width = self._getParameter("Width")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

        self._addIntermediate("BollMid", [])

    def calculate(self):
        bollMid = self.getIntermediate("BollMid")

        midPriceList = self.__midPrice.getFactorValueList()
        lastMidPrice = self.__midPrice.getLastFactorValue()

        priceArray = np.array(midPriceList[-self.__bollLag:])
        isNotValid = (priceArray <= 0.01).any()

        if isNotValid:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is None:
                factorValue = 0
            else:
                factorValue = lastFactorValue
        else:
            # 中轨
            lastMA = np.mean(priceArray)
            bollMid.append(lastMA)
            MAArray = np.array(bollMid[-self.__bollLag:])

            # 标准差
            MD = np.std(priceArray - MAArray)

            # 上下轨
            bollUp = lastMA + self.__width * MD
            bollDown = lastMA - self.__width * MD

            # 相对位置
            if bollUp == bollDown:
                factorValue = 0.5
            else:
                factorValue = (lastMidPrice - bollDown) / (bollUp - bollDown)

        self._addFactorValue(factorValue)
