from System.Factor import Factor
import numpy as np


class INFLastPriceEw(Factor):

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

            retSum = np.nanmean(returnG)
            retSum = 0. if np.isnan(retSum) else retSum

            factorValue = factorValueList[0] * (1. + retSum)

        self._addFactorValue(factorValue)
