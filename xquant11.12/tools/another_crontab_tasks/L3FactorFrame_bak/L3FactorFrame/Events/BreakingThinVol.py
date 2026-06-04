import numpy as np
import pandas as pd
from FactorBase import FactorBase
from DecimalUtil import isEqual, greaterThan, lessThan, equalGreaterThan, equalLessThan, EPSILON

class BreakingThinVol(FactorBase):
    def __init__(self, config, marketDataManager):
        super().__init__(config, marketDataManager)
        self.__interval = config.get("interval", 0.055)
        self.__breaking_num = config.get("breaking_num", 3) #突破稀薄盘口的个数, 包括本身这一档
        symbol = self.marketDataManager.getSymbol()
        date = self.marketDataManager.getDate()
        self._quantile_df = pd.read_parquet(f"/dfs/group/800657/library/l3_event/event_params/{symbol}.parquet")
        self._quantile_df = self._quantile_df[self._quantile_df["Date"]==date]
        self.askv0_quantile = self._quantile_df["AskV0Q50"].iloc[0]
        self.bidv0_quantile = self._quantile_df["BidV0Q50"].iloc[0]#np.floor(self.getDailyParameterData(f"TBV0Q{self.__quantile}"))

    def calculate(self):
        tickDataIndex = self.getPrevTick("SeqNo")
        orderIndex = self.getPrevOrder("SeqNo")
        cancelIndex = self.getPrevCancel("SeqNo")

        tickAskPriceList = self.getPrevNTick("AskPrice", 2)
        tickBidPriceList = self.getPrevNTick("BidPrice", 2)
        tickAskVolumeList = self.getPrevNTick("AskVolume", 2)
        tickBidVolumeList = self.getPrevNTick("BidVolume", 2)

        if isEqual(tickDataIndex, 8953122):
            a = 1

        if len(tickAskPriceList) < 2:
            factorValue = 0
        else:
            factorValue = 0
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
                        # 波段满足：对手方多档盘口被连续消耗
                        if equalGreaterThan(orderPrice, lastTickAskP0+EPSILON) \
                                and greaterThan(currentTickAskP0, lastTickAskP0+EPSILON):
                            localAskPrice = self.getPrevSecTick("AskPrice", self.__interval)
                            localAskVolume = self.getPrevSecTick("AskVolume", self.__interval)
                            localOrderBSFlag = self.getPrevSecOrder("BSFlag", self.__interval)
                            localOrderType = self.getPrevSecOrder("OrderType", self.__interval)
                            localOrderPrice = self.getPrevSecOrder("Price", self.__interval)
                            localOrderVolume = self.getPrevSecOrder("Volume", self.__interval)
                            breakingNum = 0#被突破的盘口档位
                            breakingVol = 0
                            for aidx, askPrice in enumerate(localAskPrice[0]):
                                # 突破的挡位数量不能太小
                                if askPrice < currentTickAskP0 - EPSILON:
                                    breakingNum+=1
                                    breakingVol+=localAskVolume[0][aidx]
                                else:
                                    break
                            netBidVolume = np.sum(localOrderVolume[(localOrderBSFlag == 1) & (
                                        (localOrderPrice >= currentTickAskP0 - EPSILON) | (localOrderType == 1))]) \
                                           - np.sum(localOrderVolume[(localOrderBSFlag == 2) & (
                                        (localOrderPrice <= currentTickAskP0 + EPSILON) | (localOrderType == 1))])
                            if equalGreaterThan(breakingNum, self.__breaking_num) and netBidVolume>self.askv0_quantile:
                                factorValue = breakingNum #breakingVol/self.askv0_quantile

                    elif isEqual(orderBSFlag, 2):
                        if equalLessThan(orderPrice, lastTickBidP0-EPSILON) \
                                and lessThan(currentTickBidP0, lastTickBidP0-EPSILON):
                            localBidPrice = self.getPrevSecTick("BidPrice", self.__interval)
                            localBidVolume = self.getPrevSecTick("BidVolume", self.__interval)
                            localOrderBSFlag = self.getPrevSecOrder("BSFlag", self.__interval)
                            localOrderType = self.getPrevSecOrder("OrderType", self.__interval)
                            localOrderPrice = self.getPrevSecOrder("Price", self.__interval)
                            localOrderVolume = self.getPrevSecOrder("Volume", self.__interval)
                            breakingNum = 0  # 被突破的盘口档位
                            breakingVol = 0
                            for bidx, bidPrice in enumerate(localBidPrice[0]):
                                if bidPrice > currentTickBidP0 + EPSILON:
                                    breakingNum += 1
                                    breakingVol += localBidVolume[0][bidx]
                                else:
                                    break
                            netAskVolume = np.sum(localOrderVolume[(localOrderBSFlag == 2) & (
                                        (localOrderPrice <= currentTickBidP0 + EPSILON) | (localOrderType == 1))]) \
                                           - np.sum(localOrderVolume[(localOrderBSFlag == 1) & (
                                        (localOrderPrice >= currentTickBidP0 - EPSILON) | (localOrderType == 1))])
                            if equalGreaterThan(breakingNum, self.__breaking_num) and  netAskVolume>self.bidv0_quantile:
                                factorValue = -breakingNum #breakingVol / self.bidv0_quantile
        self.addFactorValue(factorValue)
