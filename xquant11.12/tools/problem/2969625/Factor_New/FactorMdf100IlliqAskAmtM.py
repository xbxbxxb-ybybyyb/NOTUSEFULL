from System.Factor import Factor
import numpy as np
from copy import deepcopy


class FactorMdf100IlliqAskAmtM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__adjLevel = 2
        self.__window = self._getParameter("Window")
        self.__shortWindow = min(int(self.__window / 20), 20)

        self.__askAmtPerTrade = self._getFactor(
            {
                "ClassName": "MdfAskAmtPerTrade",
                "Parameters": {
                    "Coef": 10,
                }
            }
        )

        self._addIntermediate("PriceList", [])

    def calculate(self):
        askP = self._getLastTickData("AskPrice")
        askV = self._getLastTickData("AskVolume")
        maxP = self._getLastTickData("MaxPrice")

        askVSum = askV[:self.__adjLevel].sum()
        price = (askP[:self.__adjLevel] * askV[:self.__adjLevel]).sum() / askVSum if askVSum > 0 else maxP

        priceList = self.getIntermediate("PriceList")
        if price < 1e-4:
            priceList.append(priceList[-1])
        else:
            priceList.append(price)

        pct = np.log(np.divide(priceList[1:], priceList[:-1])) * 100
        cum_pct = np.nansum(pct)

        askAmtPerTradeList = self.__askAmtPerTrade.getFactorValueList()
        long_amt = np.nansum(np.array(askAmtPerTradeList[-self.__window:]))
        if long_amt <= 1e-6:
            res = 0
        else:
            res = (cum_pct / long_amt) * np.nansum(np.array(askAmtPerTradeList[-self.__shortWindow:]))
        if (len(pct) == 0) or (len(askAmtPerTradeList) == 0):
            res = 0
        res  = res * (-1)
        self._addFactorValue(res)
