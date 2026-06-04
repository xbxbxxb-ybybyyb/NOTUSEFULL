import datetime as dt
import numpy as np
from System.Factor import Factor


class Tag10minLongTwap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self._addIntermediate("UnfinishedMinuteStartIndex", 0)
        self._addIntermediate("UnfinishedTickStartIndex", 0)
        self._addIntermediate("LastMinuteTimestamp", 0)

        self.__ask1Price = self._getFactor(
            {
                "ClassName": "Ask1Price",
                "BType": "Tick",
            }
        )

        self.__bid1Price = self._getFactor(
            {
                "ClassName": "Bid1Price",
                "BType": "Tick",
            }
        )

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice",
                "BType": "Tick",
            }
        )

    def calculate(self):

        unfinishedMinuteStartIndex = self.getIntermediate("UnfinishedMinuteStartIndex")

        # Minute
        thisMinuteTimestamp = self._getLastMinuteData("Timestamp")
        minuteTimestampList = self._getAllTodayMinuteData("Timestamp")

        # Tick
        midPriceList = self.__midPrice.getFactorValueList()
        askPrice1List = [each if each > 0 else np.nan for each in self.__ask1Price.getFactorValueList()]
        bidPrice1List = [each if each > 0 else midPriceList[i] for i, each in enumerate(self.__bid1Price.getFactorValueList())]

        # 标签计算
        for i in range(unfinishedMinuteStartIndex, len(minuteTimestampList)):

            if self.__getTimeDiff(minuteTimestampList[i], thisMinuteTimestamp) > 660 - 0.5:

                bidPrice1ListTmp = self.__collectLastNMinPrice(2, bidPrice1List, thisMinuteTimestamp)
                unfinishedTickStartIndex = self.__updateUnfinishedTickStartIndex()
                askPrice1ListTmp = self.__collectNextNMinPrice(2, askPrice1List, unfinishedTickStartIndex)

                if len(bidPrice1ListTmp) > 0 and np.any(~np.isnan(askPrice1ListTmp)):
                    factorValue = np.mean(bidPrice1ListTmp) / np.nanmean(askPrice1ListTmp) - 1
                else:
                    factorValue = 0.
                self._addFactorValue(factorValue)

                unfinishedMinuteStartIndex += 1
                self._setIntermediate("UnfinishedMinuteStartIndex", unfinishedMinuteStartIndex)

            else:
                break

        self._setIntermediate("LastMinuteTimestamp", thisMinuteTimestamp)

    def _onDayEnd(self):

        unfinishedMinuteStartIndex = self.getIntermediate("UnfinishedMinuteStartIndex")

        minuteTimestampList = self._getAllTodayMinuteData("Timestamp")
        timestampList = self._getAllTodayTickData("Timestamp")
        midPriceList = self.__midPrice.getFactorValueList()
        askPrice1List = [each if each > 0 else np.nan for each in self.__ask1Price.getFactorValueList()]
        bidPrice1List = [each if each > 0 else midPriceList[i] for i, each in enumerate(self.__bid1Price.getFactorValueList())]

        for i in range(unfinishedMinuteStartIndex, len(minuteTimestampList)):

            if self.__getTimeDiff(minuteTimestampList[unfinishedMinuteStartIndex], minuteTimestampList[-1]) > 4 * 60 + 0.5:

                bidPrice1ListTmp = self.__collectLastNMinPrice(2, bidPrice1List, minuteTimestampList[-1])
                unfinishedTickStartIndex = self.__updateUnfinishedTickStartIndex()
                askPrice1ListTmp = self.__collectNextNMinPrice(2, askPrice1List, unfinishedTickStartIndex)

            elif self.__getTimeDiff(minuteTimestampList[unfinishedMinuteStartIndex], minuteTimestampList[-1]) > 0:

                unfinishedTickStartIndex = self.__updateUnfinishedTickStartIndex()
                leftn = len(timestampList) - unfinishedTickStartIndex
                askPrice1ListTmp = askPrice1List[unfinishedTickStartIndex: (unfinishedTickStartIndex + leftn // 2)]
                bidPrice1ListTmp = bidPrice1List[(unfinishedTickStartIndex + leftn // 2):]

            else:  # 最后一个
                askPrice1ListTmp = []
                bidPrice1ListTmp = []

            if len(bidPrice1ListTmp) > 0 and np.any(~np.isnan(askPrice1ListTmp)):
                factorValue = np.mean(bidPrice1ListTmp) / np.nanmean(askPrice1ListTmp) - 1
            else:
                factorValue = 0.
            self._addFactorValue(factorValue)

            unfinishedMinuteStartIndex += 1
            self._setIntermediate("UnfinishedMinuteStartIndex", unfinishedMinuteStartIndex)

    @staticmethod
    def __getTimeDiff(time1, time2):
        hour1 = dt.datetime.fromtimestamp(time1).hour
        hour2 = dt.datetime.fromtimestamp(time2).hour

        if hour1 < 12 < hour2:
            return time2 - time1 - 5400
        else:
            return time2 - time1

    def __collectLastNMinPrice(self, n, priceList, thisMinuteTimestamp):
        timestampList = self._getAllTodayTickData("Timestamp")
        PriceListTmp = []
        for j, timestamp in enumerate(timestampList[::-1]):
            if 0 < self.__getTimeDiff(timestamp, thisMinuteTimestamp) < n * 60 + 0.5:
                PriceListTmp.append(priceList[::-1][j])
            else:
                break
        return PriceListTmp

    def __updateUnfinishedTickStartIndex(self):
        unfinishedMinuteStartIndex = self.getIntermediate("UnfinishedMinuteStartIndex")
        unfinishedTickStartIndex = self.getIntermediate("UnfinishedTickStartIndex")
        timestampList = self._getAllTodayTickData("Timestamp")
        minuteTimestampList = self._getAllTodayMinuteData("Timestamp")

        unfinishedMinuteTimestamp = minuteTimestampList[unfinishedMinuteStartIndex]
        if (len(timestampList) == 0) or (timestampList[-1] < unfinishedMinuteTimestamp):  # 对应长时间缺Tick的情形
            unfinishedTickStartIndex = int(max(len(timestampList) - 1, 0))
        else:
            while timestampList[unfinishedTickStartIndex] < unfinishedMinuteTimestamp:
                unfinishedTickStartIndex += 1
        self._setIntermediate("UnfinishedTickStartIndex", unfinishedTickStartIndex)

        return unfinishedTickStartIndex

    def __collectNextNMinPrice(self, n, priceList, unfinishedTickStartIndex):
        unfinishedMinuteStartIndex = self.getIntermediate("UnfinishedMinuteStartIndex")
        minuteTimestampList = self._getAllTodayMinuteData("Timestamp")
        timestampList = self._getAllTodayTickData("Timestamp")
        unfinishedMinuteTimestamp = minuteTimestampList[unfinishedMinuteStartIndex]

        PriceListTmp = []
        for j in range(unfinishedTickStartIndex, len(timestampList)):
            if -0.5 < self.__getTimeDiff(unfinishedMinuteTimestamp, timestampList[j]) < 60 * n:
                PriceListTmp.append(priceList[j])
            else:
                break
        return PriceListTmp

