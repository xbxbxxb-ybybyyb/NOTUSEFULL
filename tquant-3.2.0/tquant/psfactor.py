# _*_ coding:utf-8 _*_

from FactorProvider.factordata.tpsfactor import FactorData
from tquant.utils.event_trace import event_trace


class PsFactorData:
    def __init__(self):
        self.tps = FactorData()

    @event_trace
    def get_library_info(self):
        """
        得到该用户所有的有权限访问的库信息和该库下面的所有因子信息
        :return:
        """
        return self.tps.get_library_info()

    @event_trace
    def get_library_name_by_factor(self, factors, library_type='research'):
        """
        通过因子名获取库名
        :param factors: 因子列表或因子DataFrame
        :param library_type: 库类型，为research或release
        :return:
        """
        return self.tps.get_library_name_by_factor(factors, library_type)
    
    
    @event_trace
    def update_factor_value_by_factor_library(self, library_env, factor_values, factor, check_olddata=True,
                                      allow_merge_olddata=True, library_name = None):
        """
        更新指定低频因子库中的因子值
        :param library_name: 因子库名
        :param factor_values: dataframe:因子值
        :param is_overwrite: boolean:是否覆盖原数据，默认为否
        :param factor: string:因子
        :return:
        """
        return self.tps.update_factor_value_by_factor(library_env, factor_values, factor, check_olddata=check_olddata,
                                      allow_merge_olddata=allow_merge_olddata, library_name = library_name)

    @event_trace
    def update_factor_value_by_security_library(self, library_env, factor_values, security, check_olddata=True,
                                                library_name = None):
        """
        更新指定高频因子库中的因子值
        :param library_name: 因子库名
        :param factor_values: dataframe:因子值
        :param security: string:标的
        :param is_overwrite: boolean:是否覆盖原数据，默认为否
        :param force_update: boolean:是否强制覆盖，默认为否
        :return:
        """
        return self.tps.update_factor_value_by_security(library_env, factor_values, security, 
                                                        check_olddata=check_olddata, library_name = library_name)
   

    @event_trace
    def get_factor_value_by_library(self, library_env, mddate_list, factor_list, security_list=None, sort=False):
        """
        查询指定因子库中的因子值
        :param library_env: 因子库类型
        :param date_list: list, 必传，高频传入string（单个日期）
        :param factor_list: list, 必传，高频选传，高频默认为因子库中全部因子
        :param security_list: list, 高频因子必传，低频选传，低频默认为因子库全部标的
        :param in_dataframe: boolean, 是否以DataFrame形式返回，仅低频因子可用，默认为False
        :return:
        """
        library_name = self.tps.get_library_name_by_factor(factor_list, library_env)
        return self.tps.get_factor_value(library_name, mddate_list, security_list, factor_list, sort)

    @event_trace
    def get_factor_value(self, library_name, mddate_list, factor_list=None,
                                         security_list=None, sort=False):
        """
        查询指定因子库中的因子值
        :param library_name: 因子库名
        :param date_list: list, 必传，高频传入string（单个日期）
        :param factor_list: list, 必传，高频选传，高频默认为因子库中全部因子
        :param security_list: list, 高频因子必传，低频选传，低频默认为因子库全部标的
        :param in_dataframe: boolean, 是否以DataFrame形式返回，仅低频因子可用，默认为False
        :return:
        """
        return self.tps.get_factor_value(library_name, mddate_list,
                                         security_list, factor_list, sort)
    
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

    @event_trace
    def check_data_frame(self, library_name, factors, security_list,
                                  start_date, end_date, library_info=None):
        """
        检查低频因子存储是否成功
        :param library_name: string:因子库名
        :param factors: list:因子
        :param security_list: list:股票列表
        :param start_date: string:开始时间
        :param end_date: string:结束时间
        :param library_info: dict:因子权限信息
        :return:
        """
        return self.tps.check_data_frame(library_name, factors, security_list,
                                         start_date, end_date, library_info)

    @event_trace
    def delete_factors(self, library_name, factors):
        """
        删除高频因子
        :param library_name: string:因子库名
        :param factors: list:因子列表
        :return:
        """
        return self.tps.delete_factors(library_name, factors)

    def update_label_value(self, label_values, security, check_olddata=True):
        """
        存储标签数据
        """
        return self.tps.update_label_value(label_values, security, check_olddata)

    def get_label_value(self, mddate_list, security_id, label_list=None, sort=False):
        """
        获取标签数据
        """
        return self.tps.get_label_value(mddate_list, security_id, label_list, sort)

    def add_label(self, label_names):
        """
        标签名写入表factor_label_record中
        """
        return self.tps.add_label(label_names)

    @event_trace
    def get_factor_value_by_library_path(self, library_path, mddate_list,
                                         factor_list, security_list=None,
                                         sort=False, in_dataframe=False):
        """
        查询指定因子库路径中的因子值
        :param library_env: 因子库类型
        :param date_list: list, 必传，高频传入string（单个日期）
        :param factor_list: list, 必传，高频选传，高频默认为因子库中全部因子
        :param security_list: list, 高频因子必传，低频选传，低频默认为因子库全部标的
        :param in_dataframe: boolean, 是否以DataFrame形式返回，仅低频因子可用，默认为False
        :return:
        """
        return self.tps.get_low_frequency_factor_value_by_concat(
            library_path, mddate_list, factor_list, security_list, sort, in_dataframe)
