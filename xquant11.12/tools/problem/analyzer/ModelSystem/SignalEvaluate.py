# -*- coding: utf-8 -*-
"""
Created on 2017/9/26 13:19

@author: 006547
@revise: 006688
"""
import datetime as dt
import sys
import importlib
from enum import Enum
import math
import numpy as np
import pickle

from typing import List, Tuple, Dict
from ModelSystem.Util.PositionManager import PositionManager
from ModelSystem.Util.OutputManager import OutputManager
from ModelSystem.Util.RiskManager import RiskManager
from ModelSystem.Util.OrderSide import OrderSide
from ExchangeHouse.ExchangeHouse import ExchangeHouse
from ExchangeHouse.ExchangeOrder import ExchangeOrder
from ExchangeHouse.Data.Data import Data
from ExchangeHouse.Order import Order
from ModelSystem.Util.SimpleDataConverter import SimpleDataConverter
from ModelSystem.Util.SimpleSignalHandler import *
from ModelSystem.Util.ExcelWriter import OutputSpreadSheet
from Utils_BT.InputManager import Input
from xquant.compute.sparkmr import remote_print


class SignalEvaluate:
    # temporarily use default initialisation
    def __init__(self, inputs: 'Input', signal_trigger_pairs: List[Tuple[pd.DataFrame, Dict[str, float]]]):
        # 定义一些常量
        mockTradePara = inputs.mock_trade_para
        self.__STOP_LOSS = abs(mockTradePara["maxLose"])  # 止损线参数（不考虑手续费）
        self.__COST_RATE = 0.0012  # 手续费
        self.__NOON = 120000000  # 12:00:00
        self.__MARKET_CLOSE = 145500000  # 14:55:00

        self.__symbol = inputs.symbol
        self.__OPEN_FORBIDDEN = 0.195 if self.__symbol.startswith("3") or self.__symbol.startswith("688") else 0.095 # 禁止开仓涨跌幅
        # self.__OPEN_FORBIDDEN = 0.095
        self.__short_symbol = self.__symbol[: -3]
        self.__output_path = inputs.output_path_dir

        self.__tick = inputs.tick
        self.__transaction = inputs.transaction
        self.__data_dict = inputs.tick_dict
        self.__signal_trigger_paris: List[Tuple[pd.DataFrame, Dict[str, float]]] = signal_trigger_pairs
        for signal_data, trigger_dict in self.__signal_trigger_paris:
            if signal_data.columns[0] != 'Timestamp':
                raise Exception('The first column is not Timestamp!')
            elif len(signal_data.columns) != 3:
                raise Exception('There are NOT three columns in the data frame!')

        self.__executorStr = inputs.executor_str

        self.__outputMgr = OutputManager(self.__COST_RATE, True)
        self.__positionManager = PositionManager()
        self.__riskMgr = RiskManager(self.__STOP_LOSS, self.__symbol)

        self.__exchangeHouse = ExchangeHouse(Data(self.__tick, self.__transaction))
        self.__modules = importlib.import_module('ModelSystem.' + inputs.executor_str)  # 通过String来生成的Executor的实例，先import
        self.__signalExecutor = getattr(self.__modules, inputs.executor_str)(self.__positionManager, self.__riskMgr)
        self.__signalExecutor.set_data_dict(self.__data_dict)

        self.__START_OPEN_TIME = mockTradePara.get("startOpenTime")  # 从该时刻起，允许开仓。格式为 dt.time(9,30,0)
        if self.__START_OPEN_TIME is None:
            self.__START_OPEN_TIME = dt.time(9, 30, 0)  # 若外部参数没有设置，则默认值为 9:30:00起允许开仓
        self.__LAST_OPEN_TIME = mockTradePara.get("lastOpenTime")  # 从该时刻起，禁止开仓，若有仓位，则会依据信号值自然平仓。格式为 dt.time(9,45,0)
        if self.__LAST_OPEN_TIME is None:
            self.__LAST_OPEN_TIME = dt.time(14, 57, 0)  # 若外部参数没有设置，则默认值为 14:57:00起禁止再开仓

        self.__START_OPEN_TIME = mockTradePara["start_open_time"]
        self.__LAST_OPEN_TIME = mockTradePara["last_open_time"]  # 从该时刻起，禁止开仓。 若要赋值，须为   dt.time(9, 45, 0)  格式
        # self.__initAmount = mockTradePara["initAmount"]  # 初始资金
        self.__initQty = mockTradePara["initQty"]  # 初始额度
        self.__maxExposure = mockTradePara["maxExposure"]
        self.__maxTurnoverPerOrder = mockTradePara["maxTurnoverPerOrder"]  # 每笔最大委托金额
        self.__maxRatePerOrder = mockTradePara["maxRatePerOrder"]  # 每笔最大委托占比
        self.__openWithdrawSeconds = mockTradePara["openWithdrawSeconds"]  # 开仓单驱动时间
        self.__closeWithdrawSeconds = mockTradePara["closeWithdrawSeconds"]  # 平仓单驱动时间，建议始终设为3
        self.__buyLevel = mockTradePara["buyLevel"]  # 1-based index, not 0-based
        self.__sellLevel = mockTradePara["sellLevel"]  # 1-based index, not 0-based
        self.__buyDeviation = mockTradePara["buyDeviation"]
        self.__sellDeviation = mockTradePara["sellDeviation"]
        self.__MIN_ORDER_QTY = mockTradePara["MIN_ORDER_QTY"]
        self.__initAmount = None

        self.__preTagInfo = {}
        self.__pre_net_position = {}
        self.__orderInfo = {}  # record the order info for each sent order: orderNo, isOpen
        self.__exePriceQty = {}  # the dictionary (key = price, volume) (may be) returned in the signal executor
        self.__noonRange = {}  # the noon range is not a constant value. It may vary.

        self.__funStr = None
        self.__predictions = []
        self.__order_capacity = inputs.json_param

    def evaluate(self, show=None):
        # rollingTradingOrder = []
        self.__signalExecutor.set_json_param_before_start(self.__order_capacity)
        tempCombineTradingOrder = self.runBackTest(show)
        self.TradingEvaluate(tempCombineTradingOrder, False)
        # if show:
        #     self.__consoleOutput(tempCombineTradingOrder)
        detailedOrders = tempCombineTradingOrder.get("detailedOrders")
        tempCombineTradingOrder.pop("detailedOrders", None)
        if show is not None:
            output_path = self.__output_path + 'result_' + show + '.xls'
            OutputSpreadSheet(detailedOrders, tempCombineTradingOrder, output_path, self.__funStr, self.__symbol)
        return tempCombineTradingOrder

    def TradingEvaluate(self, TradingOrder, show):
        threshold = 0.001  # 盈利阈值
        triggerTimes = TradingOrder["order"].__len__()  # 触发次数
        winTimes = 0  # 获利次数
        winRate = 0  # 胜率
        timesPerDay = 0  # 日均开仓次数
        longTimes = 0  # 开多仓次数
        shortTimes = 0  # 开空仓次数
        averageReturnRate = 0  # 平均收益率
        averageReturnRateProfit = 0  # 平均获利收益率
        averageReturnRateLoss = 0  # 平均亏损收益率
        profitLossRatio = 0  # 盈亏比
        maxLoss = 0  # 最大亏损
        averagePositionTime = 0  # 平均持仓时间
        afterCostProfit = 0  # 算上手续费的总盈亏
        aveDailyCumAmount = 0  # 日均成交额
        maxDailyCumAmount = 0  # 最大日成交额
        annualReturnMV = 0  # 年化市值收益率
        averageTradingReturnRate = 0  # 交易收益率
        dayWinningRate = 0  # 日胜率
        cumOpenAmount = 0
        if triggerTimes != 0:
            winRate = winTimes / triggerTimes
            if self.__funStr is None:
                cumOpenAmount = TradingOrder["cumOpenAmount"]
                preCostProfit = TradingOrder["preCostProfit"]
                afterCostProfit = preCostProfit - self.__COST_RATE * cumOpenAmount
                afterCostProfit = round(afterCostProfit, 2)
                dayCounts = TradingOrder["dayCounts"]
                if dayCounts != 0:
                    aveDailyCumAmount = cumOpenAmount / dayCounts
                    for item in TradingOrder["dailyOpenAmount"].values():
                        if item > maxDailyCumAmount:
                            maxDailyCumAmount = item
                    annualReturnMV = afterCostProfit / self.__initAmount / dayCounts * 250
                    afterCostDailyProfit = TradingOrder["afterCostDailyProfit"]
                    dayWinningTimes = 0
                    for dailyProfit in afterCostDailyProfit.values():
                        if dailyProfit > 0:
                            dayWinningTimes += 1
                    dayWinningRate = dayWinningTimes / len(afterCostDailyProfit.values())
            else:
                dayCounts = len(self.__predictions) / 4800
            if dayCounts != 0:
                timesPerDay = triggerTimes / dayCounts
        if triggerTimes > 0:
            for order in TradingOrder["order"]:
                if show:
                    print(order)
                # 计算持仓时间(min)
                startTime = dt.datetime.strptime(order["startTime"], "%m/%d/%y-%H:%M:%S")
                endTime = dt.datetime.strptime(order["endTime"], "%m/%d/%y-%H:%M:%S")
                if startTime.hour <= 11 and endTime.hour >= 13:
                    averagePositionTime += (endTime - startTime).seconds / 60 - 90
                else:
                    averagePositionTime += (endTime - startTime).seconds / 60
                # 计算开多和开空次数
                if order["direction"] == 'long ':
                    longTimes += 1
                else:
                    shortTimes += 1
                # 计算收益率相关值
                averageReturnRate += order["returnRate"]
                if order["returnRate"] > threshold:
                    winTimes += 1
                    averageReturnRateProfit += order["returnRate"] - threshold
                else:
                    averageReturnRateLoss += order["returnRate"] - threshold
                    if order["returnRate"] < maxLoss:
                        maxLoss = order["returnRate"]
            averagePositionTime /= triggerTimes
            winRate = winTimes / triggerTimes
            averageReturnRate /= triggerTimes
            if winTimes > 0:
                averageReturnRateProfit /= winTimes
            if triggerTimes > winTimes:
                averageReturnRateLoss /= (triggerTimes - winTimes)
                if abs(averageReturnRateLoss) > 0:
                    profitLossRatio = averageReturnRateProfit / abs(averageReturnRateLoss)
        TradingOrder.update({"triggerTimes": triggerTimes})
        TradingOrder.update({"timesPerDay": timesPerDay})
        TradingOrder.update({"winTimes": winTimes})
        TradingOrder.update({"winRate": winRate})
        TradingOrder.update({"longTimes": longTimes})
        TradingOrder.update({"shortTimes": shortTimes})
        TradingOrder.update({"averageReturnRate": averageReturnRate})
        TradingOrder.update({"averageReturnRateProfit": averageReturnRateProfit})
        TradingOrder.update({"averageReturnRateLoss": averageReturnRateLoss})
        TradingOrder.update({"profitLossRatio": profitLossRatio})
        TradingOrder.update({"maxLoss": maxLoss})
        TradingOrder.update({"averagePositionTime": averagePositionTime})
        if self.__funStr is None:
            if cumOpenAmount != 0:
                averageTradingReturnRate = afterCostProfit / cumOpenAmount
            TradingOrder.update({"dayWinningRate": dayWinningRate})
            TradingOrder.update({"averageTradingReturnRate": averageTradingReturnRate})
            TradingOrder.update({"afterCostProfit": afterCostProfit})
            TradingOrder.update({"initQty": self.__initQty})
            TradingOrder.update({'initAmount': self.__initAmount})
            TradingOrder.update({"aveDailyCumAmount": aveDailyCumAmount})
            TradingOrder.update({"maxDailyCumAmount": maxDailyCumAmount})
            TradingOrder.update({"annualReturnMV": annualReturnMV})
        return TradingOrder

    def __consoleOutput(self, tempCombineTradingOrder):
        # print("modelName:          " + self.__modelName)
        print("longTriggerRatio:   " + str(tempCombineTradingOrder["longTriggerRatio"]))
        print("shortTriggerRatio:  " + str(tempCombineTradingOrder["shortTriggerRatio"]))
        print("triggerTimes:       " + str(tempCombineTradingOrder["triggerTimes"]))
        print("winTimes:           " + str(tempCombineTradingOrder["winTimes"]))
        print("winRate:            " + str(tempCombineTradingOrder["winRate"]))
        print("averageReturnRate:  " + str(tempCombineTradingOrder["averageReturnRate"]))
        print("longTimes:          " + str(tempCombineTradingOrder["longTimes"]))
        print("shortTimes:         " + str(tempCombineTradingOrder["shortTimes"]))
        print("profitLossRatio:    " + str(tempCombineTradingOrder["profitLossRatio"]))
        print("maxLoss:            " + str(tempCombineTradingOrder["maxLoss"]))
        print("averagePositionTime:" + str(tempCombineTradingOrder["averagePositionTime"]))
        print("timesPerDay:        " + str(tempCombineTradingOrder["timesPerDay"]))
        print("outSampleRMSE:      " + str(tempCombineTradingOrder["outSampleRMSE"]))
        print("numTrainData:       " + str(tempCombineTradingOrder["numTrainData"]))
        if self.__funStr is None:
            print("initAmount          " + str(tempCombineTradingOrder["initAmount"]))
            print("costRate            " + str(self.__COST_RATE))
            print("cumOpenAmount       " + str(tempCombineTradingOrder["cumOpenAmount"]))
            print("preCostProfit       " + str(tempCombineTradingOrder["preCostProfit"]))
            print("afterCostProfit     " + str(tempCombineTradingOrder["afterCostProfit"]))
            print("afterCostDailyProfit" + str(tempCombineTradingOrder["afterCostDailyProfit"]))
            print("dailyOpenAmount     " + str(tempCombineTradingOrder["dailyOpenAmount"]))
            print("aveDailyCumAmount   " + str(tempCombineTradingOrder["aveDailyCumAmount"]))
            print("maxDailyCumAmount   " + str(tempCombineTradingOrder["maxDailyCumAmount"]))
            print("annualReturnMV      " + str(tempCombineTradingOrder["annualReturnMV"]))
        print("\r")

    def runBackTest(self, show):
        if show is None:
            self.__outputMgr = OutputManager(self.__COST_RATE, True)
        else:
            self.__outputMgr = OutputManager(self.__COST_RATE, False)
        for signals, trigger_dict in self.__signal_trigger_paris:
            self.__reset_init_amount(signals)
            self.__signalExecutor.generateTriggerRatio(self.__symbol, trigger_dict, self.__tick)
            for index, row in signals.iterrows():
                timestamp = row[0]
                slice_data = self.__data_dict.get(timestamp)
                if slice_data is not None:
                    predictions = [row[1], row[2]]
                    self.__predictions.append(predictions)
                    self.__setNoonRange(self.__symbol, slice_data)
                    if self.__isNewDay(self.__symbol, slice_data.timeStamp):
                        self.__comingNewDay(self.__symbol, slice_data)
                    # making order here because the time span between two ticks may vary.
                    # making the order that was placed last tick
                    self.__makeOrder(self.__symbol, slice_data)
                    if self.__validTradingTime(slice_data.time):
                        self.__mockTrading(self.__symbol, predictions, slice_data)
                    else:
                        self.__processMarketClose(self.__symbol, slice_data)
                    self.__preTagInfo.update({self.__symbol: slice_data})
        return self.__returnTradings(self.__symbol)

    def __mockTrading(self, symbol, predictions, slice_data):
        self.__riskMgr.checkStopLoss(symbol, slice_data)
        # check non finished close order status
        if self.__positionManager.hasNonFinished(symbol):
            if self.__isOrderValid(symbol, slice_data) and not self.__riskMgr.isStopLoss(symbol) and not self.__riskMgr.isInDanger(symbol):
                # drive the non-finished order and return to the next predict slice directly
                self.__onNewTick(symbol, predictions, slice_data)
                return
            else:
                self.__driveInValidNonFinishedOrder(symbol)
        # do mock trading
        self.__onNewTick(symbol, predictions, slice_data)
        self.__onPredictUpdated(symbol, predictions, slice_data)

    #  判断这笔平仓订单是否在一档盘口及以内
    #  如果订单inValid，则return False，需要撤单
    #  如果订单Valid，则return True，不需要撤单
    def __isOrderValid(self, symbol, slice_data):
        exchangeOrder = self.__positionManager.getNonFinishedOrder(symbol)
        price = exchangeOrder.setPrice
        ask1 = slice_data.askPrice[0]
        bid1 = slice_data.bidPrice[0]
        if self.__getOrderSide(exchangeOrder.BSFlag) == OrderSide.Sell and price > ask1:
            return False
        elif self.__getOrderSide(exchangeOrder.BSFlag) == OrderSide.Buy and price < bid1:
            return False
        else:
            return True

    def __driveInValidNonFinishedOrder(self, symbol):
        exchangeOrder = self.__positionManager.getNonFinishedOrder(symbol)
        exchangeOrder = self.__exchangeHouse.back(exchangeOrder.orderNumber)
        self.__orderFinished(exchangeOrder)

    # this method will now be called as every tick comes, to update tick info
    def __onNewTick(self, symbol, predictions, slice_data):
        self.__signalExecutor.updatePredictInfo(predictions, slice_data)

    def __onPredictUpdated(self, symbol, predictions, slice_data):
        if self.__positionManager.isPositionClosed(symbol):
            self.__outputMgr.registerOutput(symbol, slice_data.timeStamp)  # 平仓状态，outputMgr负责生成order统计
            self.__allowOpenNew(symbol, predictions, slice_data)
        elif self.__positionManager.isPositionPositive(symbol):
            self.__processPositivePosition(symbol, predictions, slice_data)
        elif self.__positionManager.isPositionNegative(symbol):
            self.__processNegativePosition(symbol, predictions, slice_data)

    def __allowOpenNew(self, symbol, predictions, slice_data):
        if self.__isOpenLong(symbol, predictions, slice_data):
            self.__processOpenSignal(symbol, OrderSide.Buy, slice_data)
        elif self.__isOpenShort(symbol, predictions, slice_data):
            self.__processOpenSignal(symbol, OrderSide.Sell, slice_data)

    def __processPositivePosition(self, symbol, predictions, slice_data):
        if self.__isCloseLong(symbol, predictions, slice_data) or self.__riskMgr.isStopLoss(symbol) or self.__riskMgr.isInDanger(symbol):
            self.__processCloseSignal(symbol, OrderSide.Sell, slice_data)
        elif self.__isOpenLong(symbol, predictions, slice_data):
            self.__processOpenSignal(symbol, OrderSide.Buy, slice_data)

    def __processNegativePosition(self, symbol, predictions, slice_data):
        if self.__isCloseShort(symbol, predictions, slice_data) or self.__riskMgr.isStopLoss(symbol) or self.__riskMgr.isInDanger(symbol):
            self.__processCloseSignal(symbol, OrderSide.Buy, slice_data)
        elif self.__isOpenShort(symbol, predictions, slice_data):
            self.__processOpenSignal(symbol, OrderSide.Sell, slice_data)

    def __processOpenSignal(self, symbol, side, slice_data):
        price = self.__calPrice(symbol, side, True, slice_data)
        quantity = self.__calQty(symbol, price)
        if quantity <= 0:
            return
        elif quantity < self.__MIN_ORDER_QTY:
            return
        preClosePx = slice_data.previousClosingPrice
        ratio = abs(price / preClosePx - 1.0)
        if ratio >= self.__OPEN_FORBIDDEN:
            return
        self.__placeOrder(symbol, side, price, quantity, True, slice_data.timeStamp)

    def __processCloseSignal(self, symbol, side, slice_data):
        price = self.__calPrice(symbol, side, False, slice_data)
        quantity = self.__calCloseQty(symbol, price)
        self.__placeOrder(symbol, side, price, quantity, False, slice_data.timeStamp)

    def __calCloseQty(self, symbol, price):
        netPosition = abs(self.__positionManager.getNetPosition(symbol))
        # 支持多空翻转操作，support for long-short inverse
        if symbol in self.__exePriceQty and "volume" in self.__exePriceQty.get(symbol):
            volume = int(self.__exePriceQty.get(symbol).get("volume"))
            # TODO
            volume = min(volume, self.__maxTurnoverPerOrder / price)
            if self.__riskMgr.isInDanger(symbol):
                # TODO
                return min(netPosition, self.__maxTurnoverPerOrder / price)
            else:
                if volume > netPosition:
                    # 翻转下单
                    exposure = volume - netPosition
                    maxExposure = self.__maxExposure
                    if maxExposure is None:
                        maxExposure = sys.maxsize
                    exposure = min(exposure, maxExposure / price, self.__maxTurnoverPerOrder / price,
                                   self.__positionManager.getBuyAvailQty(symbol), self.__positionManager.getSellAvailQty(symbol))
                    return int(exposure + netPosition)
                else:
                    return volume
        else:
            # TODO
            return min(netPosition, self.__maxTurnoverPerOrder / price)

    def __calPrice(self, symbol, side, isOpen, slice_data):
        # priceLevel = 1
        # deviation = 0
        if isOpen:
            if side == OrderSide.Buy:
                priceLevel = self.__buyLevel
                deviation = self.__buyDeviation
            else:
                priceLevel = -self.__buyLevel
                deviation = -self.__buyDeviation
        else:
            if side == OrderSide.Buy:
                priceLevel = -self.__sellLevel
                deviation = -self.__sellDeviation
            else:
                priceLevel = self.__sellLevel
                deviation = self.__sellDeviation
        if priceLevel > 0:
            priceList = slice_data.askPrice
        else:
            priceList = slice_data.bidPrice
        price = priceList[abs(priceLevel) - 1]
        # in case that price is zero
        # ask = np.array(slice_data.askPrice)
        # bid = np.array(slice_data.bidPrice)
        # askTemp = ask[ask > 0]
        # bidTemp = bid[bid > 0]
        # if len(askTemp) == 0:
        #     highest = slice_data.bidPrice[0]
        # else:
        #     highest = max(askTemp)
        # if len(bidTemp) == 0:
        #     lowest = slice_data.askPrice[0]
        # else:
        #     lowest = min(bidTemp)

        # use the price given in the signal executor
        if symbol in self.__exePriceQty and "price" in self.__exePriceQty.get(symbol):
            # 指定下单价格
            price = self.__exePriceQty.get(symbol).get("price")
            if price < slice_data.minPrice or price > slice_data.maxPrice:
                price = slice_data.lastPrice
        elif not self.__riskMgr.isStopLoss(symbol) and not self.__riskMgr.isInDanger(symbol):
            # mostly deprecated
            if price < slice_data.minPrice or price > slice_data.maxPrice:
                price = slice_data.lastPrice
            price += deviation
            if price > slice_data.maxPrice:
                price = slice_data.maxPrice
            elif price < slice_data.minPrice:
                price = slice_data.minPrice
        else:  # stop loss in risk manager or price reaches high/low limits
            if side == OrderSide.Buy:
                ask = slice_data.askPrice[0]
                if ask == 0:
                    price = slice_data.maxPrice
                else:
                    price = ask
            else:
                bid = slice_data.bidPrice[0]
                if bid == 0:
                    price = slice_data.minPrice
                else:
                    price = bid

        return round(price, 2)

    def __calQty(self, symbol, price):
        liquidQty = sys.maxsize
        if symbol in self.__exePriceQty and "volume" in self.__exePriceQty.get(symbol):
            if self.__maxExposure is not None:
                liquidQty = self.__maxExposure / price
            else:
                liquidQty = sys.maxsize
            availSpace = int(liquidQty - abs(self.__positionManager.getNetPosition(symbol)))
            volume = self.__exePriceQty.get(symbol).get("volume")
            quantity = min(availSpace, volume, self.__maxTurnoverPerOrder / price,
                           self.__positionManager.getBuyAvailQty(symbol),
                           self.__positionManager.getSellAvailQty(symbol))
        else:
            if self.__maxExposure is not None:
                liquidQty = min(liquidQty, self.__maxExposure / price)
            availSpace = int(liquidQty - abs(self.__positionManager.getNetPosition(symbol)))
            quantity = min(availSpace, self.__maxTurnoverPerOrder / price,
                           self.__positionManager.getInitialQty(symbol) * self.__maxRatePerOrder,
                           self.__positionManager.getBuyAvailQty(symbol),
                           self.__positionManager.getSellAvailQty(symbol))
        return int(math.floor(quantity / 100) * 100)

    def __placeOrder(self, symbol, side, price, quantity, isOpen, timeStamp):
        dateTime = dt.datetime.fromtimestamp(timeStamp)
        # 若在禁止开仓时刻之后，且为开仓单，则不再开仓。平仓单不受影响
        if (dateTime.time() < self.__START_OPEN_TIME or dateTime.time() >= self.__LAST_OPEN_TIME) and isOpen:
            return

        if quantity == 0:
            return

        if side == OrderSide.Buy:
            sideStr = 'B'
        else:
            sideStr = 'S'
        order = Order(symbol, None, price, quantity, sideStr, dateTime)
        orderNo = self.__exchangeHouse.send(order)
        self.__orderInfo.update({symbol: OrderInfo(orderNo, isOpen)})

    def __makeOrder(self, symbol, slice_data):
        if symbol not in self.__orderInfo or self.__orderInfo.get(symbol) is None:
            return
        orderInfo = self.__orderInfo.get(symbol)
        orderNo = orderInfo.orderNo
        if orderNo is None:
            self.__orderInfo.pop(symbol, None)
            return

        isOpen = orderInfo.isOpen
        currTime = slice_data.time
        currTimeStamp = slice_data.timeStamp
        exchangeOrder = self.__exchangeHouse.drive(orderNo,
                                                   self.__getDriveTime(symbol, isOpen, currTime, currTimeStamp))
        if exchangeOrder.orderNumber is None or exchangeOrder is None:
            self.__orderInfo.pop(symbol, None)
            return

        # 开仓单必撤，平仓单需要在下一个Tick（当前）检查盘口
        # if isOpen:
        exchangeOrder = self.__exchangeHouse.back(exchangeOrder.orderNumber)
        self.__orderFinished(exchangeOrder)
        # else:
        #     if self.__isOrderFinished(exchangeOrder):
        #         self.__orderFinished(exchangeOrder)
        #     else:
        #         self.__positionManager.updatePosition(exchangeOrder)

    def __isNewDay(self, symbol, curr_timeStamp):
        flag = False
        if len(self.__preTagInfo) == 0 or symbol not in self.__preTagInfo:
            flag = True
        elif dt.datetime.fromtimestamp(curr_timeStamp).date() != dt.datetime.fromtimestamp(
                self.__preTagInfo.get(symbol).timeStamp).date():
            flag = True
        return flag

    def __comingNewDay(self, symbol, slice_data):
        preClosePrice = slice_data.previousClosingPrice
        initQty = math.floor(self.__initQty / 100) * 100 - 100
        self.__signalExecutor.resetNewDay()
        self.__riskMgr.resetNewDay()
        self.__positionManager.initPosition(symbol, initQty)
        self.__pre_net_position.update({symbol: 0})
        self.__outputMgr.clearNonClosed(symbol)
        self.__outputMgr.addOneDay(symbol)
        self.__orderInfo.pop(symbol, None)

    def __split_reversed_cum_qty(self, last_net_position, net_position):
        if last_net_position * net_position < 0:
            return abs(last_net_position), abs(net_position)
        else:
            return None

    def __orderFinished(self, exchangeOrder):
        self.__orderInfo.pop(exchangeOrder.code, None)
        # self.__outputMgr.addOrder(exchangeOrder)
        # do not change the sequence!
        self.__positionManager.updatePosition(exchangeOrder)
        net_position = self.__positionManager.getNetPosition(exchangeOrder.code)
        self.__outputMgr.addOrder(exchangeOrder, self.__split_reversed_cum_qty(self.__pre_net_position.get(exchangeOrder.code), net_position))
        self.__riskMgr.updateCost(exchangeOrder, self.__positionManager.getNetPosition(exchangeOrder.code))
        self.__pre_net_position.update({exchangeOrder.code: net_position})

    def __isOpenLong(self, symbol, predictions, slice_data):
        result = self.__signalExecutor.isOpenLong(predictions, slice_data)
        return self.__checkExecutorOutput(symbol, result)

    def __isOpenShort(self, symbol, predictions, slice_data):
        result = self.__signalExecutor.isOpenShort(predictions, slice_data)
        return self.__checkExecutorOutput(symbol, result)

    def __isCloseLong(self, symbol, predictions, slice_data):
        result = self.__signalExecutor.isCloseLong(predictions, slice_data)
        return self.__checkExecutorOutput(symbol, result)

    def __isCloseShort(self, symbol, predictions, slice_data):
        result = self.__signalExecutor.isCloseShort(predictions, slice_data)
        return self.__checkExecutorOutput(symbol, result)

    # the returned value of signalExecutor may be one of three types
    # check SignalExecutorBase for more detailed info
    def __checkExecutorOutput(self, symbol, result):
        self.__exePriceQty.pop(symbol, None)
        # please do not change the sequence below!!
        if result is None:
            return False
        elif isinstance(result, bool):
            if result:
                return True
            else:
                return False
        elif isinstance(result, dict):
            self.__exePriceQty.update({symbol: result})
            return True

    def __processMarketClose(self, symbol, slice_data):
        if self.__positionManager.hasNonFinished(symbol):
            exchangeOrder = self.__positionManager.getNonFinishedOrder(symbol)
            exchangeOrder = self.__exchangeHouse.back(exchangeOrder.orderNumber)
            self.__orderFinished(exchangeOrder)
        if not self.__positionManager.isPositionClosed(symbol):
            self.__closePositionAtMarketClose(symbol, slice_data)

    # 如果当天收盘还有头寸未平，则fake一个ExchangeOrder，以市价盘口的思路去平仓
    # 如果十档内的量，能全部撮合，则价格为加权价格
    # 如果十档内的量，不能全部撮合，则价格为第十档价格
    def __closePositionAtMarketClose(self, symbol, slice_data):
        dateTime = dt.datetime.fromtimestamp(slice_data.timeStamp)
        netPosition = self.__positionManager.getNetPosition(symbol)
        price, accAmount = self.__calMarketCloseData(netPosition, slice_data)
        if netPosition > 0:
            quantity = netPosition
            sideStr = 'S'
        else:
            quantity = -netPosition
            sideStr = 'B'

        order = Order(symbol, None, price, quantity, sideStr, dateTime)
        orderNo = self.__exchangeHouse.send(order)
        exchangeOrder = None
        # fake an exchange order
        if orderNo is not None:
            exchangeOrder = self.__exchangeHouse.drive(orderNo, 0)
        if orderNo is None or exchangeOrder is None:
            exchangeOrder = ExchangeOrder(order)
        if exchangeOrder.setVolume != exchangeOrder.volume:
            exchangeOrder.volume = int(quantity)
            exchangeOrder.accMount = accAmount
            exchangeOrder.isback = True
        self.__orderFinished(exchangeOrder)
        self.__outputMgr.registerOutput(symbol, slice_data.timeStamp)

    def __getDriveTime(self, symbol, isOpen, currTime, currTimeStamp):
        preTime = self.__preTagInfo.get(symbol).time
        preTimeStamp = self.__preTagInfo.get(symbol).timeStamp
        timeSpan = self.__timeSpan(symbol, preTime, preTimeStamp, currTime, currTimeStamp)
        if isOpen:
            if timeSpan >= self.__openWithdrawSeconds:
                return self.__openWithdrawSeconds
            else:
                return timeSpan
        else:
            return timeSpan

    def __validTradingTime(self, currTime):
        if currTime < self.__MARKET_CLOSE:
            return True
        else:
            return False

    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    # helper functions
    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    def __returnTradings(self, symbol):
        tradingOrder = {}
        tradingOrder.update({"order": self.__outputMgr.getOrder(symbol)})
        tradingOrder.update({"preCostProfit": self.__outputMgr.getProfit(symbol)})
        tradingOrder.update({"cumOpenAmount": self.__outputMgr.getCumOpenAmount(symbol)})
        tradingOrder.update({'detailedOrders': self.__outputMgr.getDetailedOrder(symbol)})
        tradingOrder.update({"longTriggerRatio": self.__signalExecutor.getLongTriggerRatio()})
        tradingOrder.update({"longCloseRatio": self.__signalExecutor.getLongCloseRatio()})
        tradingOrder.update({"longCloseRiskRatio": self.__signalExecutor.getLongCloseRiskRatio()})
        tradingOrder.update({"shortTriggerRatio": self.__signalExecutor.getShortTriggerRatio()})
        tradingOrder.update({"shortCloseRatio": self.__signalExecutor.getShortCloseRatio()})
        tradingOrder.update({"shortCloseRiskRatio": self.__signalExecutor.getShortCloseRiskRatio()})
        tradingOrder.update({"preCostDailyProfit": self.__outputMgr.getDailyProfitDict(symbol)})
        tradingOrder.update({"afterCostDailyProfit": self.__outputMgr.getAfterCostDailyProfitDict(symbol)})
        tradingOrder.update({"dailyOpenAmount": self.__outputMgr.getDailyOpenAmountDict(symbol)})
        tradingOrder.update({"dayCounts": self.__outputMgr.getDayCounts(symbol)})
        tradingOrder.update({'dailyCancelledRatio': self.__outputMgr.getDailyCancelledRatio(symbol)})
        tradingOrder.update({'cancelledRatio': self.__outputMgr.getSumCancelledRatio(symbol)})
        return tradingOrder

    def __isOrderFinished(self, exchangeOrder):
        status = exchangeOrder.order_state()
        if status == 'cancelled' or status == 'filled' or status == 'partially_cancelled':
            return True
        else:
            return False

    def __reset_init_amount(self, signals: pd.DataFrame):
        self.__initAmount = None
        try_times = 20
        for i in range(try_times):
            timestamp = signals.iloc[i, 0]
            if timestamp in self.__data_dict:
                base_price = self.__data_dict[timestamp].previousClosingPrice
                self.__initAmount = base_price * self.__initQty
                break
        if self.__initAmount is None:
            raise Exception('{}: {} Initialize amount failed! The first '.format(self.__symbol, timestamp) + str(try_times) + ' timestamps are not in the Data.pickle')

    def __calMarketCloseData(self, netPosition, last_slice_data):
        if netPosition > 0:
            priceList = last_slice_data.bidPrice
            volumeList = last_slice_data.bidVolume
        else:
            priceList = last_slice_data.askPrice
            volumeList = last_slice_data.askVolume

        absPosition = abs(netPosition)
        accVolume = 0
        accAmount = 0
        for i in range(len(priceList)):
            temp = accVolume
            temp += volumeList[i]
            if temp >= absPosition:
                rest = absPosition - accVolume
                accAmount += rest * priceList[i]
                accVolume = absPosition
                break
            else:
                accVolume += volumeList[i]
                accAmount += volumeList[i] * priceList[i]
        if accVolume < absPosition:
            price = priceList[-1]
            if price == 0:
                for k in range(len(priceList) - 1, -1, -1):
                    if priceList[k] != 0:
                        price = priceList[k]
                if price == 0:
                    if netPosition > 0:
                        price = last_slice_data.askPrice[0]
                    else:
                        price = last_slice_data.bidPrice[0]
            accAmount = price * absPosition
            return price, accAmount
        else:
            price = accAmount / accVolume
            if netPosition > 0:
                return round(math.floor(price * 100) / 100, 2), accAmount
            else:
                return round(math.ceil(price * 100) / 100, 2), accAmount

    def __getOrderSide(self, BSFlag):
        if BSFlag == 'B':
            return OrderSide.Buy
        else:
            return OrderSide.Sell

    def __timeSpan(self, symbol, preTime, preTimeStamp, currTime, currTimeStamp):
        # startTime = self.__inTimeRange(preTime)
        # endTime = self.__inTimeRange(currTime)
        # if startTime == TimeRange.Morning and endTime == TimeRange.Afternoon:
        #     value = currTimeStamp - preTimeStamp - self.__noonRange.get(symbol)
        #     return value
        # else:
        return currTimeStamp - preTimeStamp

    def __inTimeRange(self, t):  # e.g. t = 93003000
        if t < self.__NOON:
            return TimeRange.Morning
        else:
            return TimeRange.Afternoon

    def __setNoonRange(self, symbol, slice_data):
        curr_time = slice_data.time
        curr_timeStamp = slice_data.timeStamp
        if symbol not in self.__preTagInfo:
            return
        if self.__inTimeRange(self.__preTagInfo.get(symbol).time) == TimeRange.Morning \
                and self.__inTimeRange(curr_time) == TimeRange.Afternoon:
            value = curr_timeStamp - self.__preTagInfo.get(symbol).timeStamp
            self.__noonRange.update({symbol: value})


class OrderInfo:
    def __init__(self, orderNo, isOpen):
        self.orderNo = orderNo
        self.isOpen = isOpen


class TimeRange(Enum):
    Morning = 0
    Afternoon = 1
    # Invalid = 2
