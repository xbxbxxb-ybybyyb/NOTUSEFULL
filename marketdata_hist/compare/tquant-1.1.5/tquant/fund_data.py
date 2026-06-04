# _*_ coding:utf-8 _*_
from MDCDataProvider.funddata import FundDataDP
from FactorProvider.funddata import FundDataFP

from tquant.utils.event_trace import EventTrace, event_trace



class FundData:
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
        self.fund_dp = FundDataDP()
        self.fund_fp = FundDataFP()

    @event_trace
    def get_fund_data(self, symbol, start_time, end_time, bar_size):
        """
        获取可转债行情数据
        :param symbol: 基金代码, string类型, 如'123021.SZ'
        :param start_time:起始日期,string类型，如'20190102 000000000'
        :param end_time:终止日期，string类型，如'20190102 235900000'
        :param bar_size:数据周期枚举类，支持1day('K_DAY'), 1min('K_1MIN'), tick('TICK'), order('ORDER'), transaction('TRANSACTION')
        :return:
        """
        return self.fund_dp.get_fund_data(symbol, start_time, end_time, bar_size)
    @event_trace
    def get_fund_tick(self, symbol, start_time, end_time):
        """
        获取可转债行情tick数据
        :param symbol: 基金代码, string类型, 如'123021.SZ'
        :param start_time:起始日期,string类型，如'20190102 000000000'
        :param end_time:终止日期，string类型，如'20190102 235900000'
        :return:
        """
        return self.fund_dp.get_fund_data(symbol, start_time, end_time, 'TICK')
    @event_trace
    def get_fund_kline(self, symbol, start_time, end_time, bar_size):
        """
        获取可转债行情kline数据
        :param symbol: 基金代码, string类型, 如'123021.SZ'
        :param start_time:起始日期,string类型，如'20190102 000000000'
        :param end_time:终止日期，string类型，如'20190102 235900000'
        :param bar_size:数据周期枚举类，支持1day('K_DAY'), 1min('K_1MIN')
        :return:
        """
        if bar_size not in ['K_DAY', 'K_1MIN']:
            raise Exception('该接口仅支持K_DAY, K_1MIN')
        return self.fund_dp.get_fund_data(symbol, start_time, end_time, bar_size)
    @event_trace
    def get_fund_transaction(self, symbol, start_time, end_time):
        """
        获取可转债行情成交数据
        :param symbol: 基金代码, string类型, 如'123021.SZ'
        :param start_time:起始日期,string类型，如'20190102 000000000'
        :param end_time:终止日期，string类型，如'20190102 235900000'
        :return:
        """
        return self.fund_dp.get_fund_data(symbol, start_time, end_time, 'TRANSACTION')
    @event_trace
    def get_fund_order(self, symbol, start_time, end_time):
        """
        获取可转债行情委托数据
        :param symbol: 基金代码, string类型, 如'123021.SZ'
        :param start_time:起始日期,string类型，如'20190102 000000000'
        :param end_time:终止日期，string类型，如'20190102 235900000'
        :return:
        """
        return self.fund_dp.get_fund_data(symbol, start_time, end_time, 'ORDER')
    @event_trace
    def get_fund_issuance_info(self, code):
        """
        获取基金的基本信息
        :param code: 可转债的代码，如 '159901.SZ'
        :return:
        """
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
        return self.fund_fp.get_fund_set(date, fund_type)

