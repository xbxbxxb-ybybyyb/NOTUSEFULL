import numpy as np
from L3FactorFrame.FactorBase import FactorBase
from L3FactorFrame.tools.DecimalUtil import isEqual, greaterThan, lessThan, equalGreaterThan, equalLessThan

class EventOneSideVD(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)
        self.__ratio = self.getParameter("Ratio")
        self.__max_lookback = self.getParameter("Max_Lookback")
        self.__trigger_n = self.getParameter("Trigger_N")

    def calculate(self):
        tickDataIndex = self.getPrevTick("SeqNo")
        # if isEqual(tickDataIndex, 543314):
        #     print("debug")
        orderIndex = self.getPrevOrder("SeqNo")
        cancelIndex = self.getPrevCancel("SeqNo")
        if not self.check_data_index(tickDataIndex, orderIndex, cancelIndex):
            raise IndexError("Tick SeqNo not Equal to OrderIndex or CancelIndex!")
        orderBSFlag = self.getPrevOrder("BSFlag")
        cancelBSFlag = self.getPrevCancel("BSFlag")

        currentTickAskPrice = self.getPrevTick("AskPrice")
        currentTickBidPrice = self.getPrevTick("BidPrice")
        factorValue = 0
        if ((0 not in currentTickAskPrice[:5]) and (0 not in currentTickBidPrice[:5])):
            tickAskP0List = self.getPrevNTick("AskP0", self.__max_lookback)
            tickAskV0List = self.getPrevNTick("AskV0", self.__max_lookback)
            tickBidP0List = self.getPrevNTick("BidP0", self.__max_lookback)
            tickBidV0List = self.getPrevNTick("BidV0", self.__max_lookback)
            if len(tickAskP0List) < 2:
                factorValue = 0
            else:
                currentTickAskP0, lastTickAskP0 = tickAskP0List[-1], tickAskP0List[-2]
                currentTickAskV0, lastTickAskV0 = tickAskV0List[-1], tickAskV0List[-2]
                currentTickBidP0, lastTickBidP0 = tickBidP0List[-1], tickBidP0List[-2]
                currentTickBidV0, lastTickBidV0 = tickBidV0List[-1], tickBidV0List[-2]

                if isEqual(tickDataIndex, orderIndex):
                    if isEqual(orderBSFlag, 1):
                        if isEqual(currentTickAskP0, lastTickAskP0) \
                                and isEqual(currentTickBidP0, lastTickBidP0) \
                                and lessThan(currentTickAskV0, lastTickAskV0):
                            if self.is_event_triggered(tickAskP0List, tickAskV0List, tickBidP0List, tickBidV0List,
                                                       "Buy"):
                                factorValue = 1
                    elif isEqual(orderBSFlag, 2):
                        if isEqual(currentTickAskP0, lastTickAskP0) \
                                and isEqual(currentTickBidP0, lastTickBidP0) \
                                and lessThan(currentTickBidV0, lastTickBidV0):
                            if self.is_event_triggered(tickAskP0List, tickAskV0List, tickBidP0List, tickBidV0List,
                                                       "Sell"):
                                factorValue = -1
                elif isEqual(tickDataIndex, cancelIndex):
                    if isEqual(cancelBSFlag, 2):
                        if isEqual(currentTickAskP0, lastTickAskP0) \
                                and isEqual(currentTickBidP0, lastTickBidP0) \
                                and lessThan(currentTickAskV0, lastTickAskV0):
                            if self.is_event_triggered(tickAskP0List, tickAskV0List, tickBidP0List, tickBidV0List,
                                                       "Buy"):
                                factorValue = 1
                    elif isEqual(cancelBSFlag, 1):
                        if isEqual(currentTickAskP0, lastTickAskP0) \
                                and isEqual(currentTickBidP0, lastTickBidP0) \
                                and lessThan(currentTickBidV0, lastTickBidV0):
                            if self.is_event_triggered(tickAskP0List, tickAskV0List, tickBidP0List, tickBidV0List,
                                                       "Sell"):
                                factorValue = -1
                else:
                    raise IndexError("Tick SeqNo not Equal to OrderIndex or CancelIndex!")

        self.addFactorValue(factorValue)

    def is_event_triggered(self, ap0List, av0List, bp0List, bv0List, side):
        L = len(ap0List)
        currentAskP0, currentAskV0, currentBidP0, currentBidV0 = ap0List[-1], av0List[-1], bp0List[-1], bv0List[-1]
        if side == "Buy":
            lastAskV0 = currentAskV0
            CONTINUOUS_NUM = 0
            CONTINUOUS_CALC_FLAG = True
            for i in list(range(L-1))[::-1]:
                localAskP0, localAskV0, localBidP0, localBidV0 = ap0List[i], av0List[i], bp0List[i], bv0List[i]
                if isEqual(currentAskP0, localAskP0) \
                        and isEqual(currentBidP0, localBidP0) \
                        and isEqual(currentBidV0, localBidV0):
                    if equalGreaterThan((localAskV0 - currentAskV0) / localAskV0, self.__ratio):
                        return True
                    if CONTINUOUS_CALC_FLAG:
                        if greaterThan(localAskV0, lastAskV0):
                            CONTINUOUS_NUM += 1
                            lastAskV0 = localAskV0
                            if CONTINUOUS_NUM >= self.__trigger_n:
                                return True
                        elif lessThan(localAskV0, lastAskV0):
                            CONTINUOUS_CALC_FLAG = False
                else:
                    return False
        elif side == "Sell":
            lastBidV0 = currentBidV0
            CONTINUOUS_NUM = 0
            CONTINUOUS_CALC_FLAG = True
            for i in list(range(L-1))[::-1]:
                localAskP0, localAskV0, localBidP0, localBidV0 = ap0List[i], av0List[i], bp0List[i], bv0List[i]
                if isEqual(currentAskP0, localAskP0) \
                        and isEqual(currentBidP0, localBidP0) \
                        and isEqual(currentAskV0, localAskV0):
                    if equalGreaterThan((localBidV0 - currentBidV0) / localBidV0, self.__ratio):
                        return True
                    if CONTINUOUS_CALC_FLAG:
                        if greaterThan(localBidV0, lastBidV0):
                            CONTINUOUS_NUM += 1
                            lastBidV0 = localBidV0
                            if CONTINUOUS_NUM >= self.__trigger_n:
                                return True
                        elif lessThan(localBidV0, lastBidV0):
                            CONTINUOUS_CALC_FLAG = False
                else:
                    return False
        return False

    @staticmethod
    def check_data_index(tickDataIndex, orderIndex, cancelIndex):
        flag = isEqual(tickDataIndex, orderIndex) or isEqual(tickDataIndex, cancelIndex)
        return flag