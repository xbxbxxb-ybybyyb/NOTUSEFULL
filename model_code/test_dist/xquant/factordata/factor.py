try:
    multicore_init = None
    from xquant.xqutils.helper import multicore_init
    import ray
except:
    pass
from xquant.factordata.factorenum import *
from xquant.xqutils.utils import statisticLog
from xquant.xqutils.tracking import factor_statistic
from FactorProvider.factordata import psfactor, xqfactor
from xquant.thirdpartydata.factordata import FactorData as TFactorData
import pandas as pd
import os
import math
import datetime
import numpy as np
import re
import time
import traceback
import pickle

try:
    @ray.remote
    def get_factor_value_to_pickle(library_name,factor_list,stock_list,date, save_path):
        try:
            s = FactorData()
            path = os.path.join(save_path, '{0}.pkl'.format(date))
            result_dic = []
            for stock in stock_list:
                try:
                    df = s.get_factor_value(library_name, stock, date, factor_list)
                except AttributeError as e:
                    df = pd.DataFrame()
                result_dic.append(((stock, date),df))
            with open(path, 'wb') as fw:
                pickle.dump(result_dic, fw)
            return path
        except Exception:
            print(traceback.print_exc())
except:
    def get_factor_value_to_pickle(library_name,factor_list,stock,date_list, save_path):
        return
    pass



def singleton(FactorData):
    _instance = {}

    def inner():
        if os.getpid() not in _instance:
            _instance[os.getpid()] = FactorData()
        return _instance[os.getpid()]

    return inner


#@singleton
class FactorData():
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            return cls.__instance
        else:
            obj = object.__new__(cls)
            cls.__instance = obj
            cls.__instance.__initialized = False
            return cls.__instance

    @statisticLog('factordata', 'FactorData')
    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        self.person_factor = psfactor.FactorData()
        self.basic_factor = "Basic_factor"
        self.operation_data = "operation_data"
        self.factor_vip = "Wind_vip"
        self.wind_us = "Wind_vip_us"
        self.wind_commodity = "Wind_vip_commodity"

    def __transformation(self, Contain_a):
        """
        将列表转换为字典，减少遍历时间
        :param L:列表
        :return:
        """
        tmp_dict = {}
        for i in Contain_a:
            tmp_dict[i] = 1
        return tmp_dict

    @statisticLog('factordata', 'FactorData')
    def create_factor_library(self, library_name, library_type):
        """
        根据参数library_name创建因子库
        :param library_name: 库名
        :param library_type: 类型（T+0：高频，Alpha：非高频）
        :return:
        范例：
        from xquant.factordata import FactorData
        s = FactorData()
        s.create_factor_library("xx_low_22","Alpha")
        s.create_factor_library("xx_high23","T+0")
        #返回：
        True
        """
        return self.person_factor.create_factor_library(library_name, library_type)

    @statisticLog('factordata', 'FactorData')
    def add_factor(self, library_name, factor_names):
        """
        向library_name的因子库中增加因子
        :param library_name: 库名
        :param factor_names: 因子名列表
        :return:
        范例：
        from xquant.factordata import FactorData
        s = FactorData()
        s.add_factor("xx_low_21","low1")
        #返回：
        True
        """
        return self.person_factor.add_factor(library_name, factor_names)

    @statisticLog('factordata', 'FactorData')
    def remove_factor(self, library_name, factor_names):
        """
        删除指定因子库相关因子
        :param library_name: 因子库名
        :param factor_names: 因子名列表
        :return:
        范例：
        from xquant.factordata import FactorData
        s = FactorData()
        s.remove_factor("xx_low_22", "low1")
        #返回：
        True
        """
        return self.person_factor.remove_factor(library_name, factor_names)

    @statisticLog('factordata', 'FactorData')
    def create_signal_library(self, library_name):
        """
        根据参数library_name创建信号库
        :param library_name: 库名
        :return:
        范例：
        from xquant.factordata import FactorData
        s = FactorData()
        s.create_signal_library("xx_high_23")
        #返回：
        True
        """
        return self.person_factor.create_signal_library(library_name)

    @statisticLog('factordata', 'FactorData')
    def add_signal(self, library_name, signal_names):
        """
        向library_name的信号库中增加信号
        :param library_name: 库名
        :param factor_names: 信号列表
        :return:状态(成功返回True)
        范例：
        from xquant.factordata import FactorData
        s = FactorData()
        s.add_signal("xx_high_23","high1")
        #返回：
        True
        """
        return self.person_factor.add_signal(library_name, signal_names)

    @statisticLog('factordata', 'FactorData')
    def remove_signal(self, library_name, signal_names):
        """
        删除指定信号库相关信号
        :param library_name: 因子库名
        :param factor_names: 因子名列表
        :return:
        范例：
        from xquant.factordata import FactorData
        s = FactorData()
        s.remove_signal("xx_high_23", "high1")
        #返回：
        True
        """
        return self.person_factor.remove_signal(library_name, signal_names)

    @statisticLog('factordata', 'FactorData')
    def update_factor_value(self, library_name, factor_values, stock=None, mddate=None, delete_range=False,
                            disable_progress=False, cell_size = None):
        """
        更新指定因子库中的因子值
        :param library_name: 因子库名
        :param factor_values: stock，mddate两列索引的dataframe
        :param stock: 股票
        :param mddate: 日期
        :return:
        """
        # 查找所有库名，判断用户输入的库名是否存在
        return self.person_factor.update_factor_value(library_name, factor_values, stock=stock, mddate=mddate,
                                                      delete_range=delete_range, disable_progress=disable_progress,
                                                      cell_size = cell_size)

    def __get_basic_factor(self, symbols, dates, factor_names, statement_type, stock_type, block_type, fill_na,
                           daily_bar_num=242):
        """
        查询基础因子
        :param symbols: 股票
        :param dates: 日期
        :param factor_names:因子
        :return:
        """
        factor_info = self.person_factor.get_factor_info(self.basic_factor)
        basic_info_dict = factor_info["factorInfo"]
        basic_factor_dict = {
            2: [],
            3: [],
            4: [],
            5: [],
            6: [],
            7: [],
            8: [],
            9: [],
            10: [],
            2500: [],
            2600: [],
            2700: []
        }
        for factor in factor_names:
            # 将对应的因子放到对应的列表中
            basic_factor_dict[basic_info_dict[factor]['idInfo'][-2]].append(factor)
        df_list = []
        if basic_factor_dict[2600]:
            # 可转债行情指标
            df_list.append(xqfactor.get_bond_market_data(symbols, dates, basic_factor_dict[2600], fill_na=fill_na))
        if basic_factor_dict[2700]:
            # 可转债估值指标
            df_list.append(xqfactor.get_bond_value_data(symbols, dates, basic_factor_dict[2700], fill_na=fill_na))
        if basic_factor_dict[2500]:
            # 行业数据
            df_list.append(xqfactor.get_industry_data(symbols, dates, basic_factor_dict[2500]))
        if basic_factor_dict[2]:
            # 行情指标(指数)
            df_list.append(xqfactor.get_market_price(symbols, dates, basic_factor_dict[2], fill_na=fill_na,
                                                     daily_bar_num=daily_bar_num))
        if basic_factor_dict[3] or basic_factor_dict[9]:
            # 估值指标、风险分析
            df_list.append(
                xqfactor.get_factor_idct(symbols, dates, basic_factor_dict[3] + basic_factor_dict[9], fill_na=fill_na))
        if basic_factor_dict[4]:
            # 财务报表
            df_list.append(
                xqfactor.get_finance_report(symbols, dates, basic_factor_dict[4], statement_type, fill_na=fill_na))
        if basic_factor_dict[5]:
            # 分红指标
            df_list.append(xqfactor.get_divid(symbols, dates, basic_factor_dict[5], fill_na=fill_na))
        if basic_factor_dict[8]:
            # 财务分析
            df_list.append(xqfactor.get_finance_idct(symbols, dates, basic_factor_dict[8], fill_na=fill_na))
        if basic_factor_dict[6]:
            # 最新信息
            if df_list:
                raise Exception("请单独查询最新信息数据" + str(basic_factor_dict[6]) + "！")
            df_list.append(xqfactor.get_stock_info(symbols, basic_factor_dict[6], fill_na=fill_na))
        if basic_factor_dict[7]:
            # 一致预期
            if df_list:
                raise Exception("请单独查询一致预期数据" + str(basic_factor_dict[7]) + "！")
            return xqfactor.get_conforecast(symbols, dates, basic_factor_dict[7], stock_type, block_type,
                                            fill_na=fill_na)
        if basic_factor_dict[10]:
            df_list.append(xqfactor.get_insideholder(symbols, dates, basic_factor_dict[10], fill_na=fill_na))
        new_df = pd.concat(df_list, axis=1)

        return new_df

    def __time_standard(self, time):
        '''
        将输入日期格式转化成YYYYMMDD统一格式
        **参数**
                time：str或datetime类型的时间
        **返回**
                YYYYMMDD统一格式的时间
        '''
        if time == None:
            raise Exception("日期不能为空！")
        if isinstance(time, str):
            if len(re.findall("\d{4}-\d{2}-\d{2}", time)) != 0:
                time = re.sub("-", "", time)
            elif len(re.findall("\d{8}", time)) != 0:
                pass
            else:
                raise Exception("请输入正确的str时间格式！YYYY-MM-DD或YYYYMMDD")
        elif isinstance(time, datetime.datetime):
            time = time.strftime("%Y%m%d")
        else:
            raise Exception("请输入正确的时间格式,str或datetime类型")
        return time

    @factor_statistic('factordata')
    def get_factor_value(self, library_name, stock=None, mddate=None, factor_names=None, statement_type=STYPE.COMBINED,
                         stock_type=1, block_type=4, fill_na=False, use_mysql=False, return_single_factor=False,
                         daily_bar_num=242, sort_option=True, category='stock', **kwargs):
        """
        查询指定因子库中的因子值
        :param library_name: 因子库名、万得源表名(例："WIND_AIndexEODPrices")
        :param stock: 股票，查询万得源表时可不传改参数
        :param mddate: 日期，查询万得源表时可不传改参数
        :param factor_names:因子，查询万得源表时可不传改参数
        :param category: 可选品类，股票为'stock',债券为'bond'，默认为'stock'
        :param kwargs：关键字参数，factors=[column1,column2,...] 或 factors="column" 为需要查询的列（不传则为select *）；
                    其他关键字参数则作为where的条件处理，单个数值或字符串对应的条件运算符为"="，列表对应的运算符为"in",
                    同时支持>,<,>=,<=,!= 等简单查询条件，支持column='is not null' 筛选此列不为空的数据，详情请见示例。
        :return:指定因子库中的因子值

        """
        if return_single_factor and len(factor_names) > 1:
            raise Exception("use_single_factor参数只能在因子个数为一个时设为True!")
        if category not in ['stock', 'bond']:
            raise Exception("【category】参数为可选品类，股票为'stock',债券为'bond'，请重新输入！")
        if return_single_factor:
            fill_na = True
        if library_name[:4] == "WIND":
            tfd = TFactorData()
            return tfd.get_factor_value(library_name, stock, mddate, factor_names, statement_type, stock_type,
                                        block_type, fill_na, use_mysql, return_single_factor, daily_bar_num,
                                        sort_option, category, **kwargs)
        elif library_name[:6] == "GOGOAL":
            tfd = TFactorData()
            return tfd.get_factor_value(library_name, stock, mddate, factor_names, statement_type, stock_type,
                                        block_type, fill_na, use_mysql, return_single_factor, daily_bar_num,
                                        sort_option, category, **kwargs)
        else:
            if mddate == None or factor_names == None:
                raise Exception("mddate，factor_names 参数不能为空！")
            impersonal_library = [self.basic_factor, self.operation_data, self.factor_vip, self.wind_us,
                                  self.wind_commodity]
            if not stock and library_name in impersonal_library:
                max_date = sorted(mddate)[-1]
                stock = self.person_factor.get_his_stock(max_date, category)
            catalog_id_dict = self.person_factor.get_factor_info(library_name)
            if not catalog_id_dict:
                raise Exception("library_name doesn't exist: %s因子库不存在！" % library_name)
            if catalog_id_dict["libraryType"] == 1:
                # 非高频操作
                if not type(factor_names) == list:
                    raise Exception("factor names 请传入列表!")
                if not type(mddate) == list:
                    raise Exception("mddate 请传入列表!")
                if not type(stock) == list and library_name in impersonal_library:
                    raise Exception("stock 请传入列表!")
                    # 如果category为bond则在因子前加上bond_前缀
                if category == "bond":
                    factor_names = ['bond_' + i for i in factor_names]
                # 得到该库所有因子名
                factor_symbols = list(catalog_id_dict["factorInfo"].keys())
                factor_symbols_dict = self.__transformation(factor_symbols)
                for factor_name in factor_names:
                    if factor_symbols_dict.get(factor_name) == None:
                        raise Exception("factor_name doesn't exist: %s因子不存在！" % factor_name)
                new_dates = []
                for dt in mddate:
                    dt = self.__time_standard(dt)
                    new_dates.append(dt)
                # 针对基础因子操作：
                if library_name == self.basic_factor:
                    if not return_single_factor and daily_bar_num == 240:
                        raise Exception(
                            "【Error】当前查询条件不支持！原因为当daily_bar_num参数置为240时，仅适合查询单个分钟因子并且return_single_factor为True的场景！")
                    basic_df = self.__get_basic_factor(stock, new_dates, factor_names, statement_type, stock_type,
                                                       block_type, fill_na, daily_bar_num=daily_bar_num)
                    if return_single_factor and daily_bar_num != 240:
                        # daily_bar_num为240时，已经是普通的dataframe，不需要unstack
                        basic_df = basic_df.iloc[:, 0]
                        basic_df = basic_df.unstack()
                    return basic_df
                # 针对运营数据操作
                if library_name == self.operation_data:
                    operation_data = self.person_factor.__get_operation_data(stock, new_dates, factor_names, fill_na,
                                                                             sort_option)
                    df = operation_data[0]
                    if operation_data[1] != 200:
                        raise Exception(operation_data[0])
                    if return_single_factor:
                        df = df.iloc[:, 0]
                        df = df.unstack()
                    return df
                # 针对factor_vip数据操作
                if library_name == self.factor_vip:
                    factor_vip_data = xqfactor.get_factor_vip_data(stock, mddate, factor_names, statement_type,
                                                                   "wind_vip", fill_na)
                    if return_single_factor:
                        factor_vip_data = factor_vip_data.iloc[:, 0]
                        factor_vip_data = factor_vip_data.unstack()
                    return factor_vip_data
                if library_name == self.wind_us:
                    factor_vip_data = xqfactor.get_factor_vip_data(stock, mddate, factor_names, statement_type,
                                                                   "wind_vip_us", fill_na)
                    if return_single_factor:
                        factor_vip_data = factor_vip_data.iloc[:, 0]
                        factor_vip_data = factor_vip_data.unstack()
                    return factor_vip_data
                if library_name == self.wind_commodity:
                    factor_vip_data = xqfactor.get_factor_vip_data(stock, mddate, factor_names, statement_type,
                                                                   "wind_vip_commodity", fill_na)
                    if return_single_factor:
                        factor_vip_data = factor_vip_data.iloc[:, 0]
                        factor_vip_data = factor_vip_data.unstack()
                    return factor_vip_data

                # print(self, library_name, stock, mddate, factor_names, fill_na, return_single_factor, sort_option)
                return self.person_factor.get_factor_value(library_name, stock=stock, mddate=mddate,
                                                           factor_names=factor_names, fill_na=fill_na,
                                                           return_single_factor=return_single_factor,
                                                           sort_option=sort_option)
            # 针对个人的高频因子操作：
            else:
                return self.person_factor.get_factor_value(library_name, stock=stock, mddate=mddate,
                                                           factor_names=factor_names, fill_na=fill_na,
                                                           return_single_factor=return_single_factor,
                                                           sort_option=sort_option)

    @statisticLog('factordata', 'FactorData')
    def update_signal(self, library_name, stock, mddate, signal_values):
        """
        更新某一只股票某一天的信号值
        :param library_name: 信号库名
        :param stock: 股票
        :param mddate: 日期
        :param signal_values:信号值 （time为索引的dataframe）
        :return:
        """
        return self.person_factor.update_signal(library_name, stock, mddate, signal_values)

    @statisticLog('factordata', 'FactorData')
    def get_signal(self, library_name, stock, mddate, signal_names):
        """
        在指定信号库中取出单个股票、单天的各信号值，返回dataframe
        :param library_name:信号库名
        :param stock:股票
        :param date:日期
        :param signal_names:信号名
        :return:dataframe
        """
        return self.person_factor.get_signal(library_name, stock, mddate, signal_names)

    @statisticLog('factordata', 'FactorData')
    def search_by_stock_factor(self, library_name, stock, factor, datelist):
        """
        按因子库名、股票、因子查询指定日期列表中哪些日期有数据
        :param library_name: 因子库名
        :param stock:股票
        :param factor:因子
        :param datelist:日期列表
        :return:日期列表
        """
        return self.person_factor.search_by_stock_factor(library_name, stock, factor, datelist)

    @statisticLog('factordata', 'FactorData')
    def search_by_stock_date(self, library_name, stock, mddate, factorlist):
        """
        按因子库名、股票、日期查询在指定因子列表中哪些因子有数据
        :param library_name: 因子库名
        :param stock: 股票
        :param mddate: 日期
        :param factorlist: 因子列表
        :return: 因子列表

        """
        return self.person_factor.search_by_stock_date(library_name, stock, mddate, factorlist)

    @statisticLog('factordata', 'FactorData')
    def search_by_stock(self, library_name, stock, datelist):
        """
        按因子库名、股票查询指定日期列表中哪些天有数据
        :param library_name:因子库名
        :param stock:股票
        :param datelist:日期列表
        :return:日期列表
        范例：
        from xquant.factordata import FactorData
        s = FactorData()
        date_list = s.search_by_stock("xx_high_23","SH001", ["20190326", "20190327", "20190328", "20190325"])
        print(date_list)
        """
        return self.person_factor.search_by_stock(library_name, stock, datelist)

    @statisticLog('factordata', 'FactorData')
    def search_by_date(self, library_name, mddate, stocklist):
        """
        按因子库名、日期查询指定股票列表中哪些股票有数据
        :param library_name:因子库名
        :param mddate:日期
        :param stocklist:股票列表
        :return:股票列表
        """
        return self.person_factor.search_by_date(library_name, mddate, stocklist)

    @statisticLog('factordata', 'FactorData')
    def remove_factor_value(self, library_name, stock, mddate, factor_names):
        """
        删除指定因子库中的因子的值
        :param library_name:因子库
        :param stock:股票代码
        :param tdate:日期
        :param factor_names:因子名列表
        :return:
        """
        return self.person_factor.remove_factor_value(library_name, stock, mddate, factor_names)

    @statisticLog('factordata', 'FactorData')
    def get_library_info(self):
        """
        得到该用户所有的有权限访问的库信息和该库下面的所有因子信息
        :return:
        """
        return self.person_factor.get_library_info()

    @statisticLog('factordata', 'FactorData')
    def tradingday(self, startTime, endTime, frequency='DAY', dayType=None, dateType='TRADINGDAYS', location='CN'):
        """
            通过输入的起止时间、日期类型、星期属性等参数，返回在这些条件下的交易日期列表
            :param startTime: 开始时间，格式yyyymmdd，int(20180102) 或string('20180102')
            :param endTime:结束时间，格式yyyymmdd，int(20180105) 或string('20180105')，frequency为DAY时可为非零整数：
                    以startTime为起点，前后n日的时间序列查询(abs(n) <= 10000，n>10000则最多输出10000条数据)，例如，查询以20180102前10个交易日的序列，
                    可以输入：tradingDay(20180102, -10)，后面20日：tradingDay(20180102, 20)
            :param frequency: 数据频率，默认DAY，取值详见参数说明
            :param dayType:日期类型，当frequency 参数为WEEK 时，默认值为FRIDAY；
                            当frequency 参数为其它值，默认值为LASTDAY，frequency为DAY时dayType取值无影响,
                            frequency取值MONTH或YEAR时，dayType仅支持FIRSTDAY、LASTDAY，取值详见参数说明
            :param dateType:日历类型，默认值TRADINGDAYS，取值详见参数说明
            :param location: 股票市场，'CN':国内A股，'HK':港股，'US':美股，默认为'CN'
            :return: 交易日列表(list)
        """
        tradingdays = xqfactor.tradingDay(startTime, endTime, frequency=frequency, dayType=dayType, dateType=dateType, location=location)
        return tradingdays

    @statisticLog('factordata', 'FactorData')
    def hset(self, plateType, dateTime, plateID, weightType=0):
        """
            通过输入的板块类型、时间和板块ID，输出该板块的成分股，如果是指数板块的时候，还会返回成分股的权重
            :param plateType:参数类型，目前只支持行业板块(INDUSTRY)、指数板块(INDEX)、市场板块(MARKET)三个类型
            :param dateTime:查询日期，格式yyyymmdd,例如:20100801
            :param plateID:当plateType为指数板块时，plateID输入为指数代码,如：'HS300'，详见参数说明；
                            当plateType 为行业板块时，plateID为行业代码，如： 'CITICS.b106040700'、'SW.s6110'，详见参数说明
                            支持的行业请参见行业代码表；
                            当plateType 为市场板块时，plateID可取'ALLA'(全部A股)，'SHA'(上海A股)，'SZA'(深圳A股)
            :param weightType: int型，当plateType为指数板块(INDEX)时，0表示当日权重，1表示次日权重
            :return:
            """
        return xqfactor.hset(plateType, dateTime, plateID, weightType)

    @statisticLog('factordata', 'FactorData')
    def hind(self, industryType, level=0):
        """
            根据输入的行业类别、级别查询该类别行业代码信息
            :param industryType:行业类型，'CSRC' 为证监会行业分类，'CITICS' 为中信行业分类，'SW' 为申万行业分类
            :param level: 级别，取值[0,3]之间整数，默认0，证监会行业只有两级分类取值[0,2]之间的整数
            :return:
            """
        return xqfactor.hind(industryType, level=level)

    @statisticLog('factordata', 'FactorData')
    def hsi(self, stock, mddate=datetime.date.today().strftime("%Y%m%d"), industryType=None, industryLevel=3,
            switchFlag='OFF'):
        """
            查询股票指定日期所属的指定级别行业信息，目前支持的行业类别有证监会新行业分类、中信行业分类、申万行业分类三种
            :param stock: 股票代码 或 股票列表
            :param date: 日期(string 或 int) ，默认为查询当天的日期
            :param industryType: 行业类型，'CSRC' 为证监会行业分类，'CITICS' 为中信行业分类，'SW' 为申万行业分类，默认全部行业
            :param industryLevel: 行业级别，取值[1,3]之间的整数，默认为三级行业，证监会行业只有两级分类取[1,2]的整数
            :return: 索引为trading_code的DataFrame
            """
        return xqfactor.hsi(stock, date=mddate, industryType=industryType, industryLevel=industryLevel,
                            switchFlag=switchFlag)

    @statisticLog('factordata', 'FactorData')
    def stock_filter(self, stockPool, filterDate=datetime.date.today().strftime("%Y%m%d"), filterType='SSO'):
        """
            过滤股票池中不符合条件的股票。过滤掉STPT，停牌，开盘涨停等股票
            :param stockPool: 股票池，列表类型
            :param filterDate:查询日期,数值型，例如：20151231，默认查询当天日期
            :param filterType: 过滤类型，默认为过滤掉STPT，停牌，开盘涨停的股票，引用格式：StockFilterType.SSO
            :return: DataFrame
            """
        return xqfactor.stockFilter(stockPool, filterDate=filterDate, filterType=filterType)

    @statisticLog('factordata', 'FactorData')
    def get_qtrdate_list(self, start_date, end_date):
        """
        获取季末日期列表
        :param start_date: 开始日期，int型，例：20180105
        :param end_date: 结束日期，int型，例：20181231
        :return:
        """
        qtrdate_list = xqfactor.get_all_qtr(start_date, end_date)
        return qtrdate_list

    # 计算给定日期列表的会计期间
    @statisticLog('factordata', 'FactorData')
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

    @factor_statistic('factordata')
    def get_factor_value_ray(self, num_cpu,library_name,stock_list, date_list, factor_list):
        assert multicore_init() == True
        save_path = os.path.join("/tmp/ray_tmp/",str(os.getpid()) + "_" + str(int(time.time())))
        try:
            os.makedirs(save_path)
        except Exception as e:
            print(e)
        ray.init(num_cpus=num_cpu, ignore_reinit_error = True)
        ray_task_list = [get_factor_value_to_pickle.remote(library_name, factor_list,stock_list, date, save_path) for date in date_list]
        result_dic = {}
        while(len(ray_task_list)):
            done_tasks, ray_task_list = ray.wait(ray_task_list, num_returns=1)
            path = ray.get(done_tasks[0])
            with open(path, 'rb') as fr:
                result_dic_sub = pickle.load(fr)
            for k,v in result_dic_sub:
                if not result_dic.get(k[0]):
                    result_dic[k[0]] = {}
                result_dic[k[0]][k[1]] = v
        os.system("rm -rf {}".format(save_path))
        return result_dic

    @statisticLog('factordata', 'FactorData')
    def hdf(self, trading_codes, date_list, factor_list, publishDateType="ACCOUNTINGDAY"):
        """本API用于查询日度财务指标指定股票列表的时间序列因子数据，或者横截面因子数据。通过输入股票列表、因子列表以及起止日期，输出不同因子类型下的因子数值。

    :param stockList: 股票代码列表，字符型cell列向量，例如：{‘000001.SZ’;’601688.SH’};
    :param factorList: 因子名称列表，枚举列向量，例如：[Factors.high;Factors.low]。详情请见因子列表;
    :param dateList: 数据日期列表，数值型列向量，格式 yyyymmdd,例如: [20100816;20100921]
    :param publishDateType: dtr，匹配日期类型，ACCOUNTINGDAY：会计报表日期，PUBLISHDAY：公告披露日期，默认公告披露日期， TTM:以披露日期为标准的前12个月财务数据
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
            df = self.get_factor_value('Basic_factor', trading_codes, tdate, factor_list, fill_na=True)
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
            df = self.get_factor_value('Basic_factor', trading_codes, report_dts, factor_list, fill_na=True)
            df_p = self.get_factor_value('Basic_factor', trading_codes, report_dts, ['stm_issuingdate'], fill_na=True)

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
            df = self.get_factor_value('Basic_factor', trading_codes, report_dts, factor_list, fill_na=True)
            df_p = self.get_factor_value('Basic_factor', trading_codes, report_dts, ['stm_issuingdate'], fill_na=True)

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

    def get_index_weight_next_day_csi(self, dateTime, plateID):
        """
        次日权重原始数据
        :param dateTime: 查询日期，str、int或者list，格式yyyymmdd，如20191231
        :param plateID: 指数代码，如HS300，详见参数说明
        :return:

        - plateID 指数代码
            ============  ===========  =============
            类型名称      类型说明     数据开始日期
            HS300         沪深300指数   20050411
            ZZ500         中证500指数   20100104
            SZ50          上证50指数    20100104
            ============  ===========  =============
        """
        return xqfactor.get_index_weight_next_day_csi(dateTime, plateID)
