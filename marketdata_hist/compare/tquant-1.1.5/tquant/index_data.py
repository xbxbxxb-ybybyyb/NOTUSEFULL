# _*_ coding:utf-8 _*_

from FactorProvider.factordata import xqfactor as xqf
from MDCDataProvider.indexdata import IndexDataDP
from tquant.utils.event_trace import EventTrace, event_trace



class IndexData:
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
        self.index_dp = IndexDataDP()

    @event_trace
    def get_index_info(self, date_time, plate_id, weight_type=0, use_prev_name=True):
        """
        查询指数板块的成分股及成分股的权重
        :param date_time:查询日期，格式yyyymmdd,例如:'20100801'
        :param plate_id:指数代码,如：'HS300'，详见参数说明；
        :param weight_type: int，取值0表示当天权重，1表示次日权重，默认为0
        :param use_prev_name:获取成分股名称为指定的日期时的名称或最新名称，默认True为指定的日期时的名称
        :return:

        参数说明：
        - plate_id 指数代码

        ========   ==============  ==============
        类型名称   类型说明         数据开始日期
        HS300      沪深300指数      20050411
        ZZ500     中证500指数       20100104
        SH50       上证50指数       20100104
        ========  =============   ==============
        """
        plate_type = 'INDEX'
        df = xqf.hset(plate_type, date_time, plate_id, weight_type, use_prev_name)
        return df

    @event_trace
    def get_index_tick(self, trading_code, start_datetime, end_datetime,
                       trading_phase_code=[]):
        """
        证券Tick查询服务: 根据证券ID查询一段时间范围内的Tick数据,支持指数数据查询
        :param trading_code: string，单支指数代码，如："000300.SH"
        :param start_datetime:string，开始时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180301 093000000'
        :param end_datetime:string，结束时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180305 150000250'
        :param trading_phase_code:list，取哪些市场阶段状态，默认取所有。
                                所需的交易阶段代码('0'表示开盘前，启动。'1'表示开盘集合竞价。
                                '2'表示开盘集合竞价阶段结束到连续竞价阶段开始之前。'3'表示连续竞价。
                                '4'表示中午休市。'5'表示收盘集合竞价。'6'表示已闭市。'7'表示盘后交易（实际未使用）)
        :return:DataFrame
        注意：按时间范围读取数据有最大范围限制，最长不能超过180天
        """
        df = self.index_dp.get_index_data(trading_code, start_datetime,
                                          end_datetime, 'Index',
                                          trading_phase_code)
        return df

    @event_trace
    def get_index_kline(self, trading_code, start_datetime, end_datetime):
        """
        证券K线查询服务:根据指数代码查询一段时间范围内的K线数据, 返回DataFrame对象
        :param trading_code: string，单支股票代码，如："000300.SH"
        :param start_datetime:string，开始时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180301 093000000'
        :param end_datetime:string，结束时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180305 150000250'
        :param k_type: int，k线时间间隔类型
        :return: DataFrame
        注意：按时间范围读取数据有最大范围限制，最长不能超过180天
        """
        df = self.index_dp.get_index_data(trading_code, start_datetime,
                                          end_datetime, 'Kline1M4ZT')
        return df
