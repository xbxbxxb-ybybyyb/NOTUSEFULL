import datetime as dt
from copy import deepcopy
from typing import Dict
from System.SliceData_BTCV import SliceData
from abc import abstractmethod


class SignalExecutorBase:
    def __init__(self, positionMgr):
        self._positionMgr = positionMgr
        self._data_dict: Dict[float, 'SliceData'] = None
        self.__placeOrder = None  # Callable from SE
        self.__cancelOrder = None  # Callable from SE

    def hookFuncs(self, placeOrder, cancelOrder):
        self.__placeOrder = placeOrder
        self.__cancelOrder = cancelOrder

    @abstractmethod
    def generateTriggerRatio(self, symbol, trigger_ratio_dict):
        pass

    @abstractmethod
    def set_json_param_before_start(self, param):
        pass

    @abstractmethod
    def onNewDay(self, date: dt.datetime.date):
        pass

    @abstractmethod
    def onNewTick(self, predictions, slice_data, unfinished_order, **kwargs):
        pass

    @abstractmethod
    def onTimeEnd(self, predictions, slice_data, curr_dt: dt.datetime):
        """
        暂定！
        每分钟的第59秒会触发此回调
        如果某Tick恰好为59秒，则先触发onNewTick，再触发onNewTime，策略自行处理
        predictions: 上一个最近Tick的信号值
        slice_data: 上一个最近Tick的行情（里面的time和timeStamp均未作修改）
        curr_dt: “当前”时间戳，为该分钟第59秒，即dt.datetime(year, month, day, hour, minute, 59)
        """
        pass

    def placeOrder(self, symbol, side, price, quantity, timeStamp, signalType, **kwargs):
        """
        下单api
        当前Tick完成下单后，会在下一个Tick到达时，尝试撮合
        如果撮合令订单终结，则回调onOrderUpdated；不终结，则不会回调onOrderUpdated，策略可以另行cancelOrder
        尝试撮合完成后，才会调用onNewTick
        """
        return self.__placeOrder(symbol, side, price, quantity, timeStamp, signalType, **kwargs)

    def cancelOrder(self, orderNumber):
        """
        撤单api
        撤单api是瞬时返回的，会令订单终结，从而回调onOrderUpdated
        即，在当前Tick调用完cancelOrder后，处理完onOrderUpated后，可以立即执行在cancelOrder之后的所有其他代码
        """
        self.__cancelOrder(orderNumber)

    @abstractmethod
    def onOrderUpdated(self, exchangeOrder):
        """
        订单已经是终结状态
        PositionManager的头寸已经更新
        """
        pass

    # @abstractmethod
    # def getLongTriggerRatio(self):
    #     pass
    #
    # @abstractmethod
    # def getShortTriggerRatio(self):
    #     pass

    def set_data_dict(self, data_dict: Dict[float, 'SliceData']):
        self._data_dict = data_dict

    def next_slice_data_speed(self, curr_slice_data):
        """
        该方法为加速版本，使用curr_slice_data自带的next timestamp
        如果next timestamp跟现在的timestamp相差大于3秒，则使用现在的slice data
        :param curr_slice_data: SliceData
        :return: SliceData
        """
        timestamp = curr_slice_data.timeStamp
        next_timestamp = curr_slice_data.nextTimeStamp
        if next_timestamp - timestamp < 6:
            next_slice_data = deepcopy(self._data_dict[next_timestamp])
            next_slice_data.timeStamp = timestamp
            next_slice_data.nextTimeStamp = next_timestamp
            next_slice_data.time = int(dt.datetime.fromtimestamp(timestamp).strftime("%H%M%S")) * 1000
            return next_slice_data
        else:
            return curr_slice_data
