# _*_ coding:utf-8 _*_

from FactorProvider.factordata.tpsfactor import FactorData
from tquant.utils.event_trace import EventTrace, event_trace


class PsFactorData:
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
        self.tps = FactorData()

    @event_trace
    def get_library_info(self):
        """
        得到该用户所有的有权限访问的库信息和该库下面的所有因子信息
        :return:
        """
        return self.tps.get_library_info()

    @event_trace
    def get_library_securities(self):
        """
        得到该用户所有的有权限访问的库中的标的
        :return:
        """
        return self.tps.get_library_securities()

    @event_trace
    def create_factor_library(self, library_name, library_type):
        """
        根据参数library_name创建因子库
        :param library_name: 库名
        :param library_type: 类型（T+0：高频，Alpha：非高频）
        :return:
        """
        return self.tps.create_factor_library(library_name, library_type)

    @event_trace
    def add_factor(self, library_name, factor_names):
        """
        向library_name的因子库中增加因子
        :param library_name: 库名
        :param factor_names: 因子名列表
        :return:
        """
        return self.tps.add_factor(library_name, factor_names)

    # @event_trace
    # def remove_factor(self, library_name, factor_names):
    #     """
    #     删除指定因子库相关因子
    #     :param library_name: 库名
    #     :param factor_names: 因子名列表
    #     :return:
    #     """
    #     return self.tps.remove_factor(library_name, factor_names)

    @event_trace
    def update_factor_value_by_factor(self, library_name, factor_values, factor, check_olddata=True,
                                      allow_merge_olddata=True):
        """
        更新指定低频因子库中的因子值
        :param library_name: 因子库名
        :param factor_values: dataframe:因子值
        :param is_overwrite: boolean:是否覆盖原数据，默认为否
        :param factor: string:因子
        :return:
        """
        return self.tps.update_factor_value_by_factor(library_name, factor_values, factor, check_olddata=check_olddata,
                                      allow_merge_olddata=allow_merge_olddata)

    @event_trace
    def update_factor_value_by_security(self, library_name, factor_values, security, check_olddata=True):
        """
        更新指定高频因子库中的因子值
        :param library_name: 因子库名
        :param factor_values: dataframe:因子值
        :param security: string:标的
        :param is_overwrite: boolean:是否覆盖原数据，默认为否
        :param force_update: boolean:是否强制覆盖，默认为否
        :return:
        """
        return self.tps.update_factor_value_by_security(library_name, factor_values, security, check_olddata=check_olddata)

    # def remove_factor_value(self, library_name, stock, mddate, factor_names):
    #     """
    #     删除指定因子库中的因子的值
    #     :param library_name:因子库
    #     :param stock:股票代码
    #     :param tdate:日期
    #     :param factor_names:因子名列表
    #     :return:
    #     """
    #     return self.tps.remove_factor_value(library_name, stock, mddate, factor_names)

    @event_trace
    def get_factor_value(self, library_name, mddate_list, factor_list, security_list=None, sort=False, in_dataframe=False):
        """
        查询指定因子库中的因子值
        :param library_name: 因子库名
        :param date_list: list, 必传，高频传入string（单个日期）
        :param security_list: list, 高频因子必传，低频选传，低频默认为因子库全部标的
        :param factor_list: list, 低频因子必传，高频选传，高频默认为因子库中全部因子
        :param in_dataframe: boolean, 是否以DataFrame形式返回，仅低频因子可用，默认为False
        :return:
        """
        return self.tps.get_factor_value(library_name, mddate_list, security_list, factor_list, sort, in_dataframe)

    @event_trace
    def search_by_stock_date(self, library_name, stock, mddate, factor_list):
        """
        指定因子库名、股票、日期，查询在指定因子列表中哪些因子有数据
        :param library_name: string:因子库名
        :param stock: string:股票
        :param mddate: string:日期
        :param factor_list: list:因子名列表
        :return:
        """
        return self.tps.search_by_stock_date(library_name, stock, mddate, factor_list)

    @event_trace
    def search_by_stock_factor(self, library_name, stock, factor, mddate_list):
        """
        按因子库名、股票、因子查询指定日期列表中哪些日期有数据
        :param library_name: string:因子库名
        :param stock: string:股票
        :param factor: string:因子
        :param mddate_list: list:日期列表
        :return:
        """
        return self.tps.search_by_stock_factor(library_name, stock, factor, mddate_list)

    @event_trace
    def search_by_stock(self, library_name, stock, mddate_list):
        """
        按因子库名、股票查询指定日期列表中哪些天有数据
        :param library_name: string:因子库名
        :param stock: string:股票
        :param mddate_list: list:日期列表
        :return:
        """
        return self.tps.search_by_stock(library_name, stock, mddate_list)

    @event_trace
    def search_by_date(self, library_name, mddate, stock_list):
        """
        按因子库名、日期查询指定股票列表中哪些股票有数据
        :param library_name: string:因子库名
        :param mddate: string:股票
        :param stock_list: list:股票列表
        :return:
        """
        return self.tps.search_by_date(library_name, mddate, stock_list)
