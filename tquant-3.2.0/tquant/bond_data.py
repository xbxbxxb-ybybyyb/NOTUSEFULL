# _*_ coding:utf-8 _*_
import pandas as pd
from MDCDataProvider.bonddata import BondDataDP
from MDCDataProvider.bonddata.bond_data import BondDataDP as MDCBondDataDP
from MDCDataProvider.DataProvider_ini import get_dataprovider
from FactorProvider.bonddata import BondDataFP

from tquant.utils.event_trace import EventTrace, event_trace



class BondData:
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
        # self.bond_dp = BondDataDP()
        # self.bond_fp = BondDataFP()
        self.bond_dp = None
        self.bond_mdc_dp = None
        self.bond_fp = None

    def __set_bonddatadp(self):
        if not self.bond_dp:
            self.bond_dp = BondDataDP()

    def __set_bondmdcdp(self):
        if not self.bond_mdc_dp:
            self.bond_mdc_dp = MDCBondDataDP()

    def __set_bonddatafp(self):
        if not self.bond_fp:
            self.bond_fp = BondDataFP()

    @event_trace
    def get_bond_data(self, symbol, start_time, end_time, bar_size, use_legacy_data=False):
        """
        获取可转债行情数据
        :param symbol: 可转债代码, string类型, 如'123021.SZ'
        :param start_time:起始日期,string类型，如'20190102 000000000'
        :param end_time:终止日期，string类型，如'20190102 235900000'
        :param bar_size:数据周期枚举类，支持1day('K_DAY'), 1min('K_1MIN'), tick('TICK'), order('ORDER'), transaction('TRANSACTION')
        :return:
        """
        if use_legacy_data:
            self.__set_bonddatadp()
            df = self.bond_dp.get_bond_data(
                    symbol, start_time, end_time, bar_size)
            return df
        df = pd.DataFrame()
        for dp_type, dp_values in get_dataprovider('bond', bar_size, start_time, end_time).items():
            if dp_type == 'mdc_dp':
                self.__set_bondmdcdp()
                df = df.append(self.bond_mdc_dp.get_bond_data(symbol,
                    dp_values['start_time'], dp_values['end_time'],
                    bar_size))
            else:
                self.__set_bonddatadp()
                df = df.append(self.bond_dp.get_bond_data(
                    symbol, dp_values['start_time'], dp_values['end_time'], bar_size))
        return df

    @event_trace
    def get_bond_tick(self, symbol, start_time, end_time,
                      use_legacy_data=False):
        """
        获取可转债行情tick数据
        :param symbol: 基金代码, string类型, 如'123021.SZ'
        :param start_time:起始日期,string类型，如'20190102 000000000'
        :param end_time:终止日期，string类型，如'20190102 235900000'
        :return:
        """
        if use_legacy_data:
            self.__set_bonddatadp()
            df = self.bond_dp.get_bond_data(symbol, start_time, end_time,
                'TICK')
            return df
        df = pd.DataFrame()
        for dp_type, dp_values in get_dataprovider('bond', 'TICK', start_time,
                                                   end_time).items():
            if dp_type == 'mdc_dp':
                self.__set_bondmdcdp()
                df = df.append(self.bond_mdc_dp.get_bond_data(symbol,
                                                              dp_values[
                                                                  'start_time'],
                                                              dp_values[
                                                                  'end_time'],
                                                              'TICK'))
            else:
                self.__set_bonddatadp()
                df = df.append(
                    self.bond_dp.get_bond_data(symbol, dp_values['start_time'],
                        dp_values['end_time'], 'TICK'))
        return df

    @event_trace
    def get_bond_kline(self, symbol, start_time, end_time, bar_size,
                       use_legacy_data=False):
        """
        获取可转债行情kline数据
        :param symbol: 基金代码, string类型, 如'123021.SZ'
        :param start_time:起始日期,string类型，如'20190102 000000000'
        :param end_time:终止日期，string类型，如'20190102 235900000'
        :param bar_size:数据周期枚举类，支持1day('K_DAY'), 1min('K_1MIN')
        :return:
        """
        if bar_size not in ['K_DAY', 'K_1MIN', 'K_5MIN', 'K_10MIN', 'K_60MIN']:
            raise Exception('该接口仅支持K_DAY, K_1MIN, K_10MIN, K_60MIN')
        if use_legacy_data:
            self.__set_bonddatadp()
            df = self.bond_dp.get_bond_data(symbol, start_time, end_time,
                bar_size)
            return df
        df = pd.DataFrame()
        for dp_type, dp_values in get_dataprovider('bond', bar_size,
                                                   start_time,
                                                   end_time).items():
            if dp_type == 'mdc_dp':
                self.__set_bondmdcdp()
                df = df.append(self.bond_mdc_dp.get_bond_data(symbol,
                                                              dp_values[
                                                                  'start_time'],
                                                              dp_values[
                                                                  'end_time'],
                                                              bar_size))
            else:
                self.__set_bonddatadp()
                df = df.append(
                    self.bond_dp.get_bond_data(symbol, dp_values['start_time'],
                        dp_values['end_time'], bar_size))
        return df

    @event_trace
    def get_bond_transaction(self, symbol, start_time, end_time,
                             use_legacy_data=False):
        """
        获取可转债行情成交数据
        :param symbol: 基金代码, string类型, 如'123021.SZ'
        :param start_time:起始日期,string类型，如'20190102 000000000'
        :param end_time:终止日期，string类型，如'20190102 235900000'
        :return:
        """
        if use_legacy_data:
            self.__set_bonddatadp()
            df = self.bond_dp.get_bond_data(symbol, start_time, end_time,
                                            'TRANSACTION')
            return df
        df = pd.DataFrame()
        for dp_type, dp_values in get_dataprovider('bond', 'TRANSACTION',
                                                   start_time,
                                                   end_time).items():
            if dp_type == 'mdc_dp':
                self.__set_bondmdcdp()
                df = df.append(self.bond_mdc_dp.get_bond_data(symbol,
                                                              dp_values[
                                                                  'start_time'],
                                                              dp_values[
                                                                  'end_time'],
                                                              'TRANSACTION'))
            else:
                self.__set_bonddatadp()
                df = df.append(
                    self.bond_dp.get_bond_data(symbol, dp_values['start_time'],
                        dp_values['end_time'], 'TRANSACTION'))
        return df

    @event_trace
    def get_bond_order(self, symbol, start_time, end_time,
                       use_legacy_data=False):
        """
        获取可转债行情委托数据
        :param symbol: 基金代码, string类型, 如'123021.SZ'
        :param start_time:起始日期,string类型，如'20190102 000000000'
        :param end_time:终止日期，string类型，如'20190102 235900000'
        :return:
        """
        if use_legacy_data:
            self.__set_bonddatadp()
            df = self.bond_dp.get_bond_data(symbol, start_time, end_time,
                'ORDER')
            return df
        df = pd.DataFrame()
        for dp_type, dp_values in get_dataprovider('bond', 'ORDER', start_time,
                                                   end_time).items():
            if dp_type == 'mdc_dp':
                self.__set_bondmdcdp()
                df = df.append(self.bond_mdc_dp.get_bond_data(symbol,
                                                              dp_values[
                                                                  'start_time'],
                                                              dp_values[
                                                                  'end_time'],
                                                              'ORDER'))
            else:
                self.__set_bonddatadp()
                df = df.append(
                    self.bond_dp.get_bond_data(symbol, dp_values['start_time'],
                        dp_values['end_time'], 'ORDER'))
        return df

    @event_trace
    def get_qb_bond_data(self, symbol, start_time, end_time, bar_size):
        """
        获取QB债券数据
        :param symbol: 可转债代码, string类型, 如'123021.SZ'
        :param start_time:起始日期,string类型，如'20190102 000000000'
        :param end_time:终止日期，string类型，如'20190102 235900000'
        :param bar_size:数据周期枚举类，支持quote('QUOTE'), transaction('TRANSACTION')
        :return:
        """
        self.__set_bonddatadp()
        return self.bond_dp.get_qb_bond_data(symbol, start_time, end_time, bar_size)

    @event_trace
    def get_cfe_bond_data(self, symbol, start_time, end_time, bar_size, fill_cash_bond_quotes=True):
        """
        获取CFE债券数据
        :param symbol: 可转债代码, string类型, 如'123021.SZ'
        :param start_time:起始日期,string类型，如'20190102 000000000'
        :param end_time:终止日期，string类型，如'20190102 235900000'
        :param bar_size:数据周期枚举类，支持tick('TICK') , transaction('TRANSACTION'), quote('QUOTE')
        :param fill_cash_bond_quotes: cash_bond_quotes是否补全空字段，默认为True
        :return:
        """
        self.__set_bonddatadp()
        return self.bond_dp.get_cfe_bond_data(symbol, start_time, end_time, bar_size, fill_cash_bond_quotes)

    @event_trace
    def get_bond_issuance_info(self, symbol):
        """
        获取可转债代码的基本信息
        :param code: 可转债的代码，string类型，如 '125930.SZ'
        :return:
        """
        self.__set_bonddatafp()
        return self.bond_fp.get_bond_issuance_info(symbol)

    @event_trace
    def get_bond_set(self, date, bond_type='kzz'):
        """
        查询指定日期正在发行的可转债列表
        :param date: 查询时间, 类型为string，如 '20200330'
        :param bond_type: 债券类型, 类型为string，默认 'kzz'代表可转债
        :return:
        """
        self.__set_bonddatafp()
        return self.bond_fp.get_bond_set(date, bond_type)

    @event_trace
    def get_bond_data_day(self, exchange_house, date, bar_size,
                          trading_phase_code=None,
                          sort_by_receive_time=False):
        self.__set_bondmdcdp()
        df = self.bond_mdc_dp.get_bond_data_by_day(
            bar_size=bar_size,
            date=date,
            exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df

    @event_trace
    def get_bond_tick_by_exchange(self, exchange_house, date,
                                  trading_phase_code=None,
                                  sort_by_receive_time=False):
        self.__set_bondmdcdp()
        df = self.bond_mdc_dp.get_bond_data_by_day(
            bar_size='tick',
            date=date,
            exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df

    @event_trace
    def get_bond_transaction_by_exchange(self, exchange_house, date,
                                         trading_phase_code=None,
                                         sort_by_receive_time=False):
        self.__set_bondmdcdp()
        df = self.bond_mdc_dp.get_bond_data_by_day(
            bar_size='transaction',
            date=date,
            exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df

    @event_trace
    def get_bond_order_by_exchange(self, exchange_house, date,
                                   trading_phase_code=None,
                                   sort_by_receive_time=False):
        self.__set_bondmdcdp()
        df = self.bond_mdc_dp.get_bond_data_by_day(
            bar_size='order',
            date=date,
            exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df

    @event_trace
    def get_bond_kline_by_exchange(self, exchange_house, date, bar_size,
                                   trading_phase_code=None,
                                   sort_by_receive_time=False):
        bar_size = bar_size.lower()
        if bar_size not in ['k_day', 'k_1min', 'k_5min', 'k_10min', 'k_60min']:
            raise Exception('bar_size必须在k_1min,k_5min,k_10min,k_60min中')
        self.__set_bondmdcdp()
        df = self.bond_mdc_dp.get_bond_data_by_day(
            bar_size=bar_size,
            date=date,
            exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df
