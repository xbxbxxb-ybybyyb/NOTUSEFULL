# _*_ coding:utf-8 _*_

from FactorProvider.factordata import xqfactor as xqf
from FactorProvider.factordata import tqfactor as tqf
from tquant.utils.event_trace import EventTrace, event_trace



class BasicData:
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

    @event_trace
    def get_trading_day(self, start_time, end_time, frequency='DAY', day_type=None, date_type='TRADINGDAYS',
                        location='CN'):
        """
        通过输入的起止时间、日期类型、星期属性等参数，返回在这些条件下的交易日期列表
        :param start_time: 开始时间，格式yyyymmdd，string('20180102')
        :param end_time:结束时间，格式yyyymmdd，tring('20180105')，frequency为DAY时可为非零整数：
                以startTime为起点，前后n日的时间序列查询(abs(n) <= 10000，n>10000则最多输出10000条数据)，例如，查询以20180102前10个交易日的序列，
                可以输入：tradingDay(20180102, -10)，后面20日：tradingDay(20180102, 20)
        :param frequency: 数据频率，默认DAY，取值详见参数说明
        :param day_type:日期类型，当frequency 参数为WEEK 时，默认值为FRIDAY；
                        当frequency 参数为其它值，默认值为LASTDAY，frequency为DAY时day_type取值无影响,
                        frequency取值MONTH或YEAR时，dayType仅支持FIRSTDAY、LASTDAY，取值详见参数说明
        :param date_type:日历类型，默认值TRADINGDAYS，取值详见参数说明
        :param location: 股票市场，'CN':国内A股，'HK':港股，'US':美股，默认为'CN'
        :return: 交易日列表(list)

        参数说明：
            - frequency 数据频率
            ==========   =========
            类型名称     类型说明
            DAY          日
            WEEK         周
            MONTH        月
            QUARTER      季
            HALFYEAR     半年
            YEAR         年
            ==========   =========

        - day_type 日期类型

            ==========   ============
            类型名称     类型说明
            MONDAY       周一
            TUESDAY      周二
            WEDNESDAY    周三
            THURSDAY     周四
            FRIDAY       周五
            SATURDAY     周六
            SUNDAY       周日
            FIRSTDAY     第一天
            LASTDAY      最后一天
            ==========   ============

        - date_type 日历类型

            ============   ========
            类型名称       类型说明
            ALLDAYS        日历日
            TRADINGDAYS    交易日
            ============   ========
        """
        tradingdays = xqf.tradingDay(start_time, end_time, frequency, day_type, date_type, location)
        return tradingdays

    @event_trace
    def get_industry(self, industry_type, level=0):
        """
        根据输入的行业类别、级别查询该类别行业代码信息
        :param industry_type:行业类型，'CSRC' 为证监会行业分类，'CITICS' 为中信行业分类，'SW' 为申万行业分类
        :param level: 级别，取值[0,3]之间整数，默认0，证监会行业只有两级分类取值[0,2]之间的整数
        :return:
        """
        df = xqf.hind(industry_type, level)
        return df

    @event_trace
    def get_conception(self, trading_code):
        """
        根据输入的股票代码，返回对应的所属板块信息
        :param trading_code: string,股票代码
        :return: DataFrame
        """
        return tqf.get_conception(trading_code)
