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
            bollMid.append(None)
        else:
            # 中轨
            lastMA = np.nanmean(priceArray)
            bollMid.append(lastMA)
            subBollMid = list(filter(lambda x: x is not None, bollMid))
            MAArray = np.array(subBollMid[-self.__bollLag:])

            # 标准差
            if np.nanmax(priceArray) - np.nanmin(priceArray) < 1e-6:
                MD = 0.
            else:
                MD = np.nanstd(priceArray - MAArray)

            # 上下轨
            bollUp = lastMA + self.__width * MD
            bollDown = lastMA - self.__width * MD

            # 相对位置
            if abs(bollUp - bollDown) < 1e-6:
                factorValue = 0.5
            else:
                factorValue = (lastMidPrice - bollDown) / (bollUp - bollDown)

        self._addFactorValue(factorValue)
