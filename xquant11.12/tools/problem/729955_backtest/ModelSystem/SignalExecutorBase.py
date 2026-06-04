"""
The base class of signal executors
define some interfaces in this dummy class

Please note:
isOpenLong, isOpenShort, isCloseLong, isCloseShort can return 3 types of value:
1. bool: True, False. If True, then processSignal will be called.
2. None: False. ProcessSignal will not be called
3. dict: True. key = "price", "volume". ProcessSignal will be called and the returned value is the order value.

FYI, the outSamplePredict argument is the type of nd array.
It may contains multiple predicts in the parameter.

by 011478
"""
import datetime as dt
from typing import List, Dict
from System.SliceData import SliceData


class SignalExecutorBase:
    def __init__(self, positionMgr, riskMgr):
        self._positionMgr = positionMgr
        self._riskMgr = riskMgr
        self._timestamps: List[float] = None
        self._data_dict: Dict[float, 'SliceData'] = None

    def generateTriggerRatio(self, symbol, trigger_ratio_dict, tickData):
        pass
        
    def set_json_param_before_start(self, param):
        pass

    def resetNewDay(self):
        pass

    def updatePredictInfo(self, predictions, slice_data):
        pass

    def isOpenLong(self, predictions, slice_data):
        pass

    def isOpenShort(self, predictions, slice_data):
        pass

    def isCloseLong(self, predictions, slice_data):
        pass

    def isCloseShort(self, predictions, slice_data):
        pass

    def getLongTriggerRatio(self):
        pass

    def getShortTriggerRatio(self):
        pass

    def set_data_dict(self, data_dict: Dict[float, 'SliceData']):
        self._data_dict = data_dict

    # def set_timestamps(self, timestamps: List[float]):
    #     self._timestamps = timestamps
    #
    # def next_slice_data(self, curr_timestamp: float, index: int, half_day: bool=True) -> 'SliceData':
    #     """
    #     Deprecated
    #     ！！效率太差！！
    #     通过当前slice data的时间戳，获取index个tick后的slice data。
    #     half_day是为了分类处理最后一个tick的情况
    #     half_day为True:  则在next跨中午时，返回上午最后一个tick；在跨日时，返回当天最后一个tick
    #     half_day为False: 则只在next跨日时，返回当天最后一个tick
    #
    #     :param curr_timestamp: 当前slice data的时间戳
    #     :param index: 必须非负数，往后第index个slice data
    #     :param half_day: False: 只在当天最后做处理; True: 每半天做处理。处理的结果是返回最后一个slice data
    #     :return: slice data
    #     """
    #     if index < 0:
    #         raise Exception('Index is negative.')
    #     curr_index = self._timestamps.index(curr_timestamp)
    #     if curr_index < 0:
    #         raise Exception('Cannot find the current timestamp in the list.')
    #     size = len(self._timestamps)
    #     next_index = curr_index + index
    #     if next_index >= size:
    #         timestamp = self._timestamps[-1]
    #         return self._data_dict.get(timestamp, self._data_dict[curr_timestamp])
    #
    #     next_timestamp = self._timestamps[next_index]
    #     curr_date = dt.datetime.fromtimestamp(curr_timestamp).date()
    #     next_date = dt.datetime.fromtimestamp(next_timestamp).date()
    #     if half_day:
    #         curr_dt = dt.datetime.fromtimestamp(curr_timestamp)
    #         next_dt = dt.datetime.fromtimestamp(next_timestamp)
    #         noon = dt.datetime(curr_date.year, curr_date.month, curr_date.day, 12, 0, 0)
    #         if curr_dt < noon:
    #             if next_dt < noon:
    #                 return self._data_dict.get(next_timestamp, self._data_dict[curr_timestamp])
    #             else:  # last tick in the morning
    #                 for i in range(next_index - 1, curr_index - 1, -1):
    #                     timestamp = self._timestamps[i]
    #                     if dt.datetime.fromtimestamp(timestamp) < noon:
    #                         return self._data_dict.get(timestamp, self._data_dict[curr_timestamp])
    #         else:
    #             if curr_date == next_date:
    #                 return self._data_dict.get(next_timestamp, self._data_dict[curr_timestamp])
    #             else:  # last tick on that day
    #                 for i in range(next_index - 1, curr_index - 1, -1):
    #                     timestamp = self._timestamps[i]
    #                     if dt.datetime.fromtimestamp(timestamp).date() == curr_date:
    #                         return self._data_dict.get(timestamp, self._data_dict[curr_timestamp])
    #     else:
    #         if curr_date == next_date:
    #             return self._data_dict.get(next_timestamp, self._data_dict[curr_timestamp])
    #         else:
    #             # 不是同一天，从后往前找第一个跟当前日期相同的slice data
    #             for i in range(next_index - 1, curr_index - 1, -1):  # [curr_index, next_index) reversely
    #                 timestamp = self._timestamps[i]
    #                 if dt.datetime.fromtimestamp(timestamp).date() == curr_date:
    #                     return self._data_dict.get(timestamp, self._data_dict[curr_timestamp])

    def next_slice_data_speed(self, curr_slice_data: 'SliceData') -> 'SliceData':
        """
        该方法为加速版本，使用curr_slice_data自带的next timestamp
        如果next timestamp跟现在的timestamp相差大于3秒，则使用现在的slice data
        :param curr_slice_data:
        :return:
        """
        timestamp = curr_slice_data.timeStamp
        next_timestamp = curr_slice_data.nextTimeStamp
        if next_timestamp - timestamp < 6:
            return self._data_dict[next_timestamp]
        else:
            return curr_slice_data

