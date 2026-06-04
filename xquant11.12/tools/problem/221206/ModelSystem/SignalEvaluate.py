# -*- coding: utf-8 -*-
"""
Created on 2017/9/26 13:19

@author: 006547
@revise: 006688
"""

import datetime as dt
import importlib
from Exchange.Exchange import Exchange
from Exchange.MarketData import MarketData
from Exchange.Order import Order
from ModelSystem.Util.PositionManager import PositionManager
from ModelSystem.Util.OutputManager import OutputManager
from ModelSystem.Util.OrderSide import OrderSide
# from xquant.compute.sparkmr import remote_print


class SignalEvaluate:
    # temporarily use default initialisation
    def __init__(self, inputs, signal_trigger_pairs):
        # CONSTANTS
        mock_trade_para = inputs.mock_trade_para
        # 从该时刻起，允许开仓。格式为 dt.time(9,30,0)
        self.__START_OPEN_TIME = mock_trade_para["START_OPEN_TIME"]
        # 从该时刻起，禁止开仓，若有仓位，则会依据信号值自然平仓。格式为 dt.time(9,45,0)
        self.__LAST_OPEN_TIME = mock_trade_para["LAST_OPEN_TIME"]
        # 开仓单驱动时间
        self.__OPEN_WITHDRAW_SECONDS = mock_trade_para["OPEN_WITHDRAW_SECONDS"]
        # 计划开仓额度
        self.__TARGET_QUANTITY = mock_trade_para["TARGET_QUANTITY"]
        # 计划开仓额度对应的市值，区间内不变
        self.__TARGET_VALUE = mock_trade_para["TARGET_VALUE"]

        # NonConstants
        self.__symbol = inputs.symbol
        self.__output_path = inputs.output_path_dir
        self.__tick = inputs.tick
        self.__transaction = inputs.transaction
        self.__data_dict = inputs.tick_dict
        self.__signal_trigger_pairs = signal_trigger_pairs

        self.__order_capacity = inputs.json_param
        self.__vwap_df = inputs.vwap_df

        # 头寸管理器
        self.__positionManager = PositionManager()
        self.__positionManager.initPosition(self.__symbol, self.__TARGET_QUANTITY)

        # Signal Executor
        self.__executorStr = inputs.executor_str
        self.__modules = importlib.import_module('ModelSystem.' + inputs.executor_str)
        self.__signalExecutor = getattr(self.__modules, inputs.executor_str)(self.__positionManager)
        self.__hook_executor_funcs()
        self.__signalExecutor.set_data_dict(self.__data_dict)

        # 模拟交易所
        self.__exchangeHouse = Exchange(MarketData(self.__tick, self.__transaction))

        # 结果管理器
        self.__outputMgr = None

        # 如果OPEN_WITHDRAW_SECONDS设置特别大，要经历好几个Tick，则每个Tick都要drive一下，需要重置
        self.__restSeconds = self.__OPEN_WITHDRAW_SECONDS
        self.__pre_slice_data = {}  # key: symbol; value: last slice data
        self.__predictions = []  # list of [long prediction, short prediction]
        self.__nonFinishedOrderNo = None  # (order No., datetime)
        self.__last_order_finished_timestamp = None

    def evaluate(self, show=None):
        self.__signalExecutor.set_json_param_before_start(self.__order_capacity)
        self.runBackTest()
        total, summary = self.__outputMgr.stat()
        if show is not None:
            output_path = self.__output_path + '/result_' + show + '.xlsx'
            self.__outputMgr.to_excel(output_path, self.__signal_trigger_pairs[0][1], (total, summary))
        return {'total': total, 'summary': summary, 'trigger': self.__signal_trigger_pairs[0][1]}

    def runBackTest(self):
        self.__outputMgr = OutputManager(self.__symbol, self.__TARGET_QUANTITY, self.__TARGET_VALUE, self.__vwap_df)

        tick_timestamp_list = list(self.__data_dict.keys())
        tick_timestamp_list.sort()

        for signals_df, trigger_dict in self.__signal_trigger_pairs:
            self.__signalExecutor.generateTriggerRatio(self.__symbol, trigger_dict)

            signals_df = signals_df.set_index("Timestamp")
            signals_dict = signals_df.T.to_dict(orient="list")

            signal_start_datetime = dt.datetime.fromtimestamp(min(signals_dict.keys()))
            signal_end_datetime = dt.datetime.fromtimestamp(max(signals_dict.keys()))
            signal_start_timestamp = dt.datetime.combine(signal_start_datetime.date(), dt.time(0, 0, 0)).timestamp()
            signal_end_timestamp = dt.datetime.combine(signal_end_datetime.date(), dt.time(23, 59, 59)).timestamp()

            for tick_timestamp in tick_timestamp_list:
                if not signal_start_timestamp <= tick_timestamp <= signal_end_timestamp:
                    continue

                slice_data = self.__data_dict[tick_timestamp]

                if tick_timestamp not in signals_dict:
                    predictions = [None, None]
                else:
                    predictions = signals_dict[tick_timestamp]
                self.__predictions.append(predictions)

                if self.__isNewDay(self.__symbol, slice_data.timeStamp):
                    self.__onNewDay(self.__symbol, slice_data)

                self.__updateOrders(slice_data)

                if self.__nonFinishedOrderNo:
                    unfinished_order = self.__exchangeHouse.get_order_status(self.__nonFinishedOrderNo[0])
                else:
                    unfinished_order = None

                self.__onNewTick(predictions, slice_data, unfinished_order)
                self.__pre_slice_data.update({self.__symbol: slice_data})

            if self.__nonFinishedOrderNo is not None:
                order = self.__exchangeHouse.back(self.__nonFinishedOrderNo[0])
                self.__orderFinished(order)

    def __isNewDay(self, symbol, curr_timeStamp):
        flag = False
        if len(self.__pre_slice_data) == 0 or symbol not in self.__pre_slice_data:
            flag = True
        elif dt.datetime.fromtimestamp(curr_timeStamp).date() != dt.datetime.fromtimestamp(
                self.__pre_slice_data.get(symbol).timeStamp).date():
            flag = True
        return flag

    def __onNewDay(self, symbol, slice_data):
        if self.__nonFinishedOrderNo is not None:
            order = self.__exchangeHouse.back(self.__nonFinishedOrderNo[0])
            self.__orderFinished(order)
        date = dt.datetime.fromtimestamp(slice_data.timeStamp).date()
        self.__pre_slice_data = {}
        self.__signalExecutor.onNewDay(date)
        self.__outputMgr.onNewDay(date)
        self.__positionManager.initPosition(symbol, self.__TARGET_QUANTITY)
        self.__last_order_finished_timestamp = None

    def __isNewTime(self, slice_data):
        if self.__symbol not in self.__pre_slice_data:
            return True
        curr_time = int(slice_data.time / 100000)
        pre_time = int(self.__pre_slice_data[self.__symbol].time / 100000)
        if curr_time == pre_time:
            return False
        else:
            return True

    def __onTimeEnd(self):
        if self.__symbol not in self.__pre_slice_data:
            return
        last_dt = dt.datetime.fromtimestamp(self.__pre_slice_data[self.__symbol].timeStamp)
        curr_dt = dt.datetime(last_dt.year, last_dt.month, last_dt.day, last_dt.hour, last_dt.minute, 59)
        self.__signalExecutor.onTimeEnd(self.__predictions[-1], self.__pre_slice_data[self.__symbol], curr_dt)

    def __updateOrders(self, slice_data):
        if self.__nonFinishedOrderNo is not None:
            order = self.__exchangeHouse.get_order_status(self.__nonFinishedOrderNo[0])
            if order.signal_type.name != "aggressive":
                self.__restSeconds += (slice_data.timeStamp
                                       - max(self.__nonFinishedOrderNo[1].timestamp(),
                                             self.__pre_slice_data.get(self.__symbol).timeStamp))

            drive_time = self.__calcDriveTime(self.__symbol, slice_data)
            order = self.__exchangeHouse.drive(self.__nonFinishedOrderNo[0], drive_time)

            if order.order_status == "filled":
                self.__orderFinished(order)
                return

            self.__restSeconds -= drive_time
            if self.__restSeconds <= 0:
                order = self.__exchangeHouse.back(self.__nonFinishedOrderNo[0])
                self.__orderFinished(order)

    def __onNewTick(self, predictions, slice_data, unfinished_order, **kwargs):
        self.__signalExecutor.onNewTick(predictions, slice_data, unfinished_order, **kwargs)

    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    #                                                  Helper Functions
    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    def __hook_executor_funcs(self):
        self.__signalExecutor.hookFuncs(self.__placeOrder, self.__cancelOrder)

    def __placeOrder(self, symbol, side, price, quantity, timeStamp, signalType, **kwargs):
        dateTime = dt.datetime.fromtimestamp(timeStamp)
        # 若在禁止开仓时刻之后，且为开仓单，则不再开仓。平仓单不受影响
        if dateTime.time() < self.__START_OPEN_TIME or dateTime.time() >= self.__LAST_OPEN_TIME:
            return

        if side == OrderSide.Buy.name:
            side_str = 'B'
        else:
            side_str = 'S'

        if self.__last_order_finished_timestamp is None:
            order_timestamp = dateTime.timestamp()
        else:
            order_timestamp = max(dateTime.timestamp(), self.__last_order_finished_timestamp)

        try:
            market_vwap = kwargs["market_vwap"]
        except KeyError:
            market_vwap = None
        try:
            strategy_vwap = kwargs["strategy_vwap"]
        except KeyError:
            strategy_vwap = None
        try:
            ema_volume = kwargs["ema_volume"]
        except KeyError:
            ema_volume = None
        try:
            quote_volume = kwargs["quote_volume"]
        except KeyError:
            quote_volume = None

        order = Order(symbol, price, quantity, side_str, order_timestamp, signalType, market_vwap, strategy_vwap,
                      ema_volume, quote_volume)
        orderNo = self.__exchangeHouse.send(order)

        self.__positionManager.onNewOrder(self.__symbol, orderNo)
        self.__nonFinishedOrderNo = (orderNo, dt.datetime.fromtimestamp(order_timestamp))

        return orderNo

    def __cancelOrder(self, orderNumber):
        exchangeOrder = self.__exchangeHouse.back(orderNumber)
        self.__orderFinished(exchangeOrder)

    def __orderFinished(self, exchangeOrder):
        self.__positionManager.updatePosition(exchangeOrder)
        self.__outputMgr.register(exchangeOrder)
        self.__nonFinishedOrderNo = None
        self.__restSeconds = self.__OPEN_WITHDRAW_SECONDS
        self.__signalExecutor.onOrderUpdated(exchangeOrder)
        self.__last_order_finished_timestamp = exchangeOrder.last_update_time

    def __calcDriveTime(self, symbol, slice_data):
        currTimeStamp = slice_data.timeStamp
        preTimeStamp = self.__pre_slice_data.get(symbol).timeStamp
        orderTimeStamp = self.__nonFinishedOrderNo[1].timestamp()
        sTimeStamp = max(orderTimeStamp, preTimeStamp)
        return min(currTimeStamp - sTimeStamp, self.__restSeconds)

    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
