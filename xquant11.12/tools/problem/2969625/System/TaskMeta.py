class TaskMeta:
    def __init__(self, startDate, endDate, stockSetTS):
        self.__startDate = startDate
        self.__endDate = endDate
        self.__stockSetTS = stockSetTS

    def getStartDate(self):
        return self.__startDate

    def getEndDate(self):
        return self.__endDate

    def getStockSetTS(self):
        return self.__stockSetTS
