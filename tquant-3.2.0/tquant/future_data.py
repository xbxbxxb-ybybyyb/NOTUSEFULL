# _*_ coding:utf-8 _*_
import pandas as pd
from MDCDataProvider.futuredata import FutureDataDP
from MDCDataProvider.futuredata.future_data import FutureDataDP as MDCFutureDataDP
from FactorProvider.futuredata import FutureDataFP
from MDCDataProvider.DataProvider_ini import get_dataprovider

from tquant.utils.event_trace import EventTrace, event_trace


class FutureData:
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
        # self.future_dp = FutureDataDP()
        # self.future_fd = FutureDataFP()
        self.future_dp = None
        self.future_mdc_dp = None
        self.future_fp = None

    def __set_futuredatadp(self):
        if not self.future_dp:
            self.future_dp = FutureDataDP()

    def __set_futuremdcdp(self):
        if not self.future_mdc_dp:
            self.future_mdc_dp = MDCFutureDataDP()

    def __set_futuredatafp(self):
        if not self.future_fp:
            self.future_fp = FutureDataFP()

    @event_trace
    def get_future_tick(self, symbol, start_time, end_time, use_legacy_data=False):
        """
        获取期货行情tick数据
        :param symbol: 合约名称 普通合约：IC2012.CF  主力合约：IC00.CF. 次主力合约：IC01.CF 连三合约：IC03.CF 连四合约：IC04.CF
        :param start_time: 起始日期，string类型，如'20190102 000000000'
        :param end_time: 终止日期，string类型，如'20190102 235900000'
        :return:
        """
        if use_legacy_data:
            self.__set_futuredatadp()
            df = self.future_dp.get_future_data(
                    symbol, start_time, end_time, 'TICK')
            return df
        df = pd.DataFrame()
        for dp_type, dp_values in get_dataprovider('future', 'TICK', start_time, end_time).items():
            if dp_type == 'mdc_dp':
                self.__set_futuremdcdp()
                df = df.append(self.future_mdc_dp.get_future_data(symbol,
                    dp_values['start_time'], dp_values['end_time'],
                    'TICK'))
            else:
                self.__set_futuredatadp()
                df = df.append(self.future_dp.get_future_data(
                    symbol, dp_values['start_time'], dp_values['end_time'], 'TICK'))
        return df

    @event_trace
    def get_future_kline(self, symbol, start_time, end_time, k_type='K_1MIN', use_legacy_data=False):
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
        if use_legacy_data:
            df = self.future_dp.get_future_data(symbol, start_time, end_time, k_type)
            return df
        df = pd.DataFrame()
        for dp_type, dp_values in get_dataprovider('future', k_type, start_time, end_time).items():
            if dp_type == 'mdc_dp':
                self.__set_futuremdcdp()
                df = df.append(self.future_mdc_dp.get_future_data(symbol, dp_values['start_time'],
                                                                  dp_values['end_time'], k_type))
            else:
                self.__set_futuredatadp()
                df = df.append(self.future_dp.get_future_data(symbol,
                    dp_values['start_time'], dp_values['end_time'], k_type))
        return df

    @event_trace
    def get_instrument_info(self, symbol):
        """
        获取任一期货合约的具体属性
        :param symbol: 期货合约代码或品种代码
        :return:
        注：symbol为品种的时候返回的是最新的一个合约的基本信息
        """
        self.__set_futuredatafp()
        df = self.future_fp.get_futures_cont_info(symbol)
        return df

    @event_trace
    def get_instrument_all(self, symbol, start_date, end_date):
        """
        获取某一个期货品种在时间区间内的所有合约列表
        :param symbol:合约品种符号，如RB, CU等，为字符串，ALL表示所有期货品种
        :param start_date:起始日期 int或str 如20170101或'20170101'
        :param end_date:终止日期 int或str 如20190702或'20190702'
        :return:返回指定时间区间内，所有的合约列表；如果是ALL，返回字典，key是品种，value是合约列表。(按日期从远到近排列）
        """
        self.__set_futuredatafp()
        df = self.future_fp.get_instrument_all(symbol, start_date, end_date)
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
        self.__set_futuredatafp()
        df = self.future_fp.get_contract_zl_info(symbol, start_date, end_date, contract_type)
        return df

    @event_trace
    def get_future_data_day(self, exchange_house, date, bar_size,
                            trading_phase_code=None,
                            sort_by_receive_time=False):
        self.__set_futuremdcdp()
        df = self.future_mdc_dp.get_future_data_by_day(
            bar_size=bar_size, date=date,
            exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df

    @event_trace
    def get_future_tick_by_exchange(self, exchange_house, date,
                                    trading_phase_code=None,
                                    sort_by_receive_time=False):
        self.__set_futuremdcdp()
        df = self.future_mdc_dp.get_future_data_by_day(
            bar_size='tick',
            date=date, exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df

    @event_trace
    def get_future_kline_by_exchange(self, exchange_house, date, bar_size,
                                     trading_phase_code=None,
                                     sort_by_receive_time=False):
        bar_size = bar_size.lower()
        if bar_size not in ['k_day', 'k_1min', 'k_5min', 'k_10min', 'k_60min']:
            raise Exception('bar_size必须在k_1min,k_5min,k_10min,k_60min中')
        self.__set_futuremdcdp()
        df = self.future_mdc_dp.get_future_data_by_day(
            bar_size=bar_size,
            date=date, exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df
