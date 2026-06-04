# _*_ coding:utf-8 _*_

from FactorProvider.factordata import xqfactor as xqf
from FactorProvider.factordata import tqfactor as tqf
from FactorProvider.factordata.source_factor_read import get_source_factor_value, get_source_table_value
from FactorProvider.factordata.sqlfactor import FactorSql
from MDCDataProvider.stockdata import StockDataDP
from MDCDataProvider.stockdata.stock_data import StockDataDP as MDCStockDataDP
from MDCDataProvider.DataProvider_ini import get_dataprovider
from tquant.utils import util
import datetime as dt
import math
import pandas as pd
import numpy as np

from tquant.utils.event_trace import EventTrace, event_trace
from FactorProvider.utils.stock_data_source import get_stock_method


class StockData:
    __instance = None

    def __new__(cls, *args, **kwargs):
        stock_method, data_source, use_cache = get_stock_method(**kwargs)
        if cls.__instance:
            if cls.__instance.data_source != data_source \
                    or cls.__instance.use_cache != use_cache:
                obj = object.__new__(cls)
                cls.__instance = obj
                cls.__instance.__initialized = False
        else:
            obj = object.__new__(cls)
            cls.__instance = obj
            cls.__instance.__initialized = False
        cls.__instance.stock_method = stock_method
        cls.__instance.data_source = data_source
        cls.__instance.use_cache = use_cache
        return cls.__instance

    def __init__(self, data_source="finchina", use_cache=False):
        if self.__initialized:
            return
        self.__initialized = True
        self.mdp = None
        self.mdc_mdp = None
        self.fs = None

    def __set_sqlfactor(self):
        if not self.fs:
            self.fs = FactorSql()

    def __set_stockdatadp(self):
        if not self.mdp:
            self.mdp = StockDataDP()

    def __set_stockmdcdp(self):
        if not self.mdc_mdp:
            self.mdc_mdp = MDCStockDataDP()

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
    def get_factor_price_daily(
            self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取日行情数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string)或日期列表
        :param factor_list: 单个因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return:索引为[日期,股票] 的MultiIndex DataFrame
        """
        if self.use_cache:
            return self.stock_method.get_factor_price_daily(
                trading_codes, date_list, factor_list, fill_na=fill_na,
                daily_bar_num=242, sort_option=sort_option)
        return self.stock_method.get_market_price(
            trading_codes, date_list, factor_list, fill_na, sort_option=sort_option)

    @event_trace
    def get_factor_valuation_metrics(
            self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取估值因子的因子数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string)或日期列表
        :param factor_list: 单个因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return: 索引为[日期,股票] 的MultiIndex DataFrame
        """
        if self.use_cache:
            return self.stock_method.get_factor_valuation_metrics(
                trading_codes, date_list, factor_list, fill_na=fill_na,
                sort_option=sort_option)
        return self.stock_method.get_factor_idct(
            trading_codes, date_list, factor_list, fill_na, sort_option=sort_option)

    @event_trace
    def get_factor_risk_analysis(
            self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取风险因子的因子数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string)或日期列表
        :param factor_list: 单个因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return: 索引为[日期,股票] 的MultiIndex DataFrame
        """
        if self.use_cache:
            return self.stock_method.get_factor_risk_analysis(
                trading_codes, date_list, factor_list, fill_na=fill_na,
                sort_option=sort_option)
        return self.stock_method.get_factor_idct(
            trading_codes, date_list, factor_list, fill_na, sort_option=sort_option)

    @event_trace
    def get_factor_financial_analysis(
            self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取财务分析因子数据
        :param trading_codes: 股票代码或股票代码列表
        :param date_list: 日期(string)或多个日期的列表
        :param factor_list: 因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return: 索引为[日期,股票] 的MultiIndex DataFrame
        """
        if self.use_cache:
            return self.stock_method.get_factor_financial_analysis(
                trading_codes, date_list, factor_list, fill_na=fill_na,
                sort_option=sort_option)
        return self.stock_method.get_finance_idct(
            trading_codes, date_list, factor_list, fill_na, sort_option=sort_option)

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
        if self.use_cache:
            return self.stock_method.get_factor_financial_report(
                trading_codes, date_list, factor_list, fill_na=fill_na,
                sort_option=sort_option)
        if self.data_source == "wind":
            statement_dict = {"102":"408001000", "408001000": "408001000"}
            statement_type = statement_dict[str(statement_type)]
        return self.stock_method.get_finance_report(trading_codes, date_list, factor_list, statement_type, fill_na,
                                                    sort_option=sort_option)

    @event_trace
    def get_factor_dividend(self, trading_codes, date_list,
                            factor_list, fill_na=False, sort_option=True):
        """
        获取分红因子数据数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string)或日期列表
        :param factor_list: 单个因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return:索引为[日期,股票] 的MultiIndex DataFrame
        """
        if self.use_cache:
            return self.stock_method.get_factor_dividend(
                trading_codes, date_list, factor_list, fill_na=fill_na,
                sort_option=sort_option)
        return self.stock_method.get_divid(trading_codes, date_list,
                                           factor_list, fill_na, sort_option=sort_option)

    @event_trace
    def get_factor_newsmsg(self, trading_codes, factor_list, fill_na=False):
        """
        获取股票最新信息
        :param trading_codes: 股票或股票列表
        :param factor_list: 股票信息字段或列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :return: DataFrame
        """
        if self.use_cache:
            return self.stock_method.get_factor_newsmsg(
                trading_codes, factor_list)
        return self.stock_method.get_stock_info(trading_codes, factor_list, fill_na)

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
        if self.use_cache:
            return self.stock_method.get_factor_conforecast(
                trading_codes, date_list, factor_list, stock_type, block_type,
                fill_na=fill_na, sort_option=sort_option)
        return self.stock_method.get_conforecast(trading_codes, date_list, factor_list, stock_type, block_type, fill_na,
                                                 sort_option=sort_option)

    @event_trace
    def get_stock_transaction(
            self, trading_code, start_datetime, end_datetime, use_legacy_data=False):
        """
        证券逐笔成交查询,直接返回DataFrame对象
        :param trading_code: string，单支股票代码，如："601688.SH"
        :param start_datetime:string，开始时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180301 093000000'
        :param end_datetime:string，结束时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180305 150000250'
        :return: DataFrame
        注意：按时间范围读取数据有最大范围限制，最长不能超过180天
        """
        if use_legacy_data:
            self.__set_stockdatadp()
            df = self.mdp.get_stock_data(
                    trading_code, start_datetime, end_datetime, 'Transaction')
            return df
        df = pd.DataFrame()
        for dp_type, dp_values in get_dataprovider('stock', 'Transaction', start_datetime, end_datetime).items():
            if dp_type == 'mdc_dp':
                self.__set_stockmdcdp()
                df = df.append(self.mdc_mdp.get_stock_data(trading_code,
                    dp_values['start_time'], dp_values['end_time'],
                    'Transaction'))
            else:
                self.__set_stockdatadp()
                df = df.append(self.mdp.get_stock_data(
                    trading_code, dp_values['start_time'], dp_values['end_time'], 'Transaction'))
        return df

    @event_trace
    def get_stock_order(self, trading_code, start_datetime, end_datetime, use_legacy_data=False):
        """
        证券委托数据查询服务：逐笔委托查询
        :param trading_code: string，单支股票代码，如："601688.SH"
        :param start_datetime:string，开始时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180301 093000000'
        :param end_datetime:string，结束时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180305 150000250'
        :return: DataFrame
        注意：按时间范围读取数据有最大范围限制，最长不能超过180天
        """
        if use_legacy_data:
            self.__set_stockdatadp()
            df = self.mdp.get_stock_data(
                        trading_code, start_datetime, end_datetime, 'Order')
            return df
        if trading_code.split('.')[1] == 'SH':
            self.__set_stockmdcdp()
            df = self.mdc_mdp.get_stock_data(trading_code, start_datetime,
                                        end_datetime, "Order")
        else:
            df = pd.DataFrame()
            for dp_type, dp_values in get_dataprovider('stock', 'Order', start_datetime, end_datetime).items():
                if dp_type == 'mdc_dp':
                    self.__set_stockmdcdp()
                    df = df.append(self.mdc_mdp.get_stock_data(trading_code,
                        dp_values['start_time'], dp_values['end_time'],
                        'Order'))
                else:
                    self.__set_stockdatadp()
                    df = df.append(self.mdp.get_stock_data(
                        trading_code, dp_values['start_time'], dp_values['end_time'], 'Order'))
        return df

    @event_trace
    def get_stock_kline(self, trading_code, start_datetime, end_datetime,
                        k_type='Kline1M4ZT', use_legacy_data=False):
        """
        证券K线查询服务:根据证券ID查询一段时间范围内的K线数据, 返回DataFrame对象
        :param trading_code: string，单支股票代码，如："601688.SH"
        :param start_datetime:string，开始时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180301 093000000'
        :param end_datetime:string，结束时间，格式为'YYYYmmdd HHMMSSsss'，示例：'20180305 150000250'
        :param k_type: int，k线时间间隔类型
        :return: DataFrame
        注意：按时间范围读取数据有最大范围限制，最长不能超过180天
        """
        if use_legacy_data:
            self.__set_stockdatadp()
            df = self.mdp.get_stock_data(
                    trading_code, start_datetime, end_datetime,
                    k_type)
            return df
        df = pd.DataFrame()
        for dp_type, dp_values in get_dataprovider(
                'stock', k_type, start_datetime, end_datetime).items():
            if dp_type == 'mdc_dp':
                self.__set_stockmdcdp()
                df = df.append(self.mdc_mdp.get_stock_data(trading_code,
                    dp_values['start_time'], dp_values['end_time'], k_type))
            else:
                self.__set_stockdatadp()
                df = df.append(self.mdp.get_stock_data(
                    trading_code, dp_values['start_time'], dp_values['end_time'],
                    k_type))
        return df

    @event_trace
    def get_stock_tick(self, trading_code, start_datetime,
                       end_datetime, trading_phase_code=[], use_legacy_data=False):
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
        if use_legacy_data:
            self.__set_stockdatadp()
            df = self.mdp.get_stock_data(
                    trading_code, start_datetime, end_datetime,
                    'Stock', trading_phase_code)
            return df
        df = pd.DataFrame()
        for dp_type, dp_values in get_dataprovider(
                'stock', 'Tick', start_datetime, end_datetime).items():
            if dp_type == 'mdc_dp':
                self.__set_stockmdcdp()
                df = df.append(self.mdc_mdp.get_stock_data(trading_code,
                    dp_values['start_time'], dp_values['end_time'],
                    'Stock', trading_phase_code))
            else:
                self.__set_stockdatadp()
                df = df.append(self.mdp.get_stock_data(
                    trading_code, dp_values['start_time'], dp_values['end_time'],
                    'Stock', trading_phase_code))

        return df

    @event_trace
    def get_plate_info(self, plate_type, date_time,
                       plate_id, use_prev_name=True):
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
        CS        中证行业分类
        ========  ==============

        - plate_type 为市场板块时，plate_id取值
        ========  ==============
        类型名称  类型说明
        ALLA       全部A股
        SHA        上海A股
        SZA        深圳A股
        GEM         创业板
        MBA           主板
        ========  ==============
        """
        if plate_type not in ['INDUSTRY', 'MARKET', 'CONCEPT']:
            raise Exception(
                "【plate_type】参数：板块类型，目前只支持行业板块(INDUSTRY)、市场板块(MARKET)、概念板块(CONCEPT)，请重新输入！")
        df = xqf.hset(
            plate_type,
            date_time,
            plate_id,
            use_prev_name=use_prev_name)
        return df

    @event_trace
    def get_stock_industry(self, trading_codes, date=dt.date.today().strftime("%Y%m%d"), industry_type=None,
                           industry_level=3, switch_flag='OFF'):
        """
        查询股票指定日期所属的指定级别行业信息，目前支持的行业类别有证监会新行业分类、中信行业分类、申万行业分类三种
        :param trading_codes: 单个股票代码 或 股票列表
        :param date:日期(string) ，默认为查询当天的日期，或为日期列表
        :param industry_type:行业类型，’CSRC’ 为证监会行业分类，’CITICS’ 为中信行业分类，’SW’ 为申万行业分类，默认全部行业
        :param industry_level:行业级别，取值[1,3]之间的整数，默认为三级行业，证监会行业只有两级分类取[1,2]的整数
        :param switch_flag: 是否过滤NAN值，取值'ON'或'OFF'，默认'OFF'不过滤
        :return:DataFrame
        """
        df = xqf.hsi(
            trading_codes,
            date,
            industry_type,
            industry_level,
            switch_flag)
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
        DELIST          STPT + 退市
        ========  ==============
        """
        df = xqf.stockFilter(
            stock_pool,
            filter_date,
            filter_type,
            use_prev_name)
        return df

    @event_trace
    def get_factor_alpha191(self, trading_codes, date_list,
                            factor_list, fill_na=False, sort_option=True):
        """
        获取alpha因子数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string 或 int)或日期列表或(开始日期,结束日期)的元组
        :param factor_list: 单个因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return:
        """
        if self.use_cache:
            return self.stock_method.get_factor_alpha191(
                trading_codes, date_list, factor_list, fill_na=fill_na,
                sort_option=sort_option)
        return self.stock_method.get_factor_alpha191(
            trading_codes, date_list, factor_list, fill_na, sort_option)

    @event_trace
    def get_factor_barra(self, trading_codes, date_list,
                         factor_list, fill_na=False, sort_option=True):
        """
        获取barra因子数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string 或 int)或日期列表或(开始日期,结束日期)的元组
        :param factor_list: 单个因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return:
        """
        if self.use_cache:
            return self.stock_method.get_factor_barra(
                trading_codes, date_list, factor_list, fill_na=fill_na,
                sort_option=sort_option)
        return self.stock_method.get_factor_barra(
            trading_codes, date_list, factor_list, fill_na, sort_option)

    @event_trace
    def get_factor_technical_analysis(
            self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取技术面因子数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string 或 int)或日期列表或(开始日期,结束日期)的元组
        :param factor_list: 单个因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return:
        """
        if self.use_cache:
            return self.stock_method.get_factor_technical_analysis(
                trading_codes, date_list, factor_list, fill_na=fill_na,
                sort_option=sort_option)
        return self.stock_method.get_factor_technical_analysis(
            trading_codes, date_list, factor_list, fill_na, sort_option)

    @event_trace
    def get_factors_info(self):
        """
        获取tquant所有因子的信息
        :return:
        """
        return util.get_factors_info()

    def get_tfactor_value(self, trading_codes, date_list,
                          factor_list, factor_lib=None, fill_na=False):
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
        result = self.__get_tfactor_value(
            trading_codes, date_list, factor_list, factor_lib, fill_na)
        return result

    def get_factor_lib(self, factor_list):
        factor_type2tb = {'market': ["factor_d_marketindex", "factor_day_marketindex", "factor_d_moneyflow"],
                          'valuation': ["factor_d_valuationmetricsindex", "factor_day_valuationmetricsindex"],
                          'riskanalysis': ["factor_d_riskanalysisindex", "factor_day_riskanalysisindex"],
                          'financialanalysis': ["factor_d_financialanalysisindex",
                                                "factor_day_financialanalysisindex_part1",
                                                "factor_day_financialanalysisindex_part2",
                                                "factor_day_financialanalysisindex_part3",
                                                "factor_day_financialanalysisindex_part4",
                                                "factor_day_financialanalysisindex_part5",
                                                "factor_d_financialanalysisindex_ext"],
                          'financialreport': ["factor_d_financialreportindex", "factor_day_financialreportindex",
                                              "factor_d_issuingdateindex", "factor_day_issuingdateindex"],
                          'newmsgindex': ["factor_d_newmsgindex", "factor_day_newmsgindex"],
                          'alpha': ["factor_day_alpha191_part1", "factor_day_alpha191_part2"],
                          'barra': ["factor_day_barra"],
                          'technicalanalysis': ["factor_day_technicalanalysis"],
                          'dividend': ["factor_day_dividendindex"],
                          'consensus': ['block_deviation2', 'block_deviation3', 'block_diversity',
                                        'con_forecast_c2_gics',
                                        'con_forecast_c2_idx', 'con_forecast_c2_stk', 'con_forecast_c2_sw',
                                        'con_forecast_c2_zx',
                                        'con_forecast_c3_cgb_gics', 'con_forecast_c3_cgb_idx',
                                        'con_forecast_c3_cgb_stk',
                                        'con_forecast_c3_cgb_sw', 'con_forecast_c3_gics', 'con_forecast_c3_idx',
                                        'con_forecast_c3_stk',
                                        'con_forecast_c3_sw', 'con_forecast_c3_zx', 'con_forecast_cb_gics',
                                        'con_forecast_cb_idx',
                                        'con_forecast_cb_stk', 'con_forecast_cb_sw', 'con_forecast_gics',
                                        'con_forecast_idx',
                                        'con_forecast_schedule', 'con_forecast_stk', 'con_forecast_sw',
                                        'con_forecast_zx',
                                        'con_per_gics', 'con_per_idx', 'con_per_sw', 'con_stock_deviation',
                                        'con_stock_deviation2',
                                        'con_stock_deviation3', 'stock_concern_level', 'stock_diversity',
                                        'stock_emotion',
                                        'stock_order2', 'stock_report_adjustment', 'stock_report_adjustment2',
                                        'stock_report_number'],
                          'momentum': ['factor_day_momentum'],
                          'emotion': ["factor_day_emotion"],
                          }
        factor_tb_dict = xqf.get_f_table(factor_list)
        factor_lib = []
        for factor_tb in factor_tb_dict:
            for type, tb_names in factor_type2tb.items():
                if factor_tb in tb_names:
                    factor_lib.append(type)
        if len(set(factor_lib)) > 1:
            raise Exception("该接口仅支持查询同一类型的因子")
        if len(set(factor_lib)) == 0:
            raise Exception("传入的因子列表中未找到属于13大类的因子")
        return factor_lib

    def __get_tfactor_value(self, trading_codes, date_list,
                            factor_list, factor_lib=None, fill_na=False):
        #  如果用户传了factor_lib（因子类型） 就不用去访问数据库找到表再对应到因子类型
        if isinstance(factor_lib, str):
            factor_lib = [factor_lib]
        if not factor_lib:
            factor_lib = self.get_factor_lib(factor_list)
        factor_lib = factor_lib[0]
        if factor_lib == "market":
            result = self.get_factor_price_daily(
                trading_codes, date_list, factor_list, fill_na)
        elif factor_lib == "valuation":
            result = self.get_factor_valuation_metrics(
                trading_codes, date_list, factor_list, fill_na)
        elif factor_lib == "riskanalysis":
            result = self.get_factor_risk_analysis(
                trading_codes, date_list, factor_list, fill_na)
        elif factor_lib == "financialanalysis":
            result = self.get_factor_financial_analysis(
                trading_codes, date_list, factor_list, fill_na)
        elif factor_lib == "financialreport":
            result = self.get_factor_financial_report(trading_codes, date_list, factor_list, statement_type='102',
                                                      fill_na=fill_na)
        elif factor_lib == "newmsgindex":
            result = self.get_factor_newsmsg(
                trading_codes, factor_list, fill_na)
        elif factor_lib == "alpha":
            result = self.get_factor_alpha191(
                trading_codes, date_list, factor_list, fill_na)
        elif factor_lib == "barra":
            result = self.get_factor_barra(
                trading_codes, date_list, factor_list, fill_na)
        elif factor_lib == "technicalanalysis":
            result = self.get_factor_technical_analysis(
                trading_codes, date_list, factor_list, fill_na)
        elif factor_lib == 'dividend':
            result = self.get_factor_dividend(
                trading_codes, date_list, factor_list, fill_na)
        elif factor_lib == 'consensus':
            result = self.get_factor_conforecast(
                trading_codes, date_list, factor_list, fill_na)
        elif factor_lib == 'momentum':
            result = self.get_factor_momentum(
                trading_codes, date_list, factor_list, fill_na)
        elif factor_lib == 'emotion':
            result = self.get_factor_emotion(
                trading_codes, date_list, factor_list, fill_na)
        elif factor_lib == 'barrarisk6':
            result = self.get_factor_barrarisk6(
                trading_codes, date_list, factor_list, fill_na)
        else:
            raise Exception(
                "此接口只支持'riskanalysis', 'momentum', 'emotion','dividend', 'consensus', 'financialanalysis', 'financialreport', 'valuation', 'market', 'newmsgindex', 'alpha', 'barra', 'technicalanalysis','barrarisk6'的因子查询！")
        return result

    def __get_quarter_day(self, dateList=[]):
        dateList = [int(i) for i in dateList]
        quaterDate = [None] * len(dateList)
        for i in range(len(dateList)):
            dateyear = math.floor(dateList[i] / 10000)
            datequater = math.ceil(
                math.floor(
                    (dateList[i] - dateyear * 10000) / 100) / 3)
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
        datequater = math.ceil(
            math.floor(
                (report_dt - dateyear * 10000) / 100) / 3)

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
    def get_finicial_cross_section_data(
            self, trading_codes, date_list, factor_list, publishDateType="ACCOUNTINGDAY"):
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
        if self.use_cache:
            return self.stock_method.get_finicial_cross_section_data(
                trading_codes, date_list, factor_list,
                publishDateType=publishDateType)
        assert len(
            date_list[0]) == 8, 'date_list error: 输入日期格式必须为‘YYYYmmdd’标准格式！'

        # 取有数据的前4个报告期
        quarter_days = self.__get_quarter_day(date_list)
        quarter_days = list(sorted(set(quarter_days)))
        min_quarter_day = min(quarter_days)

        if publishDateType == "ACCOUNTINGDAY":
            # 取前一年报告期
            report_dt_last_years = self.__get_report_dt_last_years(
                min_quarter_day, 1)
            tdate = quarter_days + report_dt_last_years
            tdate = list(sorted(set(tdate)))  # 日期去重
            # ,取前一年的报告期是消除0930到0430之间7个月一直不披露报告的极端情况
            df = self.__get_tfactor_value(
                trading_codes, tdate, factor_list, fill_na=True)
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
                                        data_result[factor][(
                                            day, stock)] = data[(tdate[d], stock)]
                                        predata = data[(tdate[d], stock)]
                                    else:
                                        data_result[factor][(
                                            day, stock)] = predata
                                except Exception as e:
                                    traceback.print_exc()
                                    data_result[factor][(day, stock)] = np.nan

        elif publishDateType == "TTM":
            report_dt_last_years = self.__get_report_dt_last_years(
                min_quarter_day, 2)
            report_dts = quarter_days + report_dt_last_years
            report_dts = list(sorted(set(report_dts)))  # 日期去重
            # ,取前一年的报告期是消除0930到0430之间7个月一直不披露报告的极端情况
            df = self.__get_tfactor_value(
                trading_codes, report_dts, factor_list, fill_na=True)
            df_p = self.__get_tfactor_value(
                trading_codes, report_dts, ['stm_issuingdate'], fill_na=True)

            df_dict = df.to_dict()
            data_result = {}  # 存放最终的计算数据

            for factor in factor_list:
                data = df_dict[factor]
                data_result[factor] = {}
                for stock in trading_codes:
                    publish_days = df_p.loc[(
                                                slice(None), stock), 'stm_issuingdate'].tolist()
                    publish_days = self.__standard_publish_days(
                        publish_days, report_dts)
                    # 查询对应的最近报告期
                    for d in range(len(publish_days)):
                        if d < 6:
                            continue
                        for day in date_list:
                            if day >= publish_days[d]:
                                quaterDate = int(
                                    report_dts[d]) - math.floor(int(report_dts[d]) / 10000) * 10000
                                import traceback
                                try:
                                    if quaterDate == 1231:
                                        data_result[factor][(day, stock)] = data[(
                                            report_dts[d], stock)]
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
            report_dt_last_years = self.__get_report_dt_last_years(
                min_quarter_day, 2)
            report_dts = quarter_days + report_dt_last_years
            report_dts = list(sorted(set(report_dts)))  # 日期去重
            # ,取前一年的报告期是消除0930到0430之间7个月一直不披露报告的极端情况
            df = self.__get_tfactor_value(
                trading_codes, report_dts, factor_list, fill_na=True)
            df_p = self.__get_tfactor_value(
                trading_codes, report_dts, ['stm_issuingdate'], fill_na=True)

            df_dict = df.to_dict()
            data_result = {}  # 存放最终的计算数据

            for factor in factor_list:
                data = df_dict[factor]
                data_result[factor] = {}
                for stock in trading_codes:
                    publish_days = df_p.loc[(
                                                slice(None), stock), 'stm_issuingdate'].tolist()
                    publish_days = self.__standard_publish_days(
                        publish_days, report_dts)
                    predata = np.nan
                    # 查询对应的最近报告期
                    for d in range(len(publish_days)):
                        for day in date_list:
                            if day >= publish_days[d]:
                                import traceback
                                try:
                                    if not pd.isnull(
                                            data[(report_dts[d], stock)]):
                                        data_result[factor][(day, stock)] = data[(
                                            report_dts[d], stock)]
                                        predata = data[(report_dts[d], stock)]
                                    else:
                                        data_result[factor][(
                                            day, stock)] = predata
                                except Exception as e:
                                    traceback.print_exc()
                                    data_result[factor][(day, stock)] = np.nan

        else:
            raise Exception(
                "publishDateType Type Error: 请输出publishDateType正确的参数类型：ACCOUNTINGDAY， PUBLISHDAY， TTM！")

        df_result = pd.DataFrame(data_result)
        df_result.index.names = ['mddate', 'stock']
        df_result = df_result.unstack('stock')
        df_result = df_result.fillna(method='ffill')

        df_result = df_result.loc[date_list, :]
        df_result = df_result.stack("stock", dropna=False)

        return df_result

    def get_factor_evaluation(
            self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取评价因子数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string 或 int)或日期列表
        :param factor_list: 单个因子或因子列表
        :return:
        """
        if self.use_cache:
            return self.stock_method.get_factor_evaluation(
                trading_codes, date_list, factor_list, fill_na=fill_na,
                sort_option=sort_option)
        return self.stock_method.get_factor_evaluation(
            trading_codes, date_list, factor_list, fill_na, sort_option)

    def get_factor_emotion(self, trading_codes, date_list,
                           factor_list, fill_na=False, sort_option=True):
        """
        获取情绪类数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string 或 int)或日期列表
        :param factor_list: 单个因子或因子列表
        :return:
        """
        if self.use_cache:
            return self.stock_method.get_factor_emotion(
                trading_codes, date_list, factor_list, fill_na=fill_na,
                sort_option=sort_option)
        return self.stock_method.get_factor_emotion(
            trading_codes, date_list, factor_list, fill_na, sort_option)

    def get_factor_momentum(self, trading_codes, date_list,
                            factor_list, fill_na=False, sort_option=True):
        """
        获取动量类数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string 或 int)或日期列表
        :param factor_list: 单个因子或因子列表
        :return:
        """
        if self.use_cache:
            return self.stock_method.get_factor_momentum(
                trading_codes, date_list, factor_list, fill_na=fill_na,
                sort_option=sort_option)
        return self.stock_method.get_factor_momentum(
            trading_codes, date_list, factor_list, fill_na, sort_option)

    @event_trace
    def get_factor_barrarisk6(
            self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取barrarisk6因子数据
        :param trading_codes: 单支股票代码或多支股票的列表
        :param date_list: 日期(string 或 int)或日期列表或(开始日期,结束日期)的元组
        :param factor_list: 单个因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return:
        """
        if self.use_cache:
            return self.stock_method.get_factor_barrarisk6(
                trading_codes, date_list, factor_list, fill_na=fill_na,
                sort_option=sort_option)
        return self.stock_method.get_factor_barrarisk6(
            trading_codes, date_list, factor_list, fill_na, sort_option)

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
        df = get_source_factor_value(trading_codes, date_list, factor_list, table_name, category='stock',
                                     ROLLING_TYPE=ROLLING_TYPE,
                                     CONSEN_DATA_CYCLE_TYP=CONSEN_DATA_CYCLE_TYP, S_EST_YEARTYPE=S_EST_YEARTYPE,
                                     S_WRATING_CYCLE=S_WRATING_CYCLE, **kwargs)
        return df

    @event_trace
    def get_source_table_value(self, table_name, factor_list, date_list=[], **kwargs):
        """
        查询行业景气度数据源表
        :param stock_list: 股票列表，传[] 查询所有股票
        :param date_list: 日期列表, 如果为空，不从缓存查询，如果不为空，从缓存查询，速度更快。date_list对应源表中的固定字段，具体参考文档。
        :param factor_list: 因子列表，为空时查询所有因子数据。
        :param ROLLING_TYPE: 条件，list类型，默认['FY2']，如果为[]则为无筛选条件，返回日期股票的所有数据
        :param CONSEN_DATA_CYCLE_TYP: 条件，list类型，默认['263003000']，如果为[]则为无筛选条件，返回日期股票的所有数据
        :param S_EST_YEARTYPE: 条件，list类型，默认['FY2']，如果为[]则为无筛选条件，返回日期股票的所有数据
        :param S_WRATING_CYCLE: 条件，list类型，默认['263003000']，如果为[]则为无筛选条件，返回日期股票的所有数据
        :return:
        """
        df = get_source_table_value(table_name, factor_list, date_list, **kwargs)
        return df

    @event_trace
    def get_factor_insideholder(
            self, trading_codes, date_list, factor_list, fill_na=False, sort_option=True):
        """
        获取股东因子数据
        :param trading_codes: 股票代码或股票代码列表
        :param date_list: 日期(string)或多个日期的列表
        :param factor_list: 因子或因子列表
        :param fill_na: bool: 默认False， 若为True，则入参的每个stock和mddate都有返回值，没有值时填充NAN。
        :param sort_option: 排序选项：是否对查询数据的结果按照索引进行排序，默认True
        :return: 索引为[日期,股票] 的MultiIndex DataFrame
        """
        #if self.use_cache or self.data_source != 'wind':
        #    raise Exception("只支持万得非缓存数据，实例化参数：data_source='wind',use_cache=False")
            # return self.stock_method._get_insideholder(
            #     trading_codes, date_list, factor_list, fill_na=fill_na,
            #     sort_option=sort_option)
        return self.stock_method.get_insideholder(
            trading_codes, date_list, factor_list, fill_na, sort_option=sort_option)

    @event_trace
    def get_factor_characteristic(self, trading_codes=None, factor_list=[], date_list=[],
                                   sort=False):
        self.__set_sqlfactor()
        if not factor_list or not date_list:
            raise Exception("factor_list和date_list不能为空")
        return self.fs.read_low_freq_factors(factor_list, date_list,
                                            stock_list=trading_codes, sort=sort)

    @event_trace
    def get_stock_data_day(self, exchange_house, date, bar_size,
                              trading_phase_code=None, sort_by_receive_time=False):
        self.__set_stockmdcdp()
        df = self.mdc_mdp.get_stock_data_by_day(
            bar_size=bar_size, date=date, exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df

    @event_trace
    def get_stock_tick_by_exchange(self, exchange_house, date,
                                   trading_phase_code=None,
                                   sort_by_receive_time=False):
        self.__set_stockmdcdp()
        df = self.mdc_mdp.get_stock_data_by_day(
            bar_size='stock',
            date=date,
            exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df

    @event_trace
    def get_stock_transaction_by_exchange(self, exchange_house, date,
                                          trading_phase_code=None,
                                          sort_by_receive_time=False):
        self.__set_stockmdcdp()
        df = self.mdc_mdp.get_stock_data_by_day(
            bar_size='transaction',
            date=date,
            exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df

    @event_trace
    def get_stock_order_by_exchange(self, exchange_house, date,
                                    trading_phase_code=None,
                                    sort_by_receive_time=False):
        self.__set_stockmdcdp()
        df = self.mdc_mdp.get_stock_data_by_day(
            bar_size='order',
            date=date,
            exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df

    @event_trace
    def get_stock_kline_by_exchange(self, exchange_house, date, bar_size,
                                    trading_phase_code=None,
                                    sort_by_receive_time=False):
        bar_size = bar_size.lower()
        if bar_size not in ['kline1m4zt', 'kline5m4zt', 'kline10m4zt',
                            'kline60m4zt']:
            raise Exception(
                'bar_size必须在kline1m4zt,kline5m4zt,kline10m4zt,kline60m4zt中')
        self.__set_stockmdcdp()
        df = self.mdc_mdp.get_stock_data_by_day(
            bar_size=bar_size,
            date=date,
            exchange_house=exchange_house,
            trading_phase_code=trading_phase_code,
            sort_by_receive_time=sort_by_receive_time)
        return df
