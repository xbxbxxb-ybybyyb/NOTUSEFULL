# _*_ coding:utf-8 _*_
from MDCDataProvider.bonddata import BondDataDP
from FactorProvider.bonddata import BondDataFP

from tquant.utils.event_trace import EventTrace, event_trace



class BondData:
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
        self.bond_dp = BondDataDP()
        self.bond_fp = BondDataFP()

    @event_trace
    def get_bond_data(self, symbol, start_time, end_time, bar_size):
        """
        获取可转债行情数据
        :param symbol: 可转债代码, string类型, 如'123021.SZ'
        :param start_time:起始日期,string类型，如'20190102 000000000'
        :param end_time:终止日期，string类型，如'20190102 235900000'
        :param bar_size:数据周期枚举类，支持1day('K_DAY'), 1min('K_1MIN'), tick('TICK'), order('ORDER'), transaction('TRANSACTION')
        :return:
        """
        return self.bond_dp.get_bond_data(symbol, start_time, end_time, bar_size)

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
        return self.bond_dp.get_cfe_bond_data(symbol, start_time, end_time, bar_size, fill_cash_bond_quotes)

    @event_trace
    def get_bond_issuance_info(self, symbol):
        """
        获取可转债代码的基本信息
        :param code: 可转债的代码，string类型，如 '125930.SZ'
        :return:
        """
        return self.bond_fp.get_bond_issuance_info(symbol)

    @event_trace
    def get_bond_set(self, date, bond_type='kzz'):
        """
        查询指定日期正在发行的可转债列表
        :param date: 查询时间, 类型为string，如 '20200330'
        :param bond_type: 债券类型, 类型为string，默认 'kzz'代表可转债
        :return:
        """
        return self.bond_fp.get_bond_set(date, bond_type)

