# _*_ coding:utf-8 _*_
import pandas as pd
from MDCDataProvider.funddata import FundDataDP
from MDCDataProvider.funddata.fund_data import FundDataDP as MDCFundDataDP
from MDCDataProvider.DataProvider_ini import get_dataprovider
from FactorProvider.funddata import FundDataFP

from tquant.utils.event_trace import EventTrace, event_trace



class FundData:
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
        # self.fund_dp = FundDataDP()
        # self.fund_fp = FundDataFP()
        self.fund_dp = None
        self.fund_mdc_dp = None
        self.fund_fp = None

    def __set_funddatadp(self):
        if not self.fund_dp:
            self.fund_dp = FundDataDP()

    def __set_fundmdcdp(self):
        if not self.fund_mdc_dp:
            self.fund_mdc_dp = MDCFundDataDP()

    def __set_funddatafp(self):
        if not self.fund_fp:
            self.fund_fp = FundDataFP()


    @event_trace
    def get_fund_data(self, symbol, start_time, end_time, bar_size, use_legacy_data=False):
        """
        获取可转债行情数据
        :param symbol: 基金代码, string类型, 如'123021.SZ'
        :param start_time:起始日期,string类型，如'20190102 000000000'
        :param end_time:终止日期，string类型，如'20190102 235900000'
        :param bar_size:数据周期枚举类，支持1day('K_DAY'), 1min('K_1MIN'), tick('TICK'), order('ORDER'), transaction('TRANSACTION')
        :return:
        """
        if use_legacy_data:
            self.__set_funddatadp()
            df = self.fund_dp.get_fund_data(
                    symbol, start_time, end_time, bar_size)
            return df
        df = pd.DataFrame()
        for dp_type, dp_values in get_dataprovider('fund', bar_size, start_time, end_time).items():
            if dp_type == 'mdc_dp':
                self.__set_fundmdcdp()
                df = df.append(self.fund_mdc_dp.get_fund_data(symbol,
                    dp_values['start_time'], dp_values['end_time'],
                    bar_size))
            else:
                self.__set_funddatadp()
                df = df.append(self.fund_dp.get_fund_data(
                    symbol, dp_values['start_time'], dp_values['end_time'], bar_size))
        return df

    @event_trace
    def get_fund_tick(self, symbol, start_time, end_time, use_legacy_data=False):
        """
        获取可转债行情tick数据
        :param symbol: 基金代码, string类型, 如'123021.SZ'
        :param start_time:起始日期,string类型，如'20190102 000000000'
        :param end_time:终止日期，string类型，如'20190102 235900000'
        :return:
        """
        if use_legacy_data:
            self.__set_funddatadp()
            df = self.fund_dp.get_fund_data(
                    symbol, start_time, end_time, 'TICK')
            return df
        df = pd.DataFrame()
        for dp_type, dp_values in get_dataprovider('fund', 'TICK', start_time, end_time).items():
            if dp_type == 'mdc_dp':
                self.__set_fundmdcdp()
                df = df.append(self.fund_mdc_dp.get_fund_data(symbol,
                    dp_values['start_time'], dp_values['end_time'],
                    'TICK'))
            else:
                self.__set_funddatadp()
                df = df.append(self.fund_dp.get_fund_data(
                    symbol, dp_values['start_time'], dp_values['end_time'], 'TICK'))
        return df

    @event_trace
    def get_fund_kline(self, symbol, start_time, end_time, bar_size, use_legacy_data=False):
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
            self.__set_funddatadp()
            df = self.fund_dp.get_fund_data(
                    symbol, start_time, end_time, bar_size)
            return df
        df = pd.DataFrame()
        for dp_type, dp_values in get_dataprovider('fund', bar_size, start_time, end_time).items():
            if dp_type == 'mdc_dp':
                self.__set_fundmdcdp()
                df = df.append(self.fund_mdc_dp.get_fund_data(symbol,
                    dp_values['start_time'], dp_values['end_time'],
                    bar_size))
            else:
                self.__set_funddatadp()
                df = df.append(self.fund_dp.get_fund_data(
                    symbol, dp_values['start_time'], dp_values['end_time'], bar_size))
        return df

    @event_trace
    def get_fund_transaction(self, symbol, start_time, end_time, use_legacy_data=False):
        """
        获取可转债行情成交数据
        :param symbol: 基金代码, string类型, 如'123021.SZ'
        :param start_time:起始日期,string类型，如'20190102 000000000'
        :param end_time:终止日期，string类型，如'20190102 235900000'
        :return:
        """
        if use_legacy_data:
            self.__set_funddatadp()
            df = self.fund_dp.get_fund_data(symbol, start_time, end_time, 'TRANSACTION')
            return df
        df = pd.DataFrame()
        for dp_type, dp_values in get_dataprovider('fund', 'TRANSACTION', start_time, end_time).items():
            if dp_type == 'mdc_dp':
                self.__set_fundmdcdp()
                df = df.append(self.fund_mdc_dp.get_fund_data(symbol,
                    dp_values['start_time'], dp_values['end_time'],
                    'TRANSACTION'))
            else:
                self.__set_funddatadp()
                df = df.append(self.fund_dp.get_fund_data(
                    symbol, dp_values['start_time'], dp_values['end_time'], 'TRANSACTION'))
        return df

    @event_trace
    def get_fund_order(self, symbol, start_time, end_time, use_legacy_data=False):
        """
        获取可转债行情委托数据
        :param symbol: 基金代码, string类型, 如'123021.SZ'
        :param start_time:起始日期,string类型，如'20190102 000000000'
        :param end_time:终止日期，string类型，如'20190102 235900000'
        :return:
        """
        if use_legacy_data:
            self.__set_funddatadp()
            df = self.fund_dp.get_fund_data(
                    symbol, start_time, end_time, 'ORDER')
            return df
        df = pd.DataFrame()
        for dp_type, dp_values in get_dataprovider('fund', 'ORDER', start_time, end_time).items():
            if dp_type == 'mdc_dp':
                self.__set_fundmdcdp()
                df = df.append(self.fund_mdc_dp.get_fund_data(symbol,
                    dp_values['start_time'], dp_values['end_time'],
                    'ORDER'))
            else:
                self.__set_funddatadp()
                df = df.append(self.fund_dp.get_fund_data(
                    symbol, dp_values['start_time'], dp_values['end_time'], 'ORDER'))
        return df

    @event_trace
    def get_fund_issuance_info(self, code):
        """
        获取基金的基本信息
        :param code: 可转债的代码，如 '159901.SZ'
        :return:
        """
        self.__set_funddatafp()
        return self.fund_fp.get_fund_issuance_info(code)

    @event_trace
    def get_fund_set(self, date, fund_type='ETF'):
        """
        查询指定日期的基金代码列表
        :param
        date: 查询日期, 类型为string，如'20200403'
        fund_type: 基金类型, 类型为string, 如'ETF, LOF, ALL',默认ETF, ALL为全部
        :return:
        """
        self.__set_funddatafp()
        return self.fund_fp.get_fund_set(date, fund_type)

    @event_trace
    def get_fund_data_day(self, exchange_house, date, bar_size,
                          trading_phase_code=None,
                          sort_by_receive_time=False):
        self.__set_fundmdcdp()
        df = self.fund_mdc_dp.get_fund_data_by_day(
            bar_size=bar_size,
            date=date,
            exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df

    @event_trace
    def get_fund_tick_by_exchange(self, exchange_house, date,
                                  trading_phase_code=None,
                                  sort_by_receive_time=False):
        self.__set_fundmdcdp()
        df = self.fund_mdc_dp.get_fund_data_by_day(
            bar_size='tick',
            date=date,
            exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df

    @event_trace
    def get_fund_transaction_by_exchange(self, exchange_house, date,
                                         trading_phase_code=None,
                                         sort_by_receive_time=False):
        self.__set_fundmdcdp()
        df = self.fund_mdc_dp.get_fund_data_by_day(
            bar_size='transaction',
            date=date,
            exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df

    @event_trace
    def get_fund_order_by_exchange(self, exchange_house, date,
                                   trading_phase_code=None,
                                   sort_by_receive_time=False):
        self.__set_fundmdcdp()
        df = self.fund_mdc_dp.get_fund_data_by_day(
            bar_size='order',
            date=date,
            exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df

    @event_trace
    def get_fund_kline_by_exchange(self, exchange_house, date, bar_size,
                                   trading_phase_code=None,
                                   sort_by_receive_time=False):
        bar_size = bar_size.lower()
        if bar_size not in ['k_day', 'k_1min', 'k_5min', 'k_10min', 'k_60min']:
            raise Exception('bar_size必须在k_1min,k_5min,k_10min,k_60min中')
        self.__set_fundmdcdp()
        df = self.fund_mdc_dp.get_fund_data_by_day(
            bar_size=bar_size,
            date=date,
            exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df
