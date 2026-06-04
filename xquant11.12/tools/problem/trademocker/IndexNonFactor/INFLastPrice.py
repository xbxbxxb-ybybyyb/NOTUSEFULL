from System.Factor import Factor
import numpy as np


class INFLastPrice(Factor):

    def calculate(self):

        factorValueList = self.getFactorValueList()

        if len(factorValueList) == 0:
            factorValue = 1000.
        else:
            lastPriceG = self._getAllTodayTickDataForStockGroup("LastPrice")
            returnGList = []
            for each in lastPriceG:
                if len(each) == 0:
                    returnGList.append(np.nan)
                else:
                    for firstPrice in each:
                        if ~np.isnan(firstPrice):
                            break
                    returnGList.append(each[-1] / firstPrice - 1.)

            returnG = np.array(returnGList)

            factorValue = factorValueList[0] * ( 1. + np.nansum(returnG * self.__get_weights()) )

        self._addFactorValue(factorValue)

    def __get_weights(self):
        ffs = self._getLastNHistoricalDailyDataForStockGroup("FreeFloatShares", 1, isStacked=True)[0]
        closep = self._getLastNHistoricalDailyDataForStockGroup("ClosePrice", 1, isStacked=True)[0]
        mktcap = ffs * closep
        w = mktcap / np.nansum(mktcap)
        return w
