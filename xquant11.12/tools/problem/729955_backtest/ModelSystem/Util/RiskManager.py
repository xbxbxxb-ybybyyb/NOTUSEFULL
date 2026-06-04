# -*- coding: utf-8 -*-
"""
Implement some risk control functions, such as stop loss.

by 011478
"""
from ModelSystem.Util.OrderSide import OrderSide


class RiskManager:
    def __init__(self, STOP_LOSS_PARAM):
        self.__STOP_LOSS_PARAM = STOP_LOSS_PARAM
        self.__DANGER_LINE_PARAM = 999999
        self.__costInfoMap = {}  # key = symbol, value = CostInfo
        self.__isStopLoss = {}  # key = symbol, value = boolean of whether to stop loss
        self.__inDanger = {}  # key = symbol, value = if price reaches the limits
        self.__lastNetPosition = {}  # key = symbol, value = last net position
        self.__curr_return = {}  # key = symbol, value = current return on ask/bid one, 0 if there is no position

    def resetNewDay(self):
        self.__costInfoMap = {}
        self.__isStopLoss = {}
        self.__inDanger = {}
        self.__lastNetPosition = {}
        self.__curr_return = {}

    # Called when exchange order finished. Net position should be updated first.
    def updateCost(self, exchangeOrder, netPosition):
        symbol = exchangeOrder.code
        avePrice = exchangeOrder.price()
        cumQty = exchangeOrder.volume
        if symbol not in self.__lastNetPosition:
            self.__lastNetPosition.update({symbol: 0})

        if exchangeOrder.BSFlag == 'B':
            orderSide = OrderSide.Buy
        else:
            orderSide = OrderSide.Sell

        if symbol not in self.__costInfoMap:
            self.__costInfoMap.update({symbol: CostInfo(avePrice, cumQty, orderSide)})
        else:
            if netPosition * self.__lastNetPosition.get(symbol) < 0:
                # 头寸翻转
                self.__costInfoMap.update({symbol: CostInfo(avePrice, abs(netPosition), orderSide)})
                self.__setStopLoss(symbol, False)
            else:
                cost = self.__costInfoMap.get(symbol)
                if cost.orderSide == orderSide:
                    preCost = cost.avePrice * cost.totalQty
                    newTotalQty = cost.totalQty + cumQty
                    newAvePrice = (preCost + avePrice * cumQty) / newTotalQty

                    cost.avePrice = newAvePrice
                    cost.totalQty = newTotalQty
                else:
                    cost.totalQty -= cumQty

        if 0 <= netPosition < 10:
            self.__costInfoMap.pop(symbol, None)
            self.__setStopLoss(symbol, False)
        self.__lastNetPosition.update({symbol: netPosition})

    # Called on every tick, to check if to stop loss, and to update the current return.
    def checkStopLoss(self, symbol, sliceData):
        self.__curr_return.pop(symbol, None)
        lastPx = sliceData.lastPrice
        preClosePx = sliceData.previousClosingPrice
        if lastPx == 0 or preClosePx == 0:
            return

        ratio = abs(lastPx / preClosePx - 1.0)
        if ratio >= self.__DANGER_LINE_PARAM:
            self.__setInDanger(symbol, True)
        else:
            self.__setInDanger(symbol, False)

        if symbol not in self.__costInfoMap:
            return
        else:
            cost = self.__costInfoMap.get(symbol)
            avePrice = cost.avePrice
            if cost.orderSide == OrderSide.Buy:
                cmpPrice = sliceData.bidPrice[0]
                if cmpPrice == 0:
                    cmpPrice = sliceData.askPrice[0]
                if not self.isStopLoss(symbol):
                    if cmpPrice <= avePrice * (1 - self.__STOP_LOSS_PARAM):
                        self.__setStopLoss(symbol, True)
            else:
                cmpPrice = sliceData.askPrice[0]
                if cmpPrice == 0:
                    cmpPrice = sliceData.bidPrice[0]
                if not self.isStopLoss(symbol):
                    if cmpPrice >= avePrice * (1 + self.__STOP_LOSS_PARAM):
                        self.__setStopLoss(symbol, True)
            # calculate the current return
            curr_return = (cmpPrice - avePrice) / avePrice
            self.__curr_return.update({symbol: curr_return})

    def isStopLoss(self, symbol):
        if symbol not in self.__isStopLoss:
            self.__setStopLoss(symbol, False)
        return self.__isStopLoss.get(symbol)

    def __setStopLoss(self, symbol, isStopLoss):
        self.__isStopLoss.update({symbol: isStopLoss})

    def isInDanger(self, symbol):
        if symbol not in self.__inDanger:
            self.__setInDanger(symbol, False)
        return self.__inDanger.get(symbol)

    def __setInDanger(self, symbol, isInDanger):
        self.__inDanger.update({symbol: isInDanger})

    def get_curr_return(self, symbol):
        if symbol in self.__curr_return:
            return self.__curr_return.get(symbol)
        else:
            return 0


class CostInfo:
    def __init__(self, avePrice, totalQty, orderSide):
        self.avePrice = avePrice
        self.totalQty = totalQty
        self.orderSide = orderSide
