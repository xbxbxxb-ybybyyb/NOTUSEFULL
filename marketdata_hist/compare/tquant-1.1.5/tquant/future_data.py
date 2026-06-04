# _*_ coding:utf-8 _*_
from MDCDataProvider.futuredata import FutureDataDP
from FactorProvider.futuredata import FutureDataFP

from tquant.utils.event_trace import EventTrace, event_trace


class FutureData:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            return cls.__instance
        else:
            obj = object.__new__(cls, *args, **kwargs)
            cls.__instance = obj
            cls.__instance.__initialized = False
            return cls.__instance

    @event_trace
    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        self.dp = FutureDataDP()
        self.fd = FutureDataFP()

    @event_trace
    def get_future_tick(self, symbol, start_time, end_time):
        """
        获取期货行情tick数据
        :param symbol: 合约名称 普通合约：IC2012.CF  主力合约：IC00.CF. 次主力合约：IC01.CF 连三合约：IC03.CF 连四合约：IC04.CF
        :param start_time: 起始日期，string类型，如'20190102 000000000'
        :param end_time: 终止日期，string类型，如'20190102 235900000'
        :return:
        """
        return self.dp.get_future_data(symbol, start_time, end_time, 'TICK',  method=False, contract_type='ZL00')

    @event_trace
    def get_future_kline(self, symbol, start_time, end_time):
        """
        获取期货行情kline数据
        :param symbol: 合约名称 普通合约：IC2012.CF  主力合约：IC00.CF. 次主力合约：IC01.CF 连三合约：IC03.CF 连四合约：IC04.CF
        :param start_time: 起始日期，string类型，如'20190102 000000000'
        :param end_time: 终止日期，string类型，如'20190102 235900000'
        :param bar_size: 数据周期枚举类，支持1day('K_DAY'), 1min('K_1MIN')
        :return:
        """
        # if bar_size not in ['K_DAY', 'K_1MIN']:
        #     raise Exception('该接口仅支持K_DAY, K_1MIN')
        return self.dp.get_future_data(symbol, start_time, end_time, bar_size='K_1MIN', method=False, contract_type='ZL00')

    @event_trace
    def get_instrument_info(self, symbol):
        """
        获取任一期货合约的具体属性
        :param symbol: 期货合约代码或品种代码
        :return:
        注：symbol为品种的时候返回的是最新的一个合约的基本信息
        """
        df = self.fd.get_futures_cont_info(symbol)
        return df

    @event_trace
    def get_instrument_all(self, symbol, start_date, end_date):
        """
        获取某一个期货品种在时间区间内的所有合约列表
        :param symbol:合约品种符号，如rb, cu等，为字符串
        :param start_date:起始日期 int或str 如20170101或'20170101'
        :param end_date:终止日期 int或str 如20190702或'20190702'
        :return:返回指定时间区间内，所有的合约列表。(按日期从近到远排列）
        """
        df = self.fd.get_instrument_all(symbol, start_date, end_date)
        return df

    @event_trace
    def get_contract_zl_info(self, symbol, start_date, end_date, contract_type):
        """
        获取指定日期区间、品种的主力合约的信息
        :param symbol:合约品种符号，如rb, cu等，为字符串
        :param start_date:开始日期，str类型，如'20190702'
        :param end_date:结束日期，str类型，如'20190703'
        :param contract_type:合约类型，主力合约为'ZL00'，次主力合约为'ZL01'
        :return:
        """
        df = self.fd.get_contract_zl_info(symbol, start_date, end_date, contract_type)
        return df
