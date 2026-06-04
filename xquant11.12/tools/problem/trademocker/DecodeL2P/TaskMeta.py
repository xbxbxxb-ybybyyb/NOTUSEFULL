class TaskMeta:
    def __init__(self,
                 l2pLibrary,
                 stock,
                 cbond,
                 date,
                 save,
                 saveLibrary):

        self.__l2pLibrary = l2pLibrary
        self.__stock = stock
        self.__cbond = cbond
        self.__date = date
        self.__save = save
        self.__saveLibrary = saveLibrary

    def getL2PLibrary(self):
        return self.__l2pLibrary

    def getStock(self):
        return self.__stock

    def getCBond(self):
        return self.__cbond

    def getDate(self):
        return self.__date

    def getSave(self):
        return self.__save

    def getSaveLibrary(self):
        return self.__saveLibrary


