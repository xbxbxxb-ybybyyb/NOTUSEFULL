"""
@author: 006688

当前波段序号记为0，依据界点，往前的波段依次计为第1、2、...波，指定波段的序号，给出对应波段的涨跌幅
波段序号参数为list形式，可以指定多个波段，例如[1, 2, 4, 5]
"""

from System.Factor import Factor


class LastNChange(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraLastN = para['paraLastN']
        self.__paraFastLag = para['paraFastLag']
        self.__paraSlowLag = para['paraSlowLag']

        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.__extremePoint = self.getFactorData({"name": "extremePoint", "className": "ExtremePoint",
                                                  "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                  "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                                                  "paraFastLag": self.__paraFastLag, "paraSlowLag": self.__paraSlowLag})
        self.__extremePointInfo = self.__extremePoint.getExtremePointInfo()
        factorManagement.registerFactor(self, para)

    def calculate(self):
        factorValue = [0] * len(self.__paraLastN)
        if self.__extremePoint.getUpdateStatus() == 1:
            for i in range(self.__paraLastN.__len__()):
                if self.__paraLastN[i] < len(self.__extremePointInfo):
                    factorValue[i] = self.__extremePointInfo[-self.__paraLastN[i]][3]  # 直接从界点信息中取
            self.addData(factorValue, self.__data.getLastTimeStamp())
        else:
            if len(self.getContent()) == 0:
                self.addData(factorValue, self.__data.getLastTimeStamp())
            else:
                self.addData(self.getLastContent(), self.__data.getLastTimeStamp())


