

import numpy as np
from FactorBase import FactorBase
from DecimalUtil import isEqual, greaterThan, lessThan, equalGreaterThan, equalLessThan, EPSILON

class FacBreakingP0NumOrders(FactorBase):
    def __init__(self, config, marketDataManager):
        super().__init__(config, marketDataManager)
        self.__interval = config.get("interval", 0.055)
        self.__continuous_num = config.get("continuous_num", 6)

    def calculate(self):
        tickDataIndex = self.getPrevTick("SeqNo")
        orderIndex = self.getPrevOrder("SeqNo")
        cancelIndex = self.getPrevCancel("SeqNo")

        tickAskPriceList = self.getPrevNTick("AskPrice", 2)
        tickBidPriceList = self.getPrevNTick("BidPrice", 2)
        tickAskVolumeList = self.getPrevNTick("AskVolume", 2)
        tickBidVolumeList = self.getPrevNTick("BidVolume", 2)

        if len(tickAskPriceList) < 2:
            factorValue = 0.0
        else:
            factorValue = 0.0
            lastTickAskPrice, currentTickAskPrice = tickAskPriceList
            lastTickBidPrice, currentTickBidPrice = tickBidPriceList
            lastTickAskVolume, currentTickAskVolume = tickAskVolumeList
            lastTickBidVolume, currentTickBidVolume = tickBidVolumeList

            if True:#((0 not in currentTickAskPrice[:5]) and (0 not in currentTickBidPrice[:5])):
                lastTickAskP0, lastTickBidP0 = lastTickAskPrice[0], lastTickBidPrice[0]
                currentTickAskP0, currentTickBidP0 = currentTickAskPrice[0], currentTickBidPrice[0]
                lastTickAskV0, lastTickBidV0 = lastTickAskVolume[0], lastTickBidVolume[0]
                currentTickAskV0, currentTickBidV0 = currentTickAskVolume[0], currentTickBidVolume[0]

                if isEqual(tickDataIndex, orderIndex):
                    orderPrice = self.getPrevOrder("Price")
                    orderVolume = self.getPrevOrder("Volume")
                    orderBSFlag = self.getPrevOrder("BSFlag")
                    if isEqual(orderBSFlag, 1):
                        # 波段满足：对手方一档的流动性不断被消耗，才触发统计。过去极短时间的主动单个数是否大于某一个阈值，【即一档是否被（很多单子）快速消耗】
                        if equalGreaterThan(orderPrice, lastTickAskP0) \
                                and lessThan(orderVolume, lastTickAskV0)\
                                and lessThan(currentTickAskV0, lastTickAskV0):
                            localOrderBSFlag = self.getPrevSecOrder("BSFlag", self.__interval)
                            localOrderPrice = self.getPrevSecOrder("Price", self.__interval)
                            localOrderVolume = self.getPrevSecOrder("Volume", self.__interval)
                            netBidVolume = np.sum(localOrderVolume[localOrderBSFlag == 1]) \
                                           - np.sum(localOrderVolume[localOrderBSFlag == 2])
                            if equalGreaterThan(netBidVolume, 0):
                                continuoustBidOrderNum = np.sum((localOrderBSFlag == 1)
                                                                & (localOrderPrice >= currentTickAskP0 - 0.01 - EPSILON))
                                if equalGreaterThan(continuoustBidOrderNum, self.__continuous_num):
                                    factorValue = continuoustBidOrderNum/self.__continuous_num

                    elif isEqual(orderBSFlag, 2):
                        if equalLessThan(orderPrice, lastTickBidP0) \
                                and lessThan(orderVolume, lastTickBidV0)\
                                and lessThan(currentTickBidV0, lastTickBidV0):
                            localOrderBSFlag = self.getPrevSecOrder("BSFlag", self.__interval)
                            localOrderPrice = self.getPrevSecOrder("Price", self.__interval)
                            localOrderVolume = self.getPrevSecOrder("Volume", self.__interval)
                            netAskVolume = np.sum(localOrderVolume[localOrderBSFlag == 2]) \
                                           - np.sum(localOrderVolume[localOrderBSFlag == 1])
                            if equalGreaterThan(netAskVolume, 0):
                                continuoustAskOrderNum = np.sum((localOrderBSFlag == 2)
                                                                & (localOrderPrice <= currentTickBidP0 + 0.01 + EPSILON))
                                if equalGreaterThan(continuoustAskOrderNum, self.__continuous_num):
                                    factorValue = -continuoustAskOrderNum/self.__continuous_num

        self.addFactorValue(factorValue)
