# _*_ coding:utf-8 _*_
import pandas as pd
from MDCDataProvider.optiondata import OptionDataDP
from MDCDataProvider.optiondata.option_data import OptionDataDP as MDCOptionDataDP
from MDCDataProvider.DataProvider_ini import get_dataprovider


class OptionData:
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
        self.option_dp = None
        self.option_mdc_dp = None

    def __set_optiondatadp(self):
        if not self.option_dp:
            self.option_dp = OptionDataDP()

    def __set_optionmdcdp(self):
        if not self.option_mdc_dp:
            self.option_mdc_dp = MDCOptionDataDP()

    def get_option_tick(self, symbol, start_time, end_time, use_legacy_data=False):
        """
        获取可转债行情数据
        :param symbol: 期权代码, string类型, 如'123021.SZ'
        :param start_time:起始日期,string类型，如'20190102 000000000'
        :param end_time:终止日期，string类型，如'20190102 235900000'
        :return:
        """
        if use_legacy_data:
            self.__set_optiondatadp()
            df = self.option_dp.get_option_data(
                    symbol, start_time, end_time, 'tick')
            return df
        df = pd.DataFrame()
        for dp_type, dp_values in get_dataprovider('option', 'tick', start_time, end_time).items():
            if dp_type == 'mdc_dp':
                self.__set_optionmdcdp()
                df = df.append(self.option_mdc_dp.get_option_data(symbol,
                    dp_values['start_time'], dp_values['end_time'],
                    'tick'))
            else:
                self.__set_optiondatadp()
                df = df.append(self.option_dp.get_option_data(
                    symbol, dp_values['start_time'], dp_values['end_time'], 'tick'))
        return df

    def get_option_data_day(self, exchange_house, date, bar_size,
                            trading_phase_code=None,
                            sort_by_receive_time=False):
        self.__set_optionmdcdp()
        df = self.option_mdc_dp.get_option_data_by_day(
            bar_size=bar_size,
            date=date, exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df
    
    def get_option_tick_by_exchange(self, exchange_house, date,
                                    trading_phase_code=None,
                                    sort_by_receive_time=False):
        self.__set_optionmdcdp()
        df = self.option_mdc_dp.get_option_data_by_day(
            bar_size='tick',
            date=date,
            exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df
