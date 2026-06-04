from System.Factor import Factor
import numpy as np


class INFLastPrice(Factor):

    def calculate(self):

        factorValueList = self.getFactorValueList()

        if len(factorValueList) == 0:
            factorValue = 1000.
        else:
            lastPriceG = self._getAllTodayTickDataForStockGroup("LastPrice")
            returnG = []
            for each in lastPriceG:
                if len(each) > 0:
                    firstPrice = np.nan
                    for firstPrice in each:
                        if not np.isnan(firstPrice):
                            break
                    returnG.append(each[-1] / firstPrice - 1)
                else:
                    returnG.append(np.nan)

            retSum = np.nansum(np.multiply(returnG, self.__get_weights()))

            factorValue = factorValueList[0] * (1. + retSum)

        self._addFactorValue(factorValue)

    def __get_weights(self):
        ffs = self._getLastNHistoricalDailyDataForStockGroup("FreeFloatShares", 1, isStacked=True)[0]
        closep = self._getLastNHistoricalDailyDataForStockGroup("ClosePrice", 1, isStacked=True)[0]
        mktcap = ffs * closep
        w = mktcap / np.nansum(mktcap)
        return w
