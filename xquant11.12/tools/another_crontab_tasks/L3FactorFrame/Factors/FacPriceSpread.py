

from L3FactorFrame.FactorBase import FactorBase
from L3FactorFrame.tools.DecimalUtil import isEqual, greaterThan, lessThan

class FacPriceSpread(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        self.__spread_ratio = config.get("spread_ratio", 1)

    def calculate(self):
        tickDataIndex = self.getPrevTick("SeqNo")
        # if isEqual(tickDataIndex, 4006509):
        #     print("debug")
        orderIndex = self.getPrevOrder("SeqNo")
        cancelIndex = self.getPrevCancel("SeqNo")

        orderBSFlag = self.getPrevOrder("BSFlag")
        cancelBSFlag = self.getPrevCancel("BSFlag")

        tickAskPriceList = self.getPrevNTick("AskPrice", 2)
        tickBidPriceList = self.getPrevNTick("BidPrice", 2)

        if len(tickAskPriceList) < 2:
            factorValue = 0.0
        else:
            factorValue = 0.0
            lastTickAskPrice, currentTickAskPrice = tickAskPriceList
            lastTickBidPrice, currentTickBidPrice = tickBidPriceList
            if ((0 not in currentTickAskPrice[:5]) and (0 not in currentTickBidPrice[:5])):
                lastTickAskP0, lastTickBidP0 = lastTickAskPrice[0], lastTickBidPrice[0]
                currentTickAskP0, currentTickBidP0 = currentTickAskPrice[0], currentTickBidPrice[0]

                if isEqual(tickDataIndex, orderIndex):
                    if (isEqual(orderBSFlag, 1) and greaterThan(currentTickBidP0, lastTickBidP0)):
                        currentTickBidP1 = currentTickBidPrice[1]
                        bidSpreadRatio = (currentTickBidP0 - currentTickBidP1 - 0.01) / currentTickBidP1 * 1000
                        if (bidSpreadRatio >= self.__spread_ratio):
                            factorValue = -bidSpreadRatio
                    elif (isEqual(orderBSFlag, 2) and lessThan(currentTickAskP0, lastTickAskP0)):
                        currentTickAskP1 = currentTickAskPrice[1]
                        askSpreadRatio = (currentTickAskP1 - currentTickAskP0 - 0.01) / currentTickAskP1 * 1000
                        if (askSpreadRatio >= self.__spread_ratio):
                            factorValue = askSpreadRatio
                elif isEqual(tickDataIndex, cancelIndex):
                    if (isEqual(cancelBSFlag, 1) and greaterThan(currentTickBidP0, lastTickBidP0)):
                        currentTickBidP1 = currentTickBidPrice[1]
                        bidSpreadRatio = (currentTickBidP0 - currentTickBidP1 - 0.01) / currentTickBidP1 * 1000
                        if (bidSpreadRatio >= self.__spread_ratio):
                            factorValue = -bidSpreadRatio
                    elif (isEqual(cancelBSFlag, 2) and lessThan(currentTickAskP0, lastTickAskP0)):
                        currentTickAskP1 = currentTickAskPrice[1]
                        askSpreadRatio = (currentTickAskP1 - currentTickAskP0 - 0.01) / currentTickAskP1 * 1000
                        if (askSpreadRatio >= self.__spread_ratio):
                            factorValue = askSpreadRatio

        self.addFactorValue(factorValue)
