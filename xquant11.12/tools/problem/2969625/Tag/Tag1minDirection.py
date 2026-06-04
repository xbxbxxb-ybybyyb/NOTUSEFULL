import datetime as dt
import numpy as np
from System.Factor import Factor


class Tag1minDirection(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

        self._addIntermediate("UnfinishedStartIndex", 0)
        self._addIntermediate("Timestamp", [])

    def calculate(self):
        unfinishedStartIndex = self.getIntermediate("UnfinishedStartIndex")

        timestampList = self.getIntermediate("Timestamp")
        thisTimestamp = self._getLastTickData("Timestamp")
        timestampList.append(thisTimestamp)

        midPriceList = self.__midPrice.getFactorValueList()

        for i in range(unfinishedStartIndex, len(timestampList)):
            if self.__getTimeDiff(timestampList[i], thisTimestamp) >= 66:
                midPriceListTmp = [midPriceList[-1 - j] for j in range(min(5, len(timestampList)))
                                   if timestampList[-1 - j] > timestampList[i]]
                if len(midPriceListTmp) > 0:
                    factorValue = np.sign(np.mean(midPriceListTmp) - midPriceList[i])
                else:
                    factorValue = 0
                self._addFactorValue(factorValue)
                unfinishedStartIndex += 1

        self._setIntermediate("UnfinishedStartIndex", unfinishedStartIndex)

    def _onDayEnd(self):
        unfinishedStartIndex = self.getIntermediate("UnfinishedStartIndex")
        timestampList = self.getIntermediate("Timestamp")
        midPriceList = self.__midPrice.getFactorValueList()

        for i in range(unfinishedStartIndex, len(timestampList)):
            midPriceListTmp = [midPriceList[-1 - j] for j in range(min(5, len(timestampList)))
                               if timestampList[-1 - j] > timestampList[i]]
            if len(midPriceListTmp) > 0:
                factorValue = np.sign(np.mean(midPriceListTmp) - midPriceList[i])
            else:
                factorValue = 0
            self._addFactorValue(factorValue)

    @staticmethod
    def __getTimeDiff(time1, time2):
        hour1 = dt.datetime.fromtimestamp(time1).hour
        hour2 = dt.datetime.fromtimestamp(time2).hour

        if hour1 < 12 < hour2:
            return time2 - time1 - 5400
        else:
            return time2 - time1
