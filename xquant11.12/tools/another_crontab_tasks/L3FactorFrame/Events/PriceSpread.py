

from L3FactorFrame.FactorBase import FactorBase
from L3FactorFrame.tools.DecimalUtil import isEqual, greaterThan, lessThan

class PriceSpread(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        # 本方一档价差，超过千一
        self.__spread_ratio = config.get("spread_ratio", 0.5)

    def calculate(self):
        tickDataIndex = self.getPrevTick("SeqNo")
        if isEqual(tickDataIndex, 3208626):
            print("debug")
        orderIndex = self.getPrevOrder("SeqNo")
        cancelIndex = self.getPrevCancel("SeqNo")

        orderBSFlag = self.getPrevOrder("BSFlag")
        cancelBSFlag = self.getPrevCancel("BSFlag")

        tickAskPriceList = self.getPrevNTick("AskPrice", 2)
        tickBidPriceList = self.getPrevNTick("BidPrice", 2)

        if len(tickAskPriceList) < 2:
            factorValue = 0
        else:
            factorValue = 0
            lastTickAskPrice, currentTickAskPrice = tickAskPriceList
            lastTickBidPrice, currentTickBidPrice = tickBidPriceList
            if True:#((0 not in currentTickAskPrice[:5]) and (0 not in currentTickBidPrice[:5])):
                lastTickAskP0, lastTickBidP0 = lastTickAskPrice[0], lastTickBidPrice[0]
                currentTickAskP0, currentTickBidP0 = currentTickAskPrice[0], currentTickBidPrice[0]

                if isEqual(tickDataIndex, orderIndex):
                    if (isEqual(orderBSFlag, 1) and greaterThan(currentTickBidP0, lastTickBidP0)):
                        currentTickBidP1 = currentTickBidPrice[1]
                        bidSpreadRatio = (currentTickBidP0 - currentTickBidP1 - 0.01) / currentTickBidP1 * 1000
                        if (bidSpreadRatio >= self.__spread_ratio):
                            factorValue = -1
                    elif (isEqual(orderBSFlag, 2) and lessThan(currentTickAskP0, lastTickAskP0)):
                        currentTickAskP1 = currentTickAskPrice[1]
                        askSpreadRatio = (currentTickAskP1 - currentTickAskP0 - 0.01) / currentTickAskP1 * 1000
                        if (askSpreadRatio >= self.__spread_ratio):
                            factorValue = 1
                elif isEqual(tickDataIndex, cancelIndex):
                    if (isEqual(cancelBSFlag, 1) and greaterThan(currentTickBidP0, lastTickBidP0)):
                        currentTickBidP1 = currentTickBidPrice[1]
                        bidSpreadRatio = (currentTickBidP0 - currentTickBidP1 - 0.01) / currentTickBidP1 * 1000
                        if (bidSpreadRatio >= self.__spread_ratio):
                            factorValue = -1
                    elif (isEqual(cancelBSFlag, 2) and lessThan(currentTickAskP0, lastTickAskP0)):
                        currentTickAskP1 = currentTickAskPrice[1]
                        askSpreadRatio = (currentTickAskP1 - currentTickAskP0 - 0.01) / currentTickAskP1 * 1000
                        if (askSpreadRatio >= self.__spread_ratio):
                            factorValue = 1

        self.addFactorValue(factorValue)
