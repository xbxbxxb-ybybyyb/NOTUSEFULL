

import numpy as np
from FactorBase import FactorBase
from DecimalUtil import isEqual, greaterThan, lessThan, equalGreaterThan, equalLessThan, EPSILON
import pandas as pd

class CumOrdersNetVolOverV0(FactorBase):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__interval = config.get("interval", 0.055)
        symbol = self.marketDataManager.getSymbol()
        date = self.marketDataManager.getDate()
        self._quantile_df = pd.read_parquet(f"/dfs/group/800657/library/l3_event/event_params/{symbol}.parquet")
        self._quantile_df = self._quantile_df[self._quantile_df["Date"]==date]
        self.askv0_quantile =self._quantile_df["AskV0Q50"].iloc[0]
        self.bidv0_quantile = self._quantile_df["BidV0Q50"].iloc[0]#np.floor(self.getDailyParameterData(f"TBV0Q{self.__quantile}"))


    def calculate(self):
        askv0_quantile = self.askv0_quantile
        bidv0_quantile = self.bidv0_quantile
        tickDataIndex = self.getPrevTick("SeqNo")
        if isEqual(tickDataIndex, 1427085):
            a = 1
        orderIndex = self.getPrevOrder("SeqNo")
        cancelIndex = self.getPrevCancel("SeqNo")

        orderBSFlag = self.getPrevOrder("BSFlag")

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

            if True:#((0 not in currentTickAskPrice[:5]) and (0 not in currentTickBidPrice[:5])):
                lastTickAskP0, lastTickBidP0 = lastTickAskPrice[0], lastTickBidPrice[0]
                currentTickAskP0, currentTickBidP0 = currentTickAskPrice[0], currentTickBidPrice[0]
                lastTickAskV0, lastTickBidV0 = lastTickAskVolume[0], lastTickBidVolume[0]
                currentTickAskV0, currentTickBidV0 = currentTickAskVolume[0], currentTickBidVolume[0]

                if isEqual(tickDataIndex, orderIndex):
                    if isEqual(orderBSFlag, 1):
                        # 波段满足：卖方一档流动性被不断消耗的时刻，触发统计。计算累计n秒内的主买否超过原来的一档量【主卖力量是否能撼动一档】
                        if isEqual(currentTickAskP0, lastTickAskP0) \
                                and lessThan(currentTickAskV0, lastTickAskV0):
                            localOrderBSFlag = self.getPrevSecOrder("BSFlag", self.__interval)
                            localOrderType = self.getPrevSecOrder("OrderType", self.__interval)
                            localOrderPrice = self.getPrevSecOrder("Price", self.__interval)
                            localOrderVolume = self.getPrevSecOrder("Volume", self.__interval)
                            netBidVolume = np.sum(localOrderVolume[(localOrderBSFlag == 1) & (
                                        (localOrderPrice >= currentTickAskP0 - EPSILON) | (localOrderType == 1))]) \
                                           - np.sum(localOrderVolume[(localOrderBSFlag == 2) & (
                                        (localOrderPrice <= currentTickAskP0 + EPSILON) | (localOrderType == 1))])
                            if equalGreaterThan(netBidVolume, currentTickAskV0) \
                                    and equalGreaterThan(netBidVolume, askv0_quantile):
                                factorValue = 1

                    elif isEqual(orderBSFlag, 2):
                        if isEqual(currentTickBidP0, lastTickBidP0) \
                                and lessThan(currentTickBidV0, lastTickBidV0):
                            localOrderBSFlag = self.getPrevSecOrder("BSFlag", self.__interval)
                            localOrderType = self.getPrevSecOrder("OrderType", self.__interval)
                            localOrderPrice = self.getPrevSecOrder("Price", self.__interval)
                            localOrderVolume = self.getPrevSecOrder("Volume", self.__interval)
                            netAskVolume = np.sum(localOrderVolume[(localOrderBSFlag == 2) & (
                                        (localOrderPrice <= currentTickBidP0 + EPSILON) | (localOrderType == 1))]) \
                                           - np.sum(localOrderVolume[(localOrderBSFlag == 1) & (
                                        (localOrderPrice >= currentTickBidP0 - EPSILON) | (localOrderType == 1))])
                            if (equalGreaterThan(netAskVolume, currentTickBidV0)
                                    and equalGreaterThan(netAskVolume, bidv0_quantile)):
                                factorValue = -1

        self.addFactorValue(factorValue)
