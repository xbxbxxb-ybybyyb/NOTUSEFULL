from System.TradingDay import getTradingDay
from SystemRay.RayTaskMeta import RayTaskMeta


class TaskSplitter:
    def __init__(self, stockSet, sDate, eDate, dayUnit, stockGroupNum, configAnalyzer):
        self.__stockSetToBeCalculated = stockSet
        self.__sDate = sDate
        self.__eDate = eDate
        self.__dayUnit = dayUnit
        self.__stockGroupNum = stockGroupNum
        self.__configAnalyzer = configAnalyzer

        self.__taskList = []

    def splitTask(self):
        tradingDayList = getTradingDay(self.__sDate, self.__eDate)
        startDateList = tradingDayList[::self.__dayUnit]
        endDateList = tradingDayList[self.__dayUnit - 1:-1:self.__dayUnit] + [tradingDayList[-1]]

        stockNum = len(self.__stockSetToBeCalculated)
        stockGroupNum = min(self.__stockGroupNum, stockNum)
        stockNumPerGroup, residual = divmod(stockNum, stockGroupNum)
        stockNumPerGroupList = [stockNumPerGroup] * (stockGroupNum - residual) + [stockNumPerGroup + 1] * residual
        startIndexList = [sum(stockNumPerGroupList[:i]) for i in range(len(stockNumPerGroupList))]
        endIndexList = startIndexList[1:] + [stockNum]

        stockListTS = list(self.__stockSetToBeCalculated)
        stockSetTSList = [set(stockListTS[startIndex:endIndex])
                          for startIndex, endIndex in zip(startIndexList, endIndexList)]

        for sDate, eDate in zip(startDateList, endDateList):
            self.__taskList.append(RayTaskMeta(sDate, eDate, stockSetTSList))

    def getTaskList(self):
        return self.__taskList
