import datetime as dt
import numpy as np
from System.Factor import Factor


class Tag1minShortBothSides(Factor):
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

        if bidPrice1 > 0:
            bidPrice1List.append(bidPrice1)
        else:
            bidPrice1List.append(np.nan)

        i = unfinishedStartIndex
        while self.__getTimeDiff(timestampList[i], thisTimestamp) >= 62.5:
            askPrice1ListTmp = [askPrice1List[-1 - j] for j, tsp in enumerate(timestampList[-6:][::-1])
                                if self.__getTimeDiff(tsp, thisTimestamp) < 3]
            bidPrice1ListTmp = [bidPrice1List[i + j] for j, tsp in enumerate(timestampList[i: (i+6)])
                                if self.__getTimeDiff(tsp, timestampList[i]) < 3]
            if len(askPrice1ListTmp) > 0 and np.any(~np.isnan(bidPrice1ListTmp)):
                factorValue = np.mean(askPrice1ListTmp) / np.nanmean(bidPrice1ListTmp) - 1
            else:
                factorValue = 0
            self._addFactorValue(factorValue)
            unfinishedStartIndex += 1
            i = unfinishedStartIndex

        self._setIntermediate("UnfinishedStartIndex", unfinishedStartIndex)

    def _onDayEnd(self):
        unfinishedStartIndex = self.getIntermediate("UnfinishedStartIndex")
        timestampList = self.getIntermediate("Timestamp")
        askPrice1List = self.getIntermediate("AskPrice1")
        bidPrice1List = self.getIntermediate("BidPrice1")
        lastTimestamp = timestampList[-1]

        for i in range(unfinishedStartIndex, len(timestampList)):
            askPrice1ListTmp = [askPrice1List[-1 - j] for j, tsp in enumerate(timestampList[-6:][::-1])
                                if self.__getTimeDiff(tsp, lastTimestamp) < 3 and tsp > timestampList[i]]
            timestampListTmp = [tsp for tsp in timestampList[-6:][::-1]
                                if self.__getTimeDiff(tsp, lastTimestamp) < 3 and tsp > timestampList[i]]
            if len(timestampListTmp) > 0:
                bidPrice1ListTmp = [bidPrice1List[i + j] for j, tsp in enumerate(timestampList[i: (i+6)])
                                    if self.__getTimeDiff(tsp, timestampList[i]) < 3 and tsp < timestampListTmp[-1]]
            else:
                bidPrice1ListTmp = [bidPrice1List[i]]  # 最后一个
            if len(askPrice1ListTmp) > 0 and np.any(~np.isnan(bidPrice1ListTmp)):
                factorValue = np.mean(askPrice1ListTmp) / np.nanmean(bidPrice1ListTmp) - 1
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
