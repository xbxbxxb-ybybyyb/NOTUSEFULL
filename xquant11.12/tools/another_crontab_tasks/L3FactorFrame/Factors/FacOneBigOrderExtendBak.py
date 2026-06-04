

import numpy as np
from L3FactorFrame.FactorBase import FactorBase
from L3FactorFrame.tools.DecimalUtil import isEqual, greaterThan, lessThan, equalGreaterThan, equalLessThan, EPSILON
from xquant.xqutils.perf_profile import profile
import pandas as pd

class FacOneBigOrderExtend(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        symbol = self.marketDataManager.getSymbol()
        date = self.marketDataManager.getDate()
        self._quantile_df = pd.read_parquet(f"/dfs/group/800657/library/l3_event/event_params/{symbol}.parquet")
        self._quantile_df = self._quantile_df[self._quantile_df["Date"]==date]
        self.askv0_quantile = self._quantile_df["AskV0Q50"].iloc[0]
        self.bidv0_quantile = self._quantile_df["BidV0Q50"].iloc[0]#np.floor(self.getDailyParameterData(f"TBV0Q{self.__quantile}"))
        self.__spread_ratio = config.get("spread_ratio", 3) #连吃多档之间的价差

        self.i = 0

    def calculate(self):
        self.i = self.i+1

        askv0_quantile = self.askv0_quantile
        bidv0_quantile = self.bidv0_quantile
        tickDataIndex = self.getPrevTick("SeqNo")

        orderIndex = self.getPrevOrder("SeqNo")
        tradeIndex = self.getPrevTrade("SeqNo")
        cancelIndex = self.getPrevCancel("SeqNo")

        orderBSFlag = self.getPrevOrder("BSFlag")
        cancelBSFlag = self.getPrevCancel("BSFlag")

        tickAskPriceList = self.getPrevNTick("AskPrice", 2)
        tickBidPriceList = self.getPrevNTick("BidPrice", 2)
        tickAskVolumeList = self.getPrevNTick("AskVolume", 2)
        tickBidVolumeList = self.getPrevNTick("BidVolume", 2)

        tickVolumeList = self.getPrevNTick("ttl_volume", 2)

        if orderIndex==366021:
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
                cum_vol = tickVolumeList[1] - tickVolumeList[0]

                if isEqual(tickDataIndex, orderIndex):
                    if isEqual(orderBSFlag, 1):
                        # if isEqual(currentTickAskP0, lastTickAskP0) \
                        #         and lessThan(currentTickAskV0, lastTickAskV0) \
                        #         and equalGreaterThan(lastTickAskV0 - currentTickAskV0, lastTickAskV0 / 2) \
                        #         and equalGreaterThan(lastTickAskV0 - currentTickAskV0, askv0_quantile):
                        #     factorValue = 1
                        # 买单吃了多档
                        if cum_vol > 3 * askv0_quantile and currentTickBidP0 < 2 * cum_vol and currentTickAskP0 > lastTickAskP0 + EPSILON:  # and (currentTickAskP0/lastTickAskP0-1)*1000>self.__spread_ratio:
                            # 连续消耗多档连续性
                            cum_buy_col = tickVolumeList[1] - tickVolumeList[0]
                            factorValue = cum_buy_col/askv0_quantile

                    elif isEqual(orderBSFlag, 2):
                        # if isEqual(currentTickBidP0, lastTickBidP0) \
                        #         and lessThan(currentTickBidV0, lastTickBidV0) \
                        #         and equalGreaterThan(lastTickBidV0 - currentTickBidV0, lastTickBidV0 / 2) \
                        #         and equalGreaterThan(lastTickBidV0 - currentTickBidV0, bidv0_quantile):
                        #     factorValue = -1
                        if cum_vol > 3 * bidv0_quantile and currentTickAskP0 < 2 * cum_vol and currentTickBidP0 < lastTickBidP0 - EPSILON:  # and (1-currentTickBidP0/lastTickBidP0)*1000 > self.__spread_ratio:
                            # 连续消耗多档连续性
                            cum_sell_col = tickVolumeList[1] - tickVolumeList[0]
                            factorValue = -cum_sell_col/bidv0_quantile
                # elif isEqual(tickDataIndex, cancelIndex):
                #     if isEqual(cancelBSFlag, 2):
                #         # if isEqual(currentTickAskP0, lastTickAskP0) \
                #         #         and lessThan(currentTickAskV0, lastTickAskV0) \
                #         #         and equalGreaterThan(lastTickAskV0 - currentTickAskV0, lastTickAskV0 / 2) \
                #         #         and equalGreaterThan(lastTickAskV0 - currentTickAskV0, askv0_quantile):
                #         #     factorValue = 1
                #         if greaterThan(currentTickAskP0-EPSILON, lastTickAskP0) and lastTickAskV0>askv0_quantile:
                #             # 撤掉卖一
                #             factorValue = lastTickAskV0/askv0_quantile
                #     elif isEqual(cancelBSFlag, 1):
                #         # if isEqual(currentTickBidP0, lastTickBidP0) \
                #         #         and lessThan(currentTickBidV0, lastTickBidV0) \
                #         #         and equalGreaterThan(lastTickBidV0 - currentTickBidV0, lastTickBidV0 / 2) \
                #         #         and equalGreaterThan(lastTickBidV0 - currentTickBidV0, bidv0_quantile):
                #         #     factorValue = -1
                #         if lessThan(currentTickBidP0+EPSILON, lastTickBidP0) and lastTickAskP0>bidv0_quantile:
                #             # 撤掉买一
                #             factorValue = -lastTickBidV0/bidv0_quantile
                else:
                    pass#raise IndexError("Tick SeqNo not Equal to OrderIndex or CancelIndex!")
        self.addFactorValue(factorValue)
