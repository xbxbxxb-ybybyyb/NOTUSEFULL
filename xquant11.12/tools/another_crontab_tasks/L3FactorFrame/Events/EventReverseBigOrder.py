

import numpy as np
from L3FactorFrame.FactorBase import FactorBase
from L3FactorFrame.tools.DecimalUtil import isEqual, greaterThan, lessThan, equalGreaterThan, equalLessThan

class EventReverseBigOrder(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        self.__quantile = self.getParameter("Quantile")
        self.__ratio = self.getParameter("Ratio")

    def calculate(self):
        order_vol_quantile = np.floor(self.getDailyOrderParameterData(f"OrderVolQ{self.__quantile}"))
        askv0_quantile = order_vol_quantile
        bidv0_quantile = order_vol_quantile
        tickDataIndex = self.getPrevTick("SeqNo")
        # if isEqual(tickDataIndex, 4637164):
        #     print("debug")
        orderIndex = self.getPrevOrder("SeqNo")
        cancelIndex = self.getPrevCancel("SeqNo")
        if not self.check_data_index(tickDataIndex, orderIndex, cancelIndex):
            raise IndexError("Tick SeqNo not Equal to OrderIndex or CancelIndex!")

        tickAskPriceList = self.getPrevNTick("AskPrice", 2)
        tickBidPriceList = self.getPrevNTick("BidPrice", 2)
        tickAskVolumeList = self.getPrevNTick("AskVolume", 2)
        tickBidVolumeList = self.getPrevNTick("BidVolume", 2)

        if len(tickAskPriceList) < 2:
            factorValue = 0
        else:
            factorValue = 0
            lastTickAskPrice, currentTickAskPrice = tickAskPriceList
            lastTickBidPrice, currentTickBidPrice = tickBidPriceList
            lastTickAskVolume, currentTickAskVolume = tickAskVolumeList
            lastTickBidVolume, currentTickBidVolume = tickBidVolumeList

            if ((0 not in currentTickAskPrice[:5]) and (0 not in currentTickBidPrice[:5])):
                lastTickAskP0, lastTickBidP0 = lastTickAskPrice[0], lastTickBidPrice[0]
                currentTickAskP0, currentTickBidP0 = currentTickAskPrice[0], currentTickBidPrice[0]
                lastTickAskV0, lastTickBidV0 = lastTickAskVolume[0], lastTickBidVolume[0]
                currentTickAskV0, currentTickBidV0 = currentTickAskVolume[0], currentTickBidVolume[0]

                if isEqual(tickDataIndex, orderIndex):
                    orderBSFlag = self.getPrevOrder("BSFlag")
                    orderVolume = self.getPrevOrder("Volume")
                    orderPrice = self.getPrevOrder("Price")
                    orderType = self.getPrevOrder("OrderType")

                    if isEqual(orderBSFlag, 1):
                        if equalGreaterThan(orderVolume, askv0_quantile) \
                                and (isEqual(orderType, 1) or (isEqual(orderType, 2) and equalGreaterThan(orderPrice, lastTickAskP0))) \
                                and greaterThan(currentTickAskP0, lastTickAskP0) \
                                and greaterThan(currentTickBidP0, lastTickBidP0) \
                                and greaterThan(orderVolume, lastTickAskV0) \
                                and lessThan(currentTickBidV0, orderVolume * self.__ratio):
                            factorValue = -1
                    elif isEqual(orderBSFlag, 2):
                        if equalGreaterThan(orderVolume, bidv0_quantile) \
                                and (isEqual(orderType, 1) or (isEqual(orderType, 2) and equalLessThan(orderPrice, lastTickBidP0))) \
                                and lessThan(currentTickAskP0, lastTickAskP0) \
                                and lessThan(currentTickBidP0, lastTickBidP0) \
                                and greaterThan(orderVolume, lastTickBidV0) \
                                and lessThan(currentTickAskV0, orderVolume * self.__ratio):
                            factorValue = 1

        self.addFactorValue(factorValue)

    @staticmethod
    def check_data_index(tickDataIndex, orderIndex, cancelIndex):
        flag = isEqual(tickDataIndex, orderIndex) or isEqual(tickDataIndex, cancelIndex)
        return flag