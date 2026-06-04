import datetime as dt
import numpy as np
from System.Factor import Factor


class TagNSecBTBLong(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__n = self._getParameter("N")

        self.__ask1Price = self._getFactor(
            {
                "ClassName": "Ask1Price",
            }
        )

        self.__bid1Price = self._getFactor(
            {
                "ClassName": "Bid1Price",
            }
        )

        self._addIntermediate("UnfinishedStartIndex", 0)
        self._addIntermediate("BidPrice1List", [])

    def calculate(self):
        unfinishedStartIndex = self.getIntermediate("UnfinishedStartIndex")
        bidPrice1List = self.getIntermediate("BidPrice1List")
        timestampList = self._getAllTodayTickData("Timestamp")
        targetTimestampList = self._getAllTodayTickData("TargetTimestamp")
        thisTimestamp = timestampList[-1]

        # 此时涨停
        if self.__ask1Price.getLastFactorValue() < 1e-6:
            bidPrice1List.append(np.nan)
        # 此时跌停
        elif self.__bid1Price.getLastFactorValue() < 1e-6:
            bidPrice1List.append(self.__ask1Price.getLastFactorValue())
        else:
            bidPrice1List.append(self.__bid1Price.getLastFactorValue())

        for i in range(unfinishedStartIndex, len(timestampList)):
            if self.__getTimeDiff(targetTimestampList[i], thisTimestamp) >= self.__n:
                if not np.isnan(bidPrice1List[i]):
                    factorValue = bidPrice1List[-1] / bidPrice1List[i] - 1
                else:
                    factorValue = 0.

                self._addFactorValue(factorValue)
                unfinishedStartIndex += 1
            else:
                break

        self._setIntermediate("UnfinishedStartIndex", unfinishedStartIndex)

    def _onDayEnd(self):
        unfinishedStartIndex = self.getIntermediate("UnfinishedStartIndex")
        bidPrice1List = self.getIntermediate("BidPrice1List")
        timestampList = self._getAllTodayTickData("Timestamp")

        for i in range(unfinishedStartIndex, len(timestampList)):
            if not np.isnan(bidPrice1List[i]):
                factorValue = bidPrice1List[-1] / bidPrice1List[i] - 1
            else:
                factorValue = 0.

            self._addFactorValue(factorValue)

    @staticmethod
    def __getTimeDiff(time1, time2):
        hour1 = dt.datetime.fromtimestamp(time1).hour
        hour2 = dt.datetime.fromtimestamp(time2).hour

        if hour1 < 12 < hour2:
            return time2 - time1 - 5400
        else:
            return time2 - time1
