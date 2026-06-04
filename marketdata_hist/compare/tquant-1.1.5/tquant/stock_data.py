# _*_ coding:utf-8 _*_

from FactorProvider.factordata import xqfactor as xqf
from FactorProvider.factordata import tqfactor as tqf
from MDCDataProvider.stockdata import StockDataDP
from tquant.utils import util
import datetime as dt
import math
import pandas as pd
import numpy as np

from tquant.utils.event_trace import EventTrace, event_trace


class StockData:
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
        self.mdp = StockDataDP()

    @event_trace
    def get_stock_basics(self, trading_codes):
        """
        获取股票的基本信息
        :param trading_codes: list/string，单支股票代码或多支股票的列表
        :return: DataFrame
        """
        if not trading_codes:
            raise Exception("【trading_codes】为单支股票代码或多支股票的列表，请重新输入！")
        return tqf.get_stock_basics(trading_codes)
    @event_trace
    def get_factor_price_daily(self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取日行情数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string)或日期列表
        :param factor_list: 单个因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return:索引为[日期,股票] 的MultiIndex DataFrame
        """
        return xqf.get_market_price(trading_codes, date_list, factor_list, fill_na, sort_option=sort_option)
    @event_trace
    def get_factor_valuation_metrics(self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取估值因子的因子数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string)或日期列表
        :param factor_list: 单个因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return: 索引为[日期,股票] 的MultiIndex DataFrame
        """
        return xqf.get_factor_idct(trading_codes, date_list, factor_list, fill_na, sort_option=sort_option)
    @event_trace
    def get_factor_risk_analysis(self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取风险因子的因子数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string)或日期列表
        :param factor_list: 单个因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return: 索引为[日期,股票] 的MultiIndex DataFrame
        """
        return xqf.get_factor_idct(trading_codes, date_list, factor_list, fill_na, sort_option=sort_option)
    @event_trace
    def get_factor_financial_analysis(self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取财务分析因子数据
        :param trading_codes: 股票代码或股票代码列表
        :param date_list: 日期(string)或多个日期的列表
        :param factor_list: 因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return: 索引为[日期,股票] 的MultiIndex DataFrame
        """
        return xqf.get_finance_idct(trading_codes, date_list, factor_list, fill_na, sort_option=sort_option)
    @event_trace
    def get_factor_financial_report(self, trading_codes, date_list, factor_list, statement_type="102",
                                    fill_na=False, sort_option=True):
        """
        获取财务报告数据
        :param trading_codes: 股票或股票列表
        :param date_list: 日期(string) 或日期列表
        :param factor_list: 单个因子或因子列表
        :param statement_type: str，报告类型，详见参数说明
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return: 索引为[日期,股票]的MultiIndex DataFrame

        statement_type 参数说明：
        ==============      =====        ======================
            类型名称	    数值	   类型说明
            COMBINED	    102 	合并报表
            COMBINED_SS	    108 	合并报表(单季度)
            COMBINED_SSA	109 	合并报表(单季度调整)
            COMBINED_A	    104 	合并报表(调整)
            COMBINED_NM	    106 	合并报表(更正前)
            PARENT	        202 	母公司报表
            PARENT_SS	    208 	母公司报表(单季度)
            PARENT_SSA	    209 	母公司报表(单季度调整)
            PARENT_A	    204 	母公司报表(调整)
            PARENT_NM	    206 	母公司报表(更正前)
        ==================  =====        ======================
        """
        return xqf.get_finance_report(trading_codes, date_list, factor_list, statement_type, fill_na,
                                      sort_option=sort_option)
    @event_trace
    def get_factor_dividend(self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取分红因子数据数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string)或日期列表
        :param factor_list: 单个因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return:索引为[日期,股票] 的MultiIndex DataFrame
        """
        return xqf.get_divid(trading_codes, date_list, factor_list, fill_na, sort_option=sort_option)
    @event_trace
    def get_factor_newsmsg(self, trading_codes, factor_list, fill_na=False):
        """
        获取股票最新信息
        :param trading_codes: 股票或股票列表
        :param factor_list: 股票信息字段或列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :return: DataFrame
        """
        return xqf.get_stock_info(trading_codes, factor_list, fill_na)
    @event_trace
    def get_factor_conforecast(self, trading_codes, date_list, factor_list, stock_type, block_type=4, fill_na=False,
                               sort_option=True):
        """
        一致预期源表查询
        :param trading_codes: 股票代码
        :param date_list: 日期列表
        :param factor_list: 因子列表
        :param stock_type: 证券代码对应的代码类型，1 为A股代码；2 为指数代码；
        :param block_type:组合类型，默认4：行业，详见参数说明
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return:
        参数说明：
        - block_type 组合类型 值>=5为指数分行业，默认值为4：行业
            ==========   =========
            数值         类型说明
            2            指数
            4            行业
            5            沪深300行业
            6            上证180行业
            7            红利指数行业
            8            上证50行业
            9            中证100行业
            10           深证100行业
            11           中小板指行业
            12           巨潮40行业
            13           巨潮300行业
            14           巨潮100行业
            15           中标300行业
            16           中标50行业
            17           新富A50行业
            18           道中88行业
            19           上证A股行业
            20           超大盘行业
            21           中证500行业
            22           中证700行业
            23           中小板指行业
            24           创业板指数行业
            25           上证新兴行业
            26           中证800行业
            ==========   =========
        """
        if not isinstance(trading_codes, list):
            raise Exception("【trading_codes】参数为列表形式，请重新输入！")
        return xqf.get_conforecast(trading_codes, date_list, factor_list, stock_type, block_type, fill_na,
                                   sort_option=sort_option)
    @event_trace
    def get_stock_transaction(self, trading_code, start_datetime, end_datetime):
        """
        证券逐笔成交查询,直接返回DataFrame对象
        :param trading_code: string，单支股票代码，如："601688.SH"
        :param start_datetime:string，开始时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180301 093000000'
        :param end_datetime:string，结束时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180305 150000250'
        :return: DataFrame
        注意：按时间范围读取数据有最大范围限制，最长不能超过180天
        """
        df = self.mdp.get_stock_data(trading_code, start_datetime, end_datetime,
                                "Transaction")
        return df

    @event_trace
    def get_stock_order(self, trading_code, start_datetime, end_datetime):
        """
        证券委托数据查询服务：逐笔委托查询
        :param trading_code: string，单支股票代码，如："601688.SH"
        :param start_datetime:string，开始时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180301 093000000'
        :param end_datetime:string，结束时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180305 150000250'
        :return: DataFrame
        注意：按时间范围读取数据有最大范围限制，最长不能超过180天
        """
        df = self.mdp.get_stock_data(trading_code, start_datetime, end_datetime, "Order")
        return df

    @event_trace
    def get_stock_kline(self, trading_code, start_datetime, end_datetime):
        """
        证券K线查询服务:根据证券ID查询一段时间范围内的K线数据, 返回DataFrame对象
        :param trading_code: string，单支股票代码，如："601688.SH"
        :param start_datetime:string，开始时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180301 093000000'
        :param end_datetime:string，结束时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180305 150000250'
        :param k_type: int，k线时间间隔类型
        :return: DataFrame
        注意：按时间范围读取数据有最大范围限制，最长不能超过180天
        """
        df = self.mdp.get_stock_data(trading_code, start_datetime, end_datetime,
                                "Kline1M4ZT")
        return df

    @event_trace
    def get_stock_tick(self, trading_code, start_datetime, end_datetime, trading_phase_code=[]):
        """
        证券Tick查询服务: 根据证券ID查询一段时间范围内的Tick数据,支持股票数据查询
        :param trading_code: string，单支股票代码，如："601688.SH"
        :param start_datetime:string，开始时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180301 093000000'
        :param end_datetime:string，结束时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180305 150000250'
        :param trading_phase_code:list，取哪些市场阶段状态，默认取所有。
                                所需的交易阶段代码('0'表示开盘前，启动。'1'表示开盘集合竞价。
                                '2'表示开盘集合竞价阶段结束到连续竞价阶段开始之前。'3'表示连续竞价。
                                '4'表示中午休市。'5'表示收盘集合竞价。'6'表示已闭市。'7'表示盘后交易（实际未使用）)
        :return:DataFrame
        注意：按时间范围读取数据有最大范围限制，最长不能超过180天
        """
        df = self.mdp.get_stock_data(trading_code, start_datetime, end_datetime,
                                "Stock", trading_phase_code=trading_phase_code)
        return df

    @event_trace
    def get_plate_info(self, plate_type, date_time, plate_id, use_prev_name=True):
        """
        通过输入的板块类型、时间和板块ID，输出该板块的成分股
        :param plate_type: 板块类型，目前只支持行业板块(INDUSTRY)、市场板块(MARKET)
        :param date_time:查询日期，格式yyyymmdd,例如:'20100801'
        :param plate_id:当plate_type 为行业板块时，plate_id为行业代码，如：'CITICS.b106040700'、'SW.6110'，详见参数说明,支持的行业请参见行业代码表；
                       当plate_type 为市场板块时，plate_id取值详见参数说明 可取’ALLA’(全部A股)，’SHA’(上海A股)，’SZA’(深圳A股)
        :param use_prev_name:获取成分股名称为指定的日期时的名称或最新名称，默认True为指定的日期时的名称
        :return: DataFrame

        参数说明：
        - IndustryType 行业分类代码

        ========  ==============
        类型名称  类型说明
        CSRC      证监会行业分类
        CITICS    中信行业分类
        SW        申万行业分类
        ========  ==============

        - plate_type 为市场板块时，plate_id取值
        ========  ==============
        类型名称  类型说明
        ALLA       全部A股
        SHA        上海A股
        SZA        深圳A股
        SME         中小板
        GEM         创业板
        ========  ==============
        """
        if plate_type not in ['INDUSTRY', 'MARKET','CONCEPT']:
            raise Exception("【plate_type】参数：板块类型，目前只支持行业板块(INDUSTRY)、市场板块(MARKET)、概念板块(CONCEPT)，请重新输入！")
        df = xqf.hset(plate_type, date_time, plate_id, use_prev_name=use_prev_name)
        return df

    @event_trace
    def get_stock_industry(self, trading_codes, date=dt.date.today().strftime("%Y%m%d"), industry_type=None,
                           industry_level=3, switch_flag='OFF'):
        """
        查询股票指定日期所属的指定级别行业信息，目前支持的行业类别有证监会新行业分类、中信行业分类、申万行业分类三种
        :param trading_codes: 单个股票代码 或 股票列表
        :param date:日期(string) ，默认为查询当天的日期
        :param industry_type:行业类型，’CSRC’ 为证监会行业分类，’CITICS’ 为中信行业分类，’SW’ 为申万行业分类，默认全部行业
        :param industry_level:行业级别，取值[1,3]之间的整数，默认为三级行业，证监会行业只有两级分类取[1,2]的整数
        :param switch_flag: 是否过滤NAN值，取值'ON'或'OFF'，默认'OFF'不过滤
        :return:DataFrame
        """
        df = xqf.hsi(trading_codes, date, industry_type, industry_level, switch_flag)
        return df

    @event_trace
    def stock_filter(self, stock_pool, filter_date=dt.date.today().strftime("%Y%m%d"), filter_type='SSO',
                     use_prev_name=True):
        """
        过滤股票池中不符合条件的股票。过滤掉STPT，停牌，开盘涨停等股票。
        :param stock_pool: 股票池，列表类型
        :param filter_date:查询日期,数值型，例如：20151231，默认查询当天日期
        :param filter_type:过滤类型，过滤掉STPT+停牌+开盘涨停的股票，引用格式：'SSO'
        :param use_prev_name:获取股票名称为指定的日期时的名称或最新名称，默认True为指定的日期时的名称
        :return:

        参数说明：
        - filter_type 过滤类型

        ========        ==============
        类型名称        类型说明
        STPT            特别处理、特殊处理
        SUSPEND         停牌
        OPENUPLIMIT	    开盘涨停
        OPENDOWNLIMIT	开盘跌停
        SSO				STPT + 停牌 + 开盘涨停
        STSPEND			STPT + 停牌
        STUP 			STPT + 开盘涨停
        STDOWN 			STPT + 开盘跌停
        UPSPEND 		停牌 + 开盘涨停
        DNSPWND 		停牌 + 开盘跌停
        ========  ==============
        """
        df = xqf.stockFilter(stock_pool, filter_date, filter_type, use_prev_name)
        return df
    @event_trace
    def get_factor_alph191(self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取alpha因子数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string 或 int)或日期列表或(开始日期,结束日期)的元组
        :param factor_list: 单个因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return:
        """
        return xqf.get_factor_alph191(trading_codes, date_list, factor_list, fill_na, sort_option)
    @event_trace
    def get_factor_barra(self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取barra因子数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string 或 int)或日期列表或(开始日期,结束日期)的元组
        :param factor_list: 单个因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return:
        """
        return xqf.get_factor_barra(trading_codes, date_list, factor_list, fill_na, sort_option)
    @event_trace
    def get_factor_technical_analysis(self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取技术面因子数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string 或 int)或日期列表或(开始日期,结束日期)的元组
        :param factor_list: 单个因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return:
        """
        return xqf.get_factor_technical_analysis(trading_codes, date_list, factor_list, fill_na, sort_option)
    @event_trace
    def get_factors_info(self):
        """
        获取tquant所有因子的信息
        :return:
        """
        return util.get_factors_info()

    def get_tfactor_value(self, trading_codes, date_list, factor_list, fill_na=False):
        """
        获取各个大类因子数据，只支持查询单个大类的因子
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string 或 int)或日期列表或(开始日期,结束日期)的元组
        :param factor_list: 单个因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :return:
        """
        if isinstance(factor_list, str):
            factor_list = [factor_list]
        return self.__get_tfactor_value(trading_codes, date_list, factor_list, fill_na)


    def __get_tfactor_value(self, trading_codes, date_list, factor_list, fill_na=False):
        # ['riskanalysis', 'financialanalysis', 'financialreport', 'valuation', 'market', 'newmsgindex']
        factors_info = self.get_factors_info()
        f_catalog = {}
        for factor in factor_list:
            flag = False
            for key in factors_info:
                if factor.lower() in factors_info[key]:
                    if f_catalog.get(key):
                        f_catalog[key].append(factor)
                    else:
                        f_catalog[key] = [factor]
                    flag = True
            if not flag:
                raise Exception("因子-{0}不存在，请检查后输入！".format(factor))
        if len(f_catalog) == 0:
            raise Exception("请输入正确的因子！")
        elif len(f_catalog) == 1:
            key = list(f_catalog.keys())[0]
            if key == "market":
                result = self.get_factor_price_daily(trading_codes, date_list, factor_list, fill_na)
            elif key == "valuation":
                result = self.get_factor_valuation_metrics(trading_codes, date_list, factor_list, fill_na)
            elif key == "riskanalysis":
                result = self.get_factor_risk_analysis(trading_codes, date_list, factor_list, fill_na)
            elif key == "financialanalysis":
                result = self.get_factor_financial_analysis(trading_codes, date_list, factor_list, fill_na)
            elif key == "financialreport":
                result = self.get_factor_financial_report(trading_codes, date_list, factor_list, statement_type='102',
                                                          fill_na=fill_na)
            elif key == "newmsgindex":
                result = self.get_factor_newsmsg(trading_codes, factor_list, fill_na)
            elif key == "alpha":
                result = self.get_factor_alph191(trading_codes, date_list, factor_list, fill_na)
            elif key == "barra":
                result = self.get_factor_barra(trading_codes, date_list, factor_list, fill_na)
            elif key == "technicalanalysis":
                result = self.get_factor_technical_analysis(trading_codes, date_list, factor_list, fill_na)
            else:
                raise Exception(
                    "此接口只支持'riskanalysis', 'financialanalysis', 'financialreport', 'valuation', 'market', 'newmsgindex', 'alpha', 'barra', 'technicalanalysis'的因子查询！")

        else:
            raise Exception("只支持同时查询一个大类的因子！")
        return result

    def __get_quarter_day(self, dateList=[]):
        dateList = [int(i) for i in dateList]
        quaterDate = [None] * len(dateList)
        for i in range(len(dateList)):
            dateyear = math.floor(dateList[i] / 10000)
            datequater = math.ceil(math.floor((dateList[i] - dateyear * 10000) / 100) / 3)
            if datequater == 1:
                quaterDate[i] = (dateyear - 1) * 10000 + 1231
            elif datequater == 2:
                quaterDate[i] = dateyear * 10000 + 331
            elif datequater == 3:
                quaterDate[i] = dateyear * 10000 + 630
            elif datequater == 4:
                quaterDate[i] = dateyear * 10000 + 930
        return [str(i) for i in quaterDate]

    def __get_report_dt_last_years(self, report_dt, delta_year):
        """
        获取前几年的报告期
        report_dt：当前报告期
        delta_year：获取过去n年的报告期
        """
        report_dt = int(report_dt)
        dateyear = math.floor(report_dt / 10000)
        datequater = math.ceil(math.floor((report_dt - dateyear * 10000) / 100) / 3)

        report_dt_last_years = []  # 过去n年的报告期
        for i in range(1, delta_year + 1):
            if datequater == 1:
                report_dt_last_years.append((dateyear - i) * 10000 + 331)
                report_dt_last_years.append((dateyear - i) * 10000 + 630)
                report_dt_last_years.append((dateyear - i) * 10000 + 930)
                report_dt_last_years.append((dateyear - i) * 10000 + 1231)
            elif datequater == 2:
                report_dt_last_years.append((dateyear - i + 1) * 10000 + 331)
                report_dt_last_years.append((dateyear - i) * 10000 + 1231)
                report_dt_last_years.append((dateyear - i) * 10000 + 930)
                report_dt_last_years.append((dateyear - i) * 10000 + 630)
            elif datequater == 3:
                report_dt_last_years.append((dateyear - i + 1) * 10000 + 630)
                report_dt_last_years.append((dateyear - i + 1) * 10000 + 331)
                report_dt_last_years.append((dateyear - i) * 10000 + 1231)
                report_dt_last_years.append((dateyear - i) * 10000 + 930)
            elif datequater == 4:
                report_dt_last_years.append((dateyear - i + 1) * 10000 + 930)
                report_dt_last_years.append((dateyear - i + 1) * 10000 + 630)
                report_dt_last_years.append((dateyear - i + 1) * 10000 + 331)
                report_dt_last_years.append((dateyear - i) * 10000 + 1231)
        return sorted([str(i) for i in report_dt_last_years])

    def __is_report_day(self, day):
        day = str(day)
        assert len(day) == 8, 'dayType error: 输入日期格式必须为‘YYYYmmdd’标准格式！'
        if day[-4:] == '0331' or day[-4:] == '0630' or day[-4:] == '0930' or day[-4:] == '1231':
            return True
        else:
            return False

    def __standard_publish_days(self, publish_days, tdate):
        # 规范报告期，前一个实际公告日期，应小于后一个实际公告日期
        new_days = []
        tdate = tdate[::-1]
        for didx, day in enumerate(publish_days[::-1]):
            # 从最新日期往前推
            if pd.isnull(day):
                if self.__is_report_day(tdate[didx]):
                    # 如果报告期的实际公告日期缺失，用报告期代替
                    new_days.append(tdate[didx])
                else:
                    new_days.append(day)
            else:
                new_days.append(day)
        return new_days[::-1]
    @event_trace
    def get_finicial_cross_section_data(self, trading_codes, date_list, factor_list, publishDateType="ACCOUNTINGDAY"):
        """本API用于查询日度财务指标指定股票列表的时间序列因子数据，或者横截面因子数据。通过输入股票列表、因子列表以及起止日期，输出不同因子类型下的因子数值。

        :param stockList: 股票代码列表，字符型cell列向量，例如：{‘000001.SZ’;’601688.SH’};
        :param factorList: 因子名称列表，枚举列向量，例如：[Factors.high;Factors.low]。详情请见因子列表;
        :param dateList: 数据日期列表，数值型列向量，格式 yyyymmdd,例如: [20100816;20100921]
        :param publishDateType: str，匹配日期类型，ACCOUNTINGDAY：会计报表日期，PUBLISHDAY：公告披露日期，默认公告披露日期， TTM:以披露日期为标准的前12个月财务数据
        :param factorPar: 财务报表类型，枚举值，默认为合并报表类型。需要查询特殊类型的指标时请用枚举定义引用，例如：FactorType.PARENT。
        :return: factorData，因子数据，多维List，第一层是查询因子列表，第二层是因子名称及因子数值，第三层是因子数值二维List，其行为股票代码索引，列为日期索引。

        | 因子数据矩阵的行索引、列索引请见stkCodeList、resultDateList两个数组。stkCodeList, 股票代码列表，cell类型列向量

        | resultDateList,查询结果日期列表，数值型列向量，格式 yyyymmdd,例如: [20100816,20100921]

    - PublishDateType 匹配日期类型

        ==============    ==========
        类型名称            类型说明
        ACCOUNTINGDAY        报告期
        PUBLISHDAY     实际公告日期
        TTM                  TTM数据
        ============== ==========
        """

        # 判断传入参数非财务数据的异常
        assert len(date_list[0]) == 8, 'date_list error: 输入日期格式必须为‘YYYYmmdd’标准格式！'

        # 取有数据的前4个报告期
        quarter_days = self.__get_quarter_day(date_list)
        quarter_days = list(sorted(set(quarter_days)))
        min_quarter_day = min(quarter_days)

        if publishDateType == "ACCOUNTINGDAY":
            # 取前一年报告期
            report_dt_last_years = self.__get_report_dt_last_years(min_quarter_day, 1)
            tdate = quarter_days + report_dt_last_years
            tdate = list(sorted(set(tdate)))  # 日期去重
            # ,取前一年的报告期是消除0930到0430之间7个月一直不披露报告的极端情况
            df = self.__get_tfactor_value(trading_codes, tdate, factor_list, fill_na=True)
            df_result = df

            df_dict = df.to_dict()
            data_result = {}  # 存放最终的计算数据

            for factor in factor_list:
                data = df_dict[factor]
                data_result[factor] = {}
                for stock in trading_codes:
                    predata = np.nan
                    for d in range(len(tdate)):
                        for day in date_list:
                            if day >= tdate[d]:
                                import traceback
                                try:
                                    if not pd.isnull(data[(tdate[d], stock)]):
                                        data_result[factor][(day, stock)] = data[(tdate[d], stock)]
                                        predata = data[(tdate[d], stock)]
                                    else:
                                        data_result[factor][(day, stock)] = predata
                                except Exception as e:
                                    traceback.print_exc()
                                    data_result[factor][(day, stock)] = np.nan

        elif publishDateType == "TTM":
            report_dt_last_years = self.__get_report_dt_last_years(min_quarter_day, 2)
            report_dts = quarter_days + report_dt_last_years
            report_dts = list(sorted(set(report_dts)))  # 日期去重
            # ,取前一年的报告期是消除0930到0430之间7个月一直不披露报告的极端情况
            df = self.__get_tfactor_value(trading_codes, report_dts, factor_list, fill_na=True)
            df_p = self.__get_tfactor_value(trading_codes, report_dts, ['stm_issuingdate'], fill_na=True)

            df_dict = df.to_dict()
            data_result = {}  # 存放最终的计算数据

            for factor in factor_list:
                data = df_dict[factor]
                data_result[factor] = {}
                for stock in trading_codes:
                    publish_days = df_p.loc[(slice(None), stock), 'stm_issuingdate'].tolist()
                    publish_days = self.__standard_publish_days(publish_days, report_dts)
                    # 查询对应的最近报告期
                    for d in range(len(publish_days)):
                        if d < 6:
                            continue
                        for day in date_list:
                            if day >= publish_days[d]:
                                quaterDate = int(report_dts[d]) - math.floor(int(report_dts[d]) / 10000) * 10000
                                import traceback
                                try:
                                    if quaterDate == 1231:
                                        data_result[factor][(day, stock)] = data[(report_dts[d], stock)]
                                    elif quaterDate == 930:
                                        data_result[factor][(day, stock)] = data[report_dts[d], stock] + data[
                                            report_dts[d - 3], stock] - \
                                                                            data[report_dts[d - 4], stock]
                                    elif quaterDate == 630:
                                        data_result[factor][(day, stock)] = data[report_dts[d], stock] + data[
                                            report_dts[d - 2], stock] - \
                                                                            data[report_dts[d - 4], stock]
                                    elif quaterDate == 331:
                                        data_result[factor][(day, stock)] = data[report_dts[d], stock] + data[
                                            report_dts[d - 1], stock] - \
                                                                            data[report_dts[d - 4], stock]

                                except Exception as e:
                                    traceback.print_exc()
                                    data_result[factor][(day, stock)] = np.nan


        elif publishDateType == "PUBLISHDAY":
            report_dt_last_years = self.__get_report_dt_last_years(min_quarter_day, 2)
            report_dts = quarter_days + report_dt_last_years
            report_dts = list(sorted(set(report_dts)))  # 日期去重
            # ,取前一年的报告期是消除0930到0430之间7个月一直不披露报告的极端情况
            df = self.__get_tfactor_value(trading_codes, report_dts, factor_list, fill_na=True)
            df_p = self.__get_tfactor_value(trading_codes, report_dts, ['stm_issuingdate'], fill_na=True)

            df_dict = df.to_dict()
            data_result = {}  # 存放最终的计算数据

            for factor in factor_list:
                data = df_dict[factor]
                data_result[factor] = {}
                for stock in trading_codes:
                    publish_days = df_p.loc[(slice(None), stock), 'stm_issuingdate'].tolist()
                    publish_days = self.__standard_publish_days(publish_days, report_dts)
                    predata = np.nan
                    # 查询对应的最近报告期
                    for d in range(len(publish_days)):
                        for day in date_list:
                            if day >= publish_days[d]:
                                import traceback
                                try:
                                    if not pd.isnull(data[(report_dts[d], stock)]):
                                        data_result[factor][(day, stock)] = data[(report_dts[d], stock)]
                                        predata = data[(report_dts[d], stock)]
                                    else:
                                        data_result[factor][(day, stock)] = predata
                                except Exception as e:
                                    traceback.print_exc()
                                    data_result[factor][(day, stock)] = np.nan

        else:
            raise Exception("publishDateType Type Error: 请输出publishDateType正确的参数类型：ACCOUNTINGDAY， PUBLISHDAY， TTM！")

        df_result = pd.DataFrame(data_result)
        df_result.index.names = ['mddate', 'stock']
        df_result = df_result.unstack('stock')
        df_result = df_result.fillna(method='ffill')

        df_result = df_result.loc[date_list, :]
        df_result = df_result.stack("stock", dropna = False)

        return df_result


    def get_factor_evaluation(self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取评价因子数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string 或 int)或日期列表
        :param factor_list: 单个因子或因子列表
        :return:
        """
        return xqf.get_factor_evaluation(trading_codes, date_list, factor_list, fill_na, sort_option)
    def get_factor_emotion(self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取情绪类数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string 或 int)或日期列表
        :param factor_list: 单个因子或因子列表
        :return:
        """
        return xqf.get_factor_emotion(trading_codes, date_list, factor_list, fill_na, sort_option)
    def get_factor_momentum(self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取动量类数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string 或 int)或日期列表
        :param factor_list: 单个因子或因子列表
        :return:
        """
        return xqf.get_factor_momentum(trading_codes, date_list, factor_list, fill_na, sort_option)