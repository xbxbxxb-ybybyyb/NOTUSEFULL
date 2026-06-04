from System.Factor import Factor
import numpy as np


class INFLastPriceEw(Factor):

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

            factorValue = factorValueList[0] * (1. + np.nanmean(returnG))

        self._addFactorValue(factorValue)
