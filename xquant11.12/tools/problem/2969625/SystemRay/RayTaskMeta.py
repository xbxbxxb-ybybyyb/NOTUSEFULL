class RayTaskMeta:
    def __init__(self, startDate, endDate, stockSetTSList):
        self.__startDate = startDate
        self.__endDate = endDate
        self.__stockSetTSList = stockSetTSList

    def getStartDate(self):
        return self.__startDate

    def getEndDate(self):
        return self.__endDate

    def getStockSetTSList(self):
        return self.__stockSetTSList
