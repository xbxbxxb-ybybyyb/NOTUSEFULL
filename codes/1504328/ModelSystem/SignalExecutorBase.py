from typing import List, Dict
from DataIO.SliceData import SliceData


class SignalExecutorBase:
    def __init__(self, positionMgr, riskMgr, counterMgr):
        self._positionMgr = positionMgr
        self._riskMgr = riskMgr
        self._counterMgr = counterMgr
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

