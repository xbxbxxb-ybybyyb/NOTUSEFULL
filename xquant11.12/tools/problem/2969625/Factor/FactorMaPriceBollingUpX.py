import numpy as np
from System.Factor import Factor


class FactorMaPriceBollingUpX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lltLag = self._getParameter("LLTLag")
        self.__window = self._getParameter("Window")

        self.__midPriceLLT = self._getFactor(
            {
                "ClassName": "LLTFilter",
                "Parameters": {
                    "Lag": self.__lltLag,
                    "FilterObj": "MidPrice"
                }
            }
        )
        self._addIntermediate("PriceMeanList", [])
        self._addIntermediate("PriceStdList", [])

    def calculate(self):
        midPriceList = self.__midPriceLLT.getFactorValueList()
        priceMean = np.nanmean(midPriceList[-self.__window:])
        priceStd = np.nanstd(midPriceList[-self.__window:]) if len(midPriceList) > 1 else 0.
        priceMeanList = self.getIntermediate("PriceMeanList")
        priceStdList = self.getIntermediate("PriceStdList")
        priceMeanList.append(priceMean)
        priceStdList.append(priceStd)

        if len(priceMeanList) < 10:
            factorValue = - 0.2
        else:
            priceMeanSlice, priceStdSlice = np.array(priceMeanList), np.array(priceStdList)
            bollingUp = np.array(midPriceList) - (priceMeanSlice + priceStdSlice)
            stdSum =  np.nansum(priceStdSlice)
            if stdSum > 1e-6:
                factorValue = - bollingUp[bollingUp > 1e-6].sum() / stdSum
            else:
                lastFactorValue = self.getLastFactorValue()
                if lastFactorValue is not None:
                    factorValue = lastFactorValue
                else:
                    factorValue = - 0.2

        self._addFactorValue(factorValue)





