# _*_ coding:utf-8 _*_

from FactorProvider.factordata import xqfactor as xqf
from FactorProvider.factordata import tqfactor as tqf
from tquant.utils.event_trace import EventTrace, event_trace

security_type_info = None

class BasicData:
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
        :param industry_type:行业类型，'CSRC' 为证监会行业分类，'CITICS' 为中信行业分类，'SW' 为申万行业分类，'CS'为中证行业
        :param level: 级别，取值[0,4]之间整数，默认0，证监会行业只有两级分类取值[0,2]之间的整数，中信行业、申万行业取值[0,3]之间的整数，中证行业取值[0,4]之间的整数
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

    def get_security_type(self,security_id):
        global security_type_info
        if not security_type_info:
            security_type_info = tqf.get_stock_fund_info()
        if security_id in security_type_info["STOCK"]:
            return "STOCK"
        elif security_id in security_type_info["FUND"]:
            return "FUND"
        else:
            raise Exception("目前仅支持查询证券类型为STOCK,FUND的标的！")

    def get_a_month_calender_by_date(self, input_date_list, input_month, input_year):
        # 想打印给定月份的日历，我们需要知道这个月份是多少天
        input_date_list = [int(i) for i in input_date_list]
        total_days = 3
        month_english = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                         "November", "December"]
        for year in range(1800, input_year):
            if self.is_leap_year(year):
                total_days += 366
            else:
                total_days += 365
        # 下面计算当前年份中每个月的天数
        for month in range(1, input_month):
            total_days += self.get_days_of_month(month, input_year)
        # 下面的结果是几，说明当前月份的1号就是星期几
        first_day = count = total_days % 7
        print("{: ^30}{: ^30}".format(month_english[input_month - 1], input_year))
        print("{:-^65}".format("-"))
        print("{: ^9}{: ^9}{: ^9}{: ^9}{: ^9}{: ^9}{: ^9}".format("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"))
        for days in range(1, self.get_days_of_month(input_month, input_year) + 1):
            if days == 1:
                if days not in input_date_list:
                    days = " "
                if first_day == 0:
                    print("{: ^9}".format(days), end="")
                elif 1 <= first_day <= 5:
                    for d in range(1, first_day + 1):
                        print("{: ^9}".format(" "), end="")
                    print("{: ^9}".format(days), end="")
                else:
                    for d in range(1, first_day + 1):
                        print("{: ^9}".format(" "), end="")
                    print("{: ^9}".format(days))
                count += 1

            else:
                if days not in input_date_list:
                    days = " "
                if count % 7 == 0:
                    print("{: ^9}".format(days), )
                else:
                    print("{: ^9}".format(days), end="")
            count += 1

        print()

    # 获取给定的月份有多少天
    def get_days_of_month(self, input_month, input_year):
        leap_year = self.is_leap_year(input_year)
        if input_month in (1, 3, 5, 7, 8, 10, 12):
            return 31
        elif input_month in (4, 6, 9, 11):
            return 30
        elif self.is_leap_year(input_year):
            return 29
        else:
            return 28

    # 获取给定的年份是不是闰年
    def is_leap_year(self, input_year):
        if (input_year % 4 == 0 and input_year % 100 != 0) or (input_year % 400 == 0):
            return True
        else:
            return False

    def show_days_in_calendar(self, date_list):
        if not isinstance(date_list,list):
            raise Exception("入参日期列表date_list必须是list的格式")

        year_month_list = {}
        for date in date_list:
            if not isinstance(date, str) or len(date) != 8:
                raise Exception("列表中的日期必须是字符串的形式,格式为yyyymmdd,例如20200101")
            if date[:6] not in year_month_list:
                year_month_list[date[:6]] = [date[-2:]]
            else:
                year_month_list[date[:6]].append(date[-2:])
        for year_month, date_list in year_month_list.items():
            self.get_a_month_calender_by_date(date_list, int(year_month[-2:]), int(year_month[:4]))


if __name__ == "__main__":
    # get_a_month_calender(9,2000)
    from tquant.basic_data import BasicData
    bd = BasicData()
    tradingday = bd.get_trading_day('20210101', '20210131')
    bd.show_days_in_calendar(tradingday)
