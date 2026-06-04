# _*_ coding:utf-8 _*_
import pandas as pd
from FactorProvider.factordata import xqfactor as xqf
from FactorProvider.factordata.source_factor_read import get_source_factor_value
from MDCDataProvider.indexdata import IndexDataDP
from MDCDataProvider.indexdata.index_data import IndexDataDP as MDCIndexDataDP
from MDCDataProvider.DataProvider_ini import get_dataprovider
from tquant.utils.event_trace import EventTrace, event_trace


class IndexData:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            return cls.__instance
        else:
            obj = object.__new__(cls)
            cls.__instance = obj
            cls.__instance.__initialized = False
            return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        # self.index_dp = IndexDataDP()
        self.index_dp = None
        self.index_mdc_dp = None

    def __set_indexdatadp(self):
        if not self.index_dp:
            self.index_dp = IndexDataDP()

    def __set_indexmdcdp(self):
        if not self.index_mdc_dp:
            self.index_mdc_dp = MDCIndexDataDP()

    @event_trace
    def get_index_info(self, date_time, plate_id, weight_type=0, use_prev_name=True, weight=True):
        """
        查询指数板块的成分股及成分股的权重
        :param date_time:查询日期，格式yyyymmdd,例如:'20100801'
        :param plate_id:指数代码,如：'HS300'，详见参数说明；
        :param weight_type: int，取值0表示当天权重，1表示次日权重，默认为0
        :param use_prev_name:获取成分股名称为指定的日期时的名称或最新名称，默认True为指定的日期时的名称
        :param weight:bool型，当weight=True时，返回成分股权重，False时不返回，默认为True
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
        df = xqf.hset(plate_type, date_time, plate_id, weight_type, use_prev_name, weight)
        return df

    @event_trace
    def get_index_tick(self, trading_code, start_datetime, end_datetime,
                       trading_phase_code=[], use_legacy_data=False):
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
        if use_legacy_data:
            self.__set_indexdatadp()
            df = self.index_dp.get_index_data(
                    trading_code, start_datetime, end_datetime, 'Index'
                , trading_phase_code=trading_phase_code)
            return df
        df = pd.DataFrame()
        for dp_type, dp_values in get_dataprovider('index', 'Index', start_datetime, end_datetime).items():
            if dp_type == 'mdc_dp':
                self.__set_indexmdcdp()
                df = df.append(self.index_mdc_dp.get_index_data(trading_code,
                    dp_values['start_time'], dp_values['end_time'],
                    'Index', trading_phase_code=trading_phase_code))
            else:
                self.__set_indexdatadp()
                df = df.append(self.index_dp.get_index_data(
                    trading_code, dp_values['start_time'],
                    dp_values['end_time'], 'Index',
                    trading_phase_code=trading_phase_code))
        return df

    @event_trace
    def get_index_kline(self, trading_code, start_datetime, end_datetime, k_type='Kline1M4ZT', use_legacy_data=False):
        """
        证券K线查询服务:根据指数代码查询一段时间范围内的K线数据, 返回DataFrame对象
        :param trading_code: string，单支股票代码，如："000300.SH"
        :param start_datetime:string，开始时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180301 093000000'
        :param end_datetime:string，结束时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180305 150000250'
        :param k_type: int，k线时间间隔类型
        :return: DataFrame
        注意：按时间范围读取数据有最大范围限制，最长不能超过180天
        """
        if use_legacy_data:
            self.__set_indexdatadp()
            df = self.index_dp.get_index_data(trading_code, start_datetime,
                end_datetime, k_type)
            return df
        df = pd.DataFrame()
        for dp_type, dp_values in get_dataprovider('index', k_type, start_datetime, end_datetime).items():
            if dp_type == 'mdc_dp':
                self.__set_indexmdcdp()
                df = df.append(self.index_mdc_dp.get_index_data(trading_code, dp_values['start_time'],
                                                                dp_values['end_time'], k_type))
            else:
                self.__set_indexdatadp()
                df = df.append(self.index_dp.get_index_data(trading_code,
                    dp_values['start_time'], dp_values['end_time'], k_type))
        return df

    @event_trace
    def get_source_factor_value(self, trading_codes, date_list, factor_list, table_name=None, ROLLING_TYPE=['FY2'],
                                CONSEN_DATA_CYCLE_TYP=['263003000'], S_EST_YEARTYPE=['FY2'],
                                S_WRATING_CYCLE=['263003000'], **kwargs):
        """
        查询行业景气度数据源表
        :param stock_list: 股票列表，传[] 查询所有股票
        :param date_list: 日期列表
        :param factor_list: 因子列表
        :param ROLLING_TYPE: 条件，list类型，默认['FY2']，如果为[]则为无筛选条件，返回日期股票的所有数据
        :param CONSEN_DATA_CYCLE_TYP: 条件，list类型，默认['263003000']，如果为[]则为无筛选条件，返回日期股票的所有数据
        :param S_EST_YEARTYPE: 条件，list类型，默认['FY2']，如果为[]则为无筛选条件，返回日期股票的所有数据
        :param S_WRATING_CYCLE: 条件，list类型，默认['263003000']，如果为[]则为无筛选条件，返回日期股票的所有数据
        :return:
        """
        df = get_source_factor_value(trading_codes, date_list, factor_list, table_name, category='index',
                                     ROLLING_TYPE=ROLLING_TYPE,
                                     CONSEN_DATA_CYCLE_TYP=CONSEN_DATA_CYCLE_TYP, S_EST_YEARTYPE=S_EST_YEARTYPE,
                                     S_WRATING_CYCLE=S_WRATING_CYCLE, **kwargs)
        return df

    @event_trace
    def get_index_data_day(self, exchange_house, date, bar_size,
                           trading_phase_code=None,
                           sort_by_receive_time=False):
        self.__set_indexmdcdp()
        df = self.index_mdc_dp.get_index_data_by_day(
            bar_size=bar_size,
            date=date,
            exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df

    @event_trace
    def get_index_by_exchange(self, exchange_house, date,
                              trading_phase_code=None,
                              sort_by_receive_time=False):
        self.__set_indexmdcdp()
        df = self.index_mdc_dp.get_index_data_by_day(
            bar_size='index',
            date=date,
            exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df

    @event_trace
    def get_index_kline_by_exchange(self, exchange_house, date, bar_size,
                                    trading_phase_code=None,
                                    sort_by_receive_time=False):
        bar_size = bar_size.lower()
        if bar_size not in ['kline1m4zt', 'kline5m4zt', 'kline10m4zt', 'kline60m4zt']:
            raise Exception('bar_size必须在kline1m4zt,kline5m4zt,kline10m4zt,kline60m4zt中')
        self.__set_indexmdcdp()
        df = self.index_mdc_dp.get_index_data_by_day(bar_size=bar_size,
            date=date, exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df
