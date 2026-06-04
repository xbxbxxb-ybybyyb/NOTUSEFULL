import datetime as dt
import numpy as np
from System.Factor import Factor


class Tag10minShortMin(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

        self._addIntermediate("UnfinishedStartIndex", 0)
        self._addIntermediate("Timestamp", [])
        self._addIntermediate("AskPrice1", [])
        self._addIntermediate("BidPrice1", [])

    def calculate(self):
        unfinishedStartIndex = self.getIntermediate("UnfinishedStartIndex")

        timestampList = self.getIntermediate("Timestamp")
        thisTimestamp = self._getLastTickData("Timestamp")
        timestampList.append(thisTimestamp)

        askPrice1List = self.getIntermediate("AskPrice1")
        askPrice1 = self._getLastTickData("AskPrice")[0]
        if askPrice1 > 0:
            askPrice1List.append(askPrice1)
        else:
            askPrice1List.append(self.__midPrice.getLastFactorValue())

        bidPrice1List = self.getIntermediate("BidPrice1")
        bidPrice1 = self._getLastTickData("BidPrice")[0]
        bidPrice1List.append(bidPrice1)

        for i in range(unfinishedStartIndex, len(timestampList)):
            if self.__getTimeDiff(timestampList[i], thisTimestamp) >= 600:
                bidPriceTmp = bidPrice1List[i]
                if bidPriceTmp <= 0:
                    factorValue = 0
                else:
                    returnSpeedListTmp = [askPrice1List[j] / bidPriceTmp - 1 for j in range(i + 1, len(timestampList))]
                    if len(returnSpeedListTmp) > 0:
                        factorValue = np.min(returnSpeedListTmp)
                    else:
                        factorValue = 0
                self._addFactorValue(factorValue)
                unfinishedStartIndex += 1

        self._setIntermediate("UnfinishedStartIndex", unfinishedStartIndex)

    def _onDayEnd(self):
        unfinishedStartIndex = self.getIntermediate("UnfinishedStartIndex")
        timestampList = self.getIntermediate("Timestamp")
        askPrice1List = self.getIntermediate("AskPrice1")
        bidPrice1List = self.getIntermediate("BidPrice1")

        for i in range(unfinishedStartIndex, len(timestampList)):
            bidPriceTmp = bidPrice1List[i]
            if bidPriceTmp <= 0:
                factorValue = 0
            else:
                returnSpeedListTmp = [askPrice1List[j] / bidPriceTmp - 1 for j in range(i + 1, len(timestampList))]
                if len(returnSpeedListTmp) > 0:
                    factorValue = np.min(returnSpeedListTmp)
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
