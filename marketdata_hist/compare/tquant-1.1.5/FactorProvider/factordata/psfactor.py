import copy
import math
from quanthbase import DataProvider
import datetime
import time
import numpy as np
import pandas as pd
from FactorProvider.setEnv import xquantEnv, testEnv
from FactorProvider.storage.db import DML_mysql
from FactorProvider.factordata import xqfactor
from FactorProvider.conf import DubboConf
from FactorProvider.utils.check import Permission
from FactorProvider.utils.utils import utils_set_timeout, is_valid_date
from tqdm import tqdm
import logging
import threading
import re
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("factordata")
logging.getLogger('kazoo').setLevel(logging.CRITICAL)

StorageConfig = {
    "T+0":{"catalog_type":2,"remark":"T+0高频因子","parent_id":0,"status":1},
    "Alpha":{"catalog_type":1,"remark":"Alpha非高频因子","parent_id":0,"status":1}
}

class FactorData():
    def __init__(self):
        # 多个数据源
        self.dml_xquant = DML_mysql('xquant')
        # 基础因子
        self.dml_xquant_data = DML_mysql('xquant_data')
        # 个人
        self.dml_xquant_cusdata = DML_mysql('xquant_cusdata')
        # 万得
        self.dml_xquant_wind = DML_mysql('xquant_wind')
        self.tbl_factor_resource = "tbl_factor_resource"
        if xquantEnv == 0:
            self.mod = "debug"
        elif xquantEnv == 1:
            self.mod = "online"
        else:
            raise Exception("mod error")
        self.bd = None

        self.userAccount = None
        self.basic_factor = "Basic_factor"
        self.operation_data = "operation_data"
        self.factor_vip = "Wind_vip"
        self.wind_us = "Wind_vip_us"
        self.wind_commodity = "Wind_vip_commodity"

        self.user_provider_create_library = None
        self.user_provider_add_factor = None
        self.user_provider_remove_factor = None
        self.query_wind_from_oracle = None
        self.query_gogoal_from_oracle = None
        self.ZlGoalDailyTargetDubboService = None

        self.ps = Permission()
        self.__jurisdictionData_dict = self.ps.get_jurisdictionData_dict()

    def __set_ZlGoalDailyTargetDubboService(self):
        if not self.ZlGoalDailyTargetDubboService:
            self.ZlGoalDailyTargetDubboService = DubboConf.set_ZlGoalDailyTargetDubboService()
            
    def __set_query_gogoal_from_oracle(self):
        if not self.query_gogoal_from_oracle:
            self.query_gogoal_from_oracle = DubboConf.set_query_gogoal_from_oracle()


    def __set_query_wind_from_oracle(self):
        if not self.query_wind_from_oracle:
            self.query_wind_from_oracle = DubboConf.set_query_wind_from_oracle()


    def __set_user_provider_remove_factor(self):
        if not self.user_provider_remove_factor:
            self.user_provider_remove_factor = DubboConf.set_user_provider_remove_factor()

    def __set_user_provider_add_factor(self):
        if not self.user_provider_add_factor:
            self.user_provider_add_factor = DubboConf.set_user_provider_add_factor()


    def __set_user_provider_create_library(self):
        if not self.user_provider_create_library:
            self.user_provider_create_library = DubboConf.set_user_provider_create_library()

    def __set_userAccount(self):
        if not self.userAccount:
            self.userAccount = DubboConf.get_xquantConfig().get("userAccount")

    def __set_DataProvider(self):
        if not self.bd:
            self.bd = DataProvider(self.mod)

    #获取库中因子信息
    def get_factor_info(self,library_name):
        factor_info = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].get(library_name)
        if not factor_info:
            return
        factor_info_copy = copy.deepcopy(factor_info)
        return factor_info_copy

    def get_his_stock(self, date, category):
        '查询截止日之前的历史全量股'
        if not is_valid_date(date, date_type='year_month_day'):
            raise Exception("【date】日期类型为string类型YYYYMMDD格式，如 '20200330'")
        c_name = "conn_"+str(int(round(time.time() * 1000))) + str(threading.get_ident())
        if category == "stock":
            sql_use = """
                        select a.S_INFO_WINDCODE from xquant_wind.asharedescription a 
                        where s_info_windcode not like 'A%' and s_info_windcode not like 'T%' 
                        and a.S_INFO_LISTBOARDNAME in ('主板', '创业板', '中小企业板', '科创板')
                        and  '{0}'>=a.S_INFO_LISTDATE and a.S_INFO_LISTDATE is not null""".format(date)
            df = self.dml_xquant_wind.getAllByPandas(c_name, sql_use)
            self.dml_xquant_wind.close(c_name)
            stock_list = df['S_INFO_WINDCODE'].tolist()
        elif category == "bond":
            sql_use = "select WINDCODE from xquant_data.ccbond_issuance_info where listeddate <= {0} and isconvertiblebonds = 1".format(date)
            df = self.dml_xquant_data.getAllByPandas(c_name, sql_use)
            self.dml_xquant_data.close(c_name)
            stock_list = df['WINDCODE'].tolist()
        return stock_list

    def __naming_specification(self, name):
        '''
        判断命名规范
        :return:
        '''
        try:
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name):
                return False
            else:
                return True
        except:
            return False

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

    def __insertLibraryInfo(self, library_name, library_type, ordertpye):
        """
        创库第一个dubbo接口
        :param library_name:库名
        :param library_type: 库类型
        :return:
        """
        self.__set_user_provider_create_library()
        try:
            self.__set_userAccount()
            json_dict = {
                "request": {"userAccount": self.userAccount, "libraryName": library_name, "frequencyType": library_type,
                            "operateType": ordertpye}}
            json_str = json.dumps(json_dict)
            get_result = self.user_provider_create_library.insertLibraryInfo(json_str)
            get_result = json.loads(get_result)
            return get_result, 200
        except Exception as e:
            return str(e), 500

    def create_factor_library(self, library_name, library_type):
        """
        根据参数library_name创建因子库
        :param library_name: 库名
        :param library_type: 类型（T+0：高频，Alpha：非高频）
        :return:
        """
        if not library_type in StorageConfig.keys():
            raise Exception("library_type 设置错误！请重新设置！目前只支持T+0和Alpha!")
        if not self.__naming_specification(library_name):
            raise Exception("library_name 命名不规范！请以字母开头且只能包含字母,数字和下划线！")
        # 得到所有库名

        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if library_name in DB_names:
            raise Exception("The library name already exists:该库名已存在！请重新输入！")
        get_result_insertLibraryInfo = self.__insertLibraryInfo(library_name, library_type, "0")
        if get_result_insertLibraryInfo[1] != 200:
            raise Exception(str(get_result_insertLibraryInfo[0]) + "调用dubbo接口失败，无法创建因子库%s！" % (library_name))
        else:
            if get_result_insertLibraryInfo[0].get("resultCode") == -1:
                raise Exception("调用dubbo接口失败，无法创建因子库: ", get_result_insertLibraryInfo[0].get("response").get("result"))
        library_id = int(get_result_insertLibraryInfo[0].get('response').get('libraryId'))
        catalog_type = StorageConfig[library_type]["catalog_type"]
        self.__set_DataProvider()
        # 调用大数据平台接口
        if catalog_type == 2:
            try:
                meta_flag = self.bd.create_factor_library(str(library_id))
                if not meta_flag:
                    self.__insertLibraryInfo(library_name, library_type, "1")
                    raise Exception("大数据平台创建因子库失败！请重新调用！")
            except:
                self.__insertLibraryInfo(library_name, library_type, "1")
                raise Exception("大数据平台创建因子库失败！请重新调用！")
        self.__set_userAccount()
        self.__set_user_provider_create_library()
        try:
            json_dict = {
                "request": {"userAccount": self.userAccount, "libraryName": library_name}}
            json_str = json.dumps(json_dict)
            get_result_insertAfterStepsInfo = self.user_provider_create_library.insertAfterStepsInfo(json_str)
            get_result_insertAfterStepsInfo = json.loads(get_result_insertAfterStepsInfo)
            if get_result_insertAfterStepsInfo.get("resultCode") == -1:
                self.__insertLibraryInfo(library_name, library_type, "1")
                raise Exception("调用dubbo接口失败，无法创建因子库: ",
                                get_result_insertAfterStepsInfo[0].get("response").get("result"))
        except Exception as e:
            self.__insertLibraryInfo(library_name, library_type, "1")
            raise Exception(str(e) + "调用dubbo接口失败，无法创建因子库%s！" % (library_name))
        catalog_id = int(get_result_insertAfterStepsInfo.get('response').get('catalogId'))
        # 更新权限文件
        self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name] = {
            "factorInfo": {},
            "libraryId": library_id,
            "libraryType": catalog_type,
            "catalogId": catalog_id
        }
        self.__jurisdictionData_dict["因子权限信息"]["目录可读写"].append(catalog_id)
        return True

    def __get_dubbo_add_factor(self, library_name, factor_name):
        """
        调用dubbo接口，增加因子
        :param library_name: 因子库名
        :param factor_name: 因子名
        :return:
        """
        self.__set_user_provider_add_factor()
        try:
            self.__set_userAccount()
            json_dict = {
                "request": {"userAccount": self.userAccount, "libraryName": library_name, "factorName": factor_name}}
            json_str = json.dumps(json_dict)
            get_result = self.user_provider_add_factor.addFactor(json_str)
            get_result = json.loads(get_result)
            return get_result, 200
        except Exception as e:
            return str(e), 500

    def add_factor(self, library_name, factor_names):
        """
        向library_name的因子库中增加因子
        :param library_name: 库名
        :param factor_names: 因子名列表
        :return:

        """
        if not type(factor_names) == list:
            raise Exception("factor_names 请传入列表！")
        for factor in factor_names:
            if not self.__naming_specification(factor):
                raise Exception("%s因子命名不规范！" % str(factor))
        # 查找所有库名，判断用户输入的库名是否存在

        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("library_name doesn't exists! %s不存在！" % str(library_name))
        self.ps.check_factor_permission(library_name=library_name)
        # 得到该库id，tbl_factor_catalog_rela插入数据是用到
        catalog_id_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]
        # 得到该库所有因子名
        factor_symbols = list(catalog_id_dict["factorInfo"].keys())
        for factor_name in factor_names:
            if factor_name in factor_symbols:
                raise Exception("%s在%s库中已存在！" % (factor_name, library_name))
        for factor_name in factor_names:
            result = self.__get_dubbo_add_factor(library_name, factor_name)
            if result[1] != 200:
                raise Exception(str(result[0]) + "调用dubbo接口失败，无法增加因子%s！" % (factor_name))
            else:
                if result[0].get("resultCode") == -1:
                    raise Exception("调用dubbo接口失败，无法增加因子: ", result[0].get("response").get("result"))
            ju_info = result[0]
            owner_meta_col_name = ju_info["response"]["column"]
            factor_id = int(ju_info["response"]["factorId"])
            catalog_id = int(ju_info["response"]["catalogId"])
            owner_meta_table_name = ju_info["response"]["table"]
            # 更新权限文件
            self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]["factorInfo"][factor_name] = {
                "column": owner_meta_col_name,
                "idInfo": [factor_id, catalog_id],
                "table": owner_meta_table_name,
                'statementTypeMap': {}
            }
            # self.__jurisdictionData_dict["因子权限信息"]["因子可读写"].append(factor_id)
        return True

    def __remove_factor(self, libraryId, factorId):
        """
        调用dubbo接口删除因子
        :param libraryId: 库id
        :param factorId: 因子id
        :return:
        """
        self.__set_user_provider_remove_factor()
        try:
            self.__set_userAccount()
            json_dict = {"request": {"userAccount": self.userAccount, "libraryId": libraryId, "factorId": factorId}}
            json_str = json.dumps(json_dict)
            get_result = self.user_provider_remove_factor.delFactor(json_str)
            get_result = json.loads(get_result)
            return get_result, 200
        except Exception as e:
            return str(e), 500

    def remove_factor(self, library_name, factor_names):
        """
        删除指定因子库相关因子
        :param library_name: 因子库名
        :param factor_names: 因子名列表
        :return:
        """
        if not type(factor_names) == list:
            raise Exception("factor_names 请传入列表！")

        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("The library_name doesn't exist:该库不存在！")
        catalog_id_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]
        # 得到该库所有因子名
        factor_symbols = list(catalog_id_dict["factorInfo"].keys())
        factor_symbols_dict = self.__transformation(factor_symbols)
        for factor_name in factor_names:
            if factor_symbols_dict.get(factor_name) == None:
                raise Exception("%s在%s库中不存在！删除失败！" % (factor_name, library_name))
        self.ps.check_factor_permission(library_name=library_name, factor_names=factor_names)
        self.__set_DataProvider()
        library_id = catalog_id_dict['libraryId']
        for factor_name in factor_names:
            factor_id = \
            self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]['factorInfo'][factor_name]['idInfo'][0]
            if catalog_id_dict["libraryType"] == 2:
                try:
                    self.bd.remove_factor(str(library_id), str(factor_id))
                except:
                    pass
            result = self.__remove_factor(str(library_id), str(factor_id))
            if result[1] != 200:
                raise Exception(str(result[0]) + "dubbo接口调用失败！无法删除因子%s！" % (factor_name))
            else:
                if result[0].get("resultCode") == -1:
                    raise Exception("调用dubbo接口失败，无法删除因子: ", result[0].get("response").get("result"))
            # 更新权限文件
            self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]["factorInfo"].pop(factor_name)
            # self.__jurisdictionData_dict["因子权限信息"]["因子可读写"].remove(factor_id)
        return True

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
        if isinstance(time, int):
            time = str(time)
        if isinstance(time, str):
            assert len(time)==8, "请输入YYYYMMDD格式的时间格式"
        elif isinstance(time, datetime.datetime):
            time = time.strftime("%Y%m%d")
        else:
            raise Exception("请输入正确的时间格式,str或datetime类型")
        return time

    def create_signal_library(self, library_name):
        """
        根据参数library_name创建信号库
        :param library_name: 库名
        :return:
        """
        if not self.__naming_specification(library_name):
            raise Exception("library_name 命名不规范！请以字母开头且只能包含字母,数字和下划线！")
        # 得到所有库名

        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if library_name in DB_names:
            raise Exception("The library name already exists:该库名已存在！请重新输入！")
        library_type = "T+0"
        get_result_insertLibraryInfo = self.__insertLibraryInfo(library_name, library_type, "0")
        if get_result_insertLibraryInfo[1] != 200:
            raise Exception(str(get_result_insertLibraryInfo[0]) + "调用dubbo接口失败，无法创建因子库%s！" % (library_name))
        else:
            if get_result_insertLibraryInfo[0].get("resultCode") == -1:
                raise Exception("调用dubbo接口失败，无法创建因子库: ", get_result_insertLibraryInfo[0].get("response").get("result"))
        library_id = int(get_result_insertLibraryInfo[0].get('response').get('libraryId'))
        catalog_type = StorageConfig[library_type]["catalog_type"]
        self.__set_DataProvider()
        # 调用大数据平台接口
        meta_flag = self.bd.create_factor_library(str(library_id))
        if catalog_type != 2:
            raise Exception("创建的不是高频信号库！")
        if not meta_flag:
            self.__insertLibraryInfo(library_name, library_type, "1")
            raise Exception("大数据平台创建因子库失败！请重新调用！")
        self.__set_userAccount()
        self.__set_user_provider_create_library()
        try:
            json_dict = {
                "request": {"userAccount": self.userAccount, "libraryName": library_name}}
            json_str = json.dumps(json_dict)
            get_result_insertAfterStepsInfo = self.user_provider_create_library.insertAfterStepsInfo(json_str)
            get_result_insertAfterStepsInfo = json.loads(get_result_insertAfterStepsInfo)
            if get_result_insertAfterStepsInfo.get("resultCode") == -1:
                raise Exception("调用dubbo接口失败，无法创建因子库: ",
                                get_result_insertAfterStepsInfo[0].get("response").get("result"))
        except Exception as e:
            raise Exception(str(e) + "调用dubbo接口失败，无法创建因子库%s！" % (library_name))
        catalog_id = int(get_result_insertAfterStepsInfo.get('response').get('catalogId'))
        # 更新权限文件
        self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name] = {
            "factorInfo": {},
            "libraryId": library_id,
            "libraryType": catalog_type,
            "catalogId": catalog_id
        }
        self.__jurisdictionData_dict["因子权限信息"]["目录可读写"].append(catalog_id)
        return True

    def add_signal(self, library_name, signal_names):
        """
        向library_name的信号库中增加信号
        :param library_name: 库名
        :param factor_names: 信号列表
        :return:状态(成功返回True)

        """
        if not type(signal_names) == list:
            raise Exception("factor_names 请传入列表！")
        for signal in signal_names:
            if not self.__naming_specification(signal):
                raise Exception("%s信号命名不规范！" % str(signal))

        # 查找所有库名，判断用户输入的库名是否存在
        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("library_name doesn't exists! %s不存在！" % str(library_name))
        self.ps.check_factor_permission(library_name=library_name)
        # 得到该库id，tbl_factor_catalog_rela插入数据是用到
        catalog_id_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]
        # 得到该库所有因子名
        signal_symbols = list(catalog_id_dict["factorInfo"].keys())
        for signal_name in signal_names:
            if signal_name in signal_symbols:
                raise Exception("%s在%s库中已存在！" % (signal_name, library_name))
        # 高频因子数据操作
        if catalog_id_dict["libraryType"] != 2:
            raise Exception("该库不是高频信号库！")
        for factor_name in signal_names:
            result = self.__get_dubbo_add_factor(library_name, factor_name)
            if result[1] != 200:
                raise Exception(str(result[0]) + "调用dubbo接口失败，无法增加因子%s！" % (factor_name))
            else:
                if result[0].get("resultCode") == -1:
                    raise Exception("调用dubbo接口失败，无法增加信号: ", result[0].get("response").get("result"))
            ju_info = result[0]
            owner_meta_col_name = ju_info["response"]["column"]
            factor_id = int(ju_info["response"]["factorId"])
            catalog_id = int(ju_info["response"]["catalogId"])
            owner_meta_table_name = ju_info["response"]["table"]
            # 更新权限文件
            self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]["factorInfo"][factor_name] = {
                "column": owner_meta_col_name,
                "idInfo": [factor_id, catalog_id],
                "table": owner_meta_table_name,
                'statementTypeMap': {}
            }
            # self.__jurisdictionData_dict["因子权限信息"]["因子可读写"].append(factor_id)
        return True

    def remove_signal(self, library_name, signal_names):
        """
        删除指定信号库相关信号
        :param library_name: 因子库名
        :param factor_names: 因子名列表
        :return:
        """
        if not type(signal_names) == list:
            raise Exception("signal_names 请传入列表！")

        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("The library_name doesn't exist： 该库不存在！")
        catalog_id_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]
        # 得到该库所有因子名
        factor_symbols = list(catalog_id_dict["factorInfo"].keys())
        factor_symbols_dict = self.__transformation(factor_symbols)
        for factor_name in signal_names:
            if factor_symbols_dict.get(factor_name) == None:
                raise Exception("%s在%s库中不存在！删除失败！" % (factor_name, library_name))
        self.ps.check_factor_permission(library_name=library_name, factor_names=signal_names)
        if catalog_id_dict["libraryType"] != 2:
            raise Exception("删除的不是高频因子！")
        library_id = catalog_id_dict['libraryId']
        self.__set_DataProvider()
        for factor_name in signal_names:
            factor_id = \
            self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]['factorInfo'][factor_name]['idInfo'][0]
            try:
                self.bd.remove_factor(str(library_id), str(factor_id))
            except:
                pass
            result = self.__remove_factor(str(library_id), str(factor_id))
            if result[1] != 200:
                raise Exception(str(result[0]) + "dubbo接口调用失败！无法删除信号%s！" % (factor_name))
            else:
                if result[0].get("resultCode") == -1:
                    raise Exception("调用dubbo接口失败，无法删除因子: ", result[0].get("response").get("result"))
            # 更新权限文件
            self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]["factorInfo"].pop(factor_name)
            # self.__jurisdictionData_dict["因子权限信息"]["因子可读写"].remove(factor_id)
        return True

    def __is_valid_date(self, mddate):
        '''判断是否是一个有效的日期字符串'''
        try:
            assert(len(mddate)==8)
            return True
        except:
            return False

    def __is_valid_stock(self, stock):
        """
        判断是否是有效的股票名称
        :param stock: 股票
        :return:
        """
        if "." in stock:
            return True
        return False


    def __append_factor_after_delete(self, value_multi_df, tablename, conn_name):
        """
        插入数据
        :param df:
        :param tablename:
        :param conn_name:
        :return:
        """
        try:
            df = value_multi_df.reset_index()
            df.rename(columns={"stock": "tradingcode", "mddate": "tdate"}, inplace=True)
            columns = df.columns.tolist()
            new_value = df.values.tolist()
            self.__low_frequency_update_factor(tablename, columns, new_value, conn_name, duplicate_update = False)
            self.dml_xquant_cusdata.commit(conn_name)
        except Exception as e:
            self.dml_xquant_cusdata.rollback(conn_name)
            raise Exception("【ERROR】更新因子{}条记录失败！".format(len(value_multi_df)), e)

    def __delete_factor(self, tablename, conn_name, startday, endday):
        sql = "delete from {} where tdate between '{}' and '{}'".format(tablename, startday, endday)
        try:
            self.dml_xquant_cusdata.execute(conn_name, sql)
            self.dml_xquant_cusdata.commit(conn_name)
        except:
            self.dml_xquant_cusdata.rollback(conn_name)
            raise Exception("表记录清除失败！")

    def __update_factor(self, table_name, value_multi_df, conn_name):
        """
        更新因子:on duplicate key update
        :param table_name:
        :param value_multi_df:
        :param conn_name:
        :return:
        """
        columns = value_multi_df.columns.tolist()
        v1 = value_multi_df.values
        value_multi_df.reset_index(inplace=True)
        new_df = value_multi_df.reindex(columns=["stock", "mddate"] + columns)
        v2 = new_df.values
        new_value = np.hstack((v2, v1)).tolist()

        try:
            self.__low_frequency_update_factor(table_name, columns, new_value, conn_name)
            self.dml_xquant_cusdata.commit(conn_name)
        except Exception as e:
            self.dml_xquant_cusdata.rollback(conn_name)
            raise Exception("【ERROR】更新因子{}条记录失败！".format(len(value_multi_df)), e)

    def __low_frequency_update_factor(self, table_name, columns, values, conn_name, duplicate_update = True):
        '''
        非高频更新factor内部函数
        :param table_name: 表名
        :param columns: 列名
        :param values: 值
        :return:
        '''
        logger.info("正在更新数据......")
        parm = ""
        for i in columns:
            parm += i
            parm += "=%s,"
        if duplicate_update == True:
            low_frequency_sql = "insert into %s(tradingcode,tdate," % (table_name) + ",".join(
                columns) + ") select %s,%s," + (
                                    ("%s," * (len(columns)))[:-1]) + " on duplicate key update " + parm[:-1]
        else:
            low_frequency_sql = "insert into %s(%s" % (table_name,",".join(columns)) + \
                                ") values(" + (("%s," * (len(columns)))[:-1]) + ")"
        self.dml_xquant_cusdata.executeMany(conn_name, low_frequency_sql, values)

    def update_factor_value(self, library_name, factor_values, stock=None, mddate=None, delete_range=False, disable_progress = False, cell_size = None):
        """
        更新指定因子库中的因子值
        :param library_name: 因子库名
        :param factor_values: stock，mddate两列索引的dataframe
        :param stock: 股票
        :param mddate: 日期
        :return:
        """
        # 查找所有库名，判断用户输入的库名是否存在
        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("library_name doesn't exist: %s因子库不存在！" % library_name)
        catalog_id_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]
        library_id = catalog_id_dict['libraryId']
        
        if catalog_id_dict["libraryType"] == 1:
            # 非高频操作
            if type(factor_values) != pd.DataFrame:
                raise Exception("factor values 需传入DataFrame!")
            if list(factor_values.index.names) != ['stock', 'mddate'] and list(factor_values.index.names) != ['mddate',
                                                                                                              'stock']:
                raise Exception("更新非高频的因子，请传入stock，mddate两列索引的dataframe！")
            if mddate:
                raise Exception("更新非高频的因子，无需传入mddate！")
            if stock:
                raise Exception("更新非高频的因子，无需传入stock！")
            factor_values = factor_values.replace({np.inf: None, -np.inf: None})
            factor_values = factor_values.where((pd.notnull(factor_values)), None)
            df_factor_values = factor_values.reset_index()
            stock_list = df_factor_values["stock"].tolist()
            mddate_list = df_factor_values["mddate"].tolist()
            no_stock_list = []
            no_date_list = []
            for m in mddate_list:
                if not self.__is_valid_date(m):
                    no_date_list.append(m)
            if no_date_list:
                raise Exception("factor_values中以下时间%s不符合格式：" % (str(no_date_list)))
            for s in stock_list:
                if not self.__is_valid_stock(s):
                    no_stock_list.append(s)
            if no_stock_list:
                raise Exception("factor_values中以下股票%s不符合格式：" % (str(no_stock_list)))
            # 获取所有的factor
            factor_values_list = factor_values.columns.tolist()
            self.ps.check_factor_permission(library_name=library_name, factor_names=factor_values_list)
            # 找出要更新的表、列
            new_update_table_col_dict = {}
            for factor in factor_values_list:
                if not new_update_table_col_dict.get(catalog_id_dict["factorInfo"][factor]["table"]):
                    new_update_table_col_dict[catalog_id_dict["factorInfo"][factor]["table"]] = {
                        factor: catalog_id_dict["factorInfo"][factor]["column"]}
                else:
                    new_update_table_col_dict[catalog_id_dict["factorInfo"][factor]["table"]][factor] = \
                        catalog_id_dict["factorInfo"][factor]["column"]
            logging.info(new_update_table_col_dict)

            # 得到列表所要更新的df
            finally_update_table_col_dict = {}
            for i in new_update_table_col_dict:
                drop_list = list(set(factor_values_list) - set(new_update_table_col_dict[i].keys()))
                if drop_list:
                    drop_df = factor_values.drop(columns=drop_list)
                    rename_df = drop_df.rename(columns=new_update_table_col_dict[i])
                else:
                    rename_df = factor_values.rename(columns=new_update_table_col_dict[i])
                finally_update_table_col_dict[i] = rename_df
            logging.info(finally_update_table_col_dict)

            update_batch_size = 30000
            # 链接池key由时间戳生成
            conn_name = str(int(time.time())) + str(threading.get_ident())
            # 得到要更新的表名，列名，以及每条记录的数据
            for table_name in finally_update_table_col_dict:
                if delete_range:
                    self.__delete_factor(table_name, conn_name, delete_range[0], delete_range[1])
                value_multi_df = finally_update_table_col_dict[table_name]
                for startidx in tqdm(range(0, len(factor_values), update_batch_size), desc="update_factor_progress", disable = disable_progress):
                    sub_value_df = value_multi_df[startidx:startidx + update_batch_size]
                    if  delete_range:
                        self.__append_factor_after_delete(sub_value_df, table_name, conn_name)
                    else:
                        self.__update_factor(table_name, sub_value_df, conn_name)
            self.dml_xquant_cusdata.close(conn_name)
            return True
        elif catalog_id_dict["libraryType"] == 2:
            # 高频操作
            if type(factor_values) != pd.DataFrame:
                raise Exception("factor values 请传入dataframe!")
            if not stock:
                raise Exception("更新高频因子需传入股票！")
            if not mddate:
                raise Exception("更新高频因子需传入日期！")
            if not is_valid_date(mddate, date_type='year_month_day'):
                raise Exception("【mddate】日期类型为string类型YYYYMMDD格式，如 '20200330'")
            date = self.__time_standard(mddate)
            if not isinstance(stock, str):
                raise Exception("更新高频因子值，stock请传入string类型!")
            factor_symbols = list(catalog_id_dict["factorInfo"].keys())
            # 得到所有因子列表
            new_factor_values = copy.deepcopy(factor_values)
            factor_values_list = new_factor_values.columns.tolist()
            logger.debug(factor_values_list)
            factor_symbols_dict = self.__transformation(factor_symbols)
            for factor in factor_values_list:
                if factor_symbols_dict.get(factor) == None:
                    raise Exception("factor doesn't exist：%s 因子不存在！" % (factor))
            self.ps.check_factor_permission(library_name=library_name, factor_names=factor_values_list)
            factor_id_dict = {}
            for factor in factor_values_list:
                factor_id_dict[factor] = str(catalog_id_dict['factorInfo'][factor]['idInfo'][0])
            new_factor_values.rename(columns=factor_id_dict, inplace=True)
            # 链接池key由时间戳生成
            conn_name = str(int(time.time())) + str(threading.get_ident())
            self.__set_DataProvider()
            if not cell_size:
                high_frequency_flag = self.bd.update_factor_value(str(library_id), stock, date, new_factor_values)
            else:
                high_frequency_flag = self.bd.update_factor_value_by_jvm(str(library_id), stock, date,
                                                                         new_factor_values, cell_size=cell_size)
            if not high_frequency_flag:
                raise Exception("大数据平台更新factor失败！")
            # 找出要更新的表、列
            new_update_table_col_dict = {}
            for factor in factor_values_list:
                if not new_update_table_col_dict.get(catalog_id_dict["factorInfo"][factor]["table"]):
                    new_update_table_col_dict[catalog_id_dict["factorInfo"][factor]["table"]] = [
                        catalog_id_dict["factorInfo"][factor]["column"]]
                else:
                    new_update_table_col_dict[catalog_id_dict["factorInfo"][factor]["table"]].append(
                        catalog_id_dict["factorInfo"][factor]["column"])
            logger.debug(new_update_table_col_dict)
            # 操作要更新的表、列
            try:
                for update_info in new_update_table_col_dict:
                    # 有则更新，无则插入
                    # high_frequency_sql = "insert into %s(symbol,date,"%(update_info) + ",".join(new_update_table_col_dict[update_info]) + ") select '%s','%s',"%(symbol,date) + (("%s,"*(len(new_update_table_col_dict[update_info])))[:-1])%("1","1") + " on duplicate key update " + (("%s = 1,"*len(new_update_table_col_dict[update_info]))[:-1])%tuple(new_update_table_col_dict[update_info])
                    high_frequency_sql = "insert into %s(tradingcode,tdate," % (update_info) + ",".join(
                        new_update_table_col_dict[update_info]) + ") select '%s','%s'," % (stock, date) + (
                                             ("%s," * (len(new_update_table_col_dict[update_info])))[:-1]) % tuple(
                        ["1"] * len(new_update_table_col_dict[update_info])) + " on duplicate key update " + (
                                             ("%s = 1," * len(new_update_table_col_dict[update_info]))[:-1]) % tuple(
                        new_update_table_col_dict[update_info])
                    logger.debug(high_frequency_sql)
                    self.dml_xquant_cusdata.execute(conn_name, high_frequency_sql)
                self.dml_xquant_cusdata.commit(conn_name)
                self.dml_xquant_cusdata.close(conn_name)
                return True
            except Exception as e:
                self.dml_xquant_cusdata.rollback(conn_name)
                self.dml_xquant_cusdata.close(conn_name)
                raise Exception(e)
        else:
            raise Exception("librarytype error!")


    
    def __get_basic_factor(self, symbols, dates, factor_names, statement_type, stock_type, block_type, fill_na, daily_bar_num = 242):
        """
        查询基础因子
        :param symbols: 股票
        :param dates: 日期
        :param factor_names:因子
        :return:
        """

        basic_info_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"]["Basic_factor"]["factorInfo"]
        basic_factor_dict = {
            2: [],
            3: [],
            4: [],
            5: [],
            6: [],
            7: [],
            8: [],
            9: [],
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
            #行业数据
            df_list.append(xqfactor.get_industry_data(symbols, dates, basic_factor_dict[2500]))
        if basic_factor_dict[2]:
            # 行情指标(指数)
            df_list.append(xqfactor.get_market_price(symbols, dates, basic_factor_dict[2], fill_na=fill_na, daily_bar_num = daily_bar_num))
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
        new_df = pd.concat(df_list, axis=1)

        return new_df

    def __get_operation_data(self, stock, mddate, factor_name, fill_na, sort_option):
        """
        查询运营数据（dubbo接口）

        | 参数          | 注释                          |                                                                                                                                                                                                                                                                                                                                       |
        |---------------|-------------------------------|
        | stock         | list:股票列表                 |
        | mddate    	| list:日期列表                 |
        | factor_name	| list:因子名列表               |

        - **返回**

            Dataframe

        - **范例**

        """
        self.__set_ZlGoalDailyTargetDubboService()
        try:
            json_dict = {
                "source": "xquant",
                "key": "cfd257c9d12542eb86105c341d27fec9",
                "stock": stock,
                "mddate": mddate,
                "factor_names": factor_name
            }
            json_str = json.dumps(json_dict)
            get_result = self.ZlGoalDailyTargetDubboService.getFactorData(json_str)
            get_result = json.loads(get_result)
            factor_list = get_result.get("factorList")
            factor_datas = {}
            for li in factor_list:
                key_tuple = (li[1], li[0])
                if key_tuple in factor_datas:
                    factor_datas[key_tuple][li[2]] = li[3]
                else:
                    factor_datas[key_tuple] = {li[2]: li[3]}
            df = pd.DataFrame(factor_datas)
            if df.empty:
                return df, 200
            df_result = df.T
            df_result.index.names = ["tdate", "tradingcode"]
            df_result.reset_index(inplace=True)
            df_result = xqfactor._fill_df(df_result, stock, mddate, fill_na=fill_na,sort_option=sort_option)
            df_result.index.names = ["mddate", "stock"]
            df_result.sort_index(inplace=True)
            return df_result, 200
        except Exception as e:
            return get_result["msg"], 500
         
    #thirdpatrydata.factordata中调用   
    def __get_wind_source(self, library_name, **kwargs):
        if library_name[:4] == "WIND":
            table_name = library_name[5:]
        else:
            table_name = library_name[7:]
        data = {}
        data["request"] = {}
        data["request"]["table_name"] = table_name
        params_dict = {}
        if kwargs:
            for param in kwargs:
                value = kwargs[param]
                if isinstance(value, str) or isinstance(value, int) or isinstance(value, float):
                    params_dict[param] = value
                elif isinstance(value, list):
                    value_str = ""
                    if not value:
                        params_dict[param] = ""
                    else:
                        for i in value:
                            if not isinstance(i, str):
                                i = str(i)
                            value_str += i + ","
                        params_dict[param] = value_str[:-1]
                else:
                    raise Exception("参数值或列名支持单个值或多个值的列表list")
        if "factors" in params_dict and params_dict["factors"].strip() == "":
            del params_dict["factors"]
        data["request"]["params"] = params_dict
        json_data = json.dumps(data)
        self.__set_query_wind_from_oracle()
        self.__set_query_gogoal_from_oracle()
        if library_name[:4] == "WIND":
            judge_json = self.query_wind_from_oracle.queryTableAccount(json_data)
        else:
            judge_json = self.query_gogoal_from_oracle.queryTableAccount(json_data)
        # {"result":"success","resultCode":0,"totalCount":"7244"}
        judge_data = json.loads(judge_json)
        if judge_data["resultCode"] == -1:
            raise Exception("dubbo 接口：%s" % judge_data["result"])
        row_num = int(judge_data["totalCount"])
        if row_num > 500000:
            raise Exception("SQL查询的数据量超过了50W行，为减轻Oracle服务器压力，请重新设置where条件缩小查询量！")
        if library_name[:4] == "WIND":
            result_json = self.query_wind_from_oracle.queryWindInfo(json_data)
        else:
            result_json = self.query_gogoal_from_oracle.queryGogoalOrGogoalNewInfo(json_data)
        result_data = json.loads(result_json)
        if result_data["resultCode"] == -1:
            raise Exception("dubbo 接口：%s" % result_data["result"])
        wind_data = result_data["resultList"]
        order_columns = result_data["resultColumnList"]
        if len(wind_data) == 0:
            return pd.DataFrame()
        elif len(wind_data) > 1:
            df = pd.DataFrame(wind_data)
        else:
            df = pd.DataFrame(pd.Series(wind_data[0])).T
        df[df.isnull()] = np.NAN
        df = df[order_columns]
        return df

    
    def get_factor_value(self, library_name, stock=None, mddate=None, factor_names=None,
                         fill_na=False, return_single_factor=False, sort_option=True):
        """
        查询指定因子库中的因子值
        :param library_name: 因子库名、万得源表名(例："WIND_AIndexEODPrices")
        :param stock: 股票，查询万得源表时可不传改参数
        :param mddate: 日期，查询万得源表时可不传改参数
        :param factor_names:因子，查询万得源表时可不传改参数
        :param kwargs：关键字参数，factors=[column1,column2,...] 或 factors="column" 为需要查询的列（不传则为select *）；
                    其他关键字参数则作为where的条件处理，单个数值或字符串对应的条件运算符为"="，列表对应的运算符为"in",
                    同时支持>,<,>=,<=,!= 等简单查询条件，支持column='is not null' 筛选此列不为空的数据，详情请见示例。
        :return:指定因子库中的因子值

        """
        # 链接池key由时间戳生成
        conn_name = str(int(time.time())) + str(threading.get_ident())
        if mddate:
            if isinstance(mddate, int) or isinstance(mddate, str):
                if not is_valid_date(mddate, date_type='year_month_day'):
                    raise Exception("【mddate】日期类型为YYYYMMDD格式，如 '20200330'")
            elif isinstance(mddate, list):
                for i in mddate:
                    if not is_valid_date(i, date_type='year_month_day'):
                        raise Exception("【mddate】-{0}的格式不符合要求，日期类型为YYYYMMDD格式，如 '20200330'".format(i))
            else:
                raise Exception("【mddate】为YYYYMMDD格式的单个日期或列表")
        catalog_id_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]
        library_id = catalog_id_dict['libraryId']
        if type(mddate) == list:
            mddate.sort()
            sday, eday = mddate[0], mddate[-1]
        else:
            sday, eday = mddate, mddate
        self.ps.check_factor_date_permission(sday, eday)
        if catalog_id_dict["libraryType"] == 1:
            # 非高频操作
            # 判断可读权限即可
            self.ps.check_factor_permission(library_name=library_name, factor_names=factor_names, readable=True)
            new_dates = []
            for dt in mddate:
                dt = self.__time_standard(dt)
                new_dates.append(dt)
            # 针对个人的非高频因子操作：
            # 找出要get的表、列
            new_get_table_col_dict = {}
            for factor in factor_names:
                if not new_get_table_col_dict.get(catalog_id_dict["factorInfo"][factor]["table"]):
                    new_get_table_col_dict[catalog_id_dict["factorInfo"][factor]["table"]] = {
                        catalog_id_dict["factorInfo"][factor]["column"]: factor}
                else:
                    new_get_table_col_dict[catalog_id_dict["factorInfo"][factor]["table"]][
                        catalog_id_dict["factorInfo"][factor]["column"]] = factor
            logger.debug(new_get_table_col_dict)
            # 查表
            df_list = []
            for table in new_get_table_col_dict:
                # 查询所有满足条件的值
                if not stock:
                    sql = "select tdate,tradingcode," + (("%s," * len(new_get_table_col_dict[table]))[:-1]) % tuple(
                        new_get_table_col_dict[table].keys()) + " from %s where tdate in (" % (table) + (
                              ("'%s'," * len(new_dates))[:-1]) % tuple(new_dates) + ")"
                else:
                    sql = "select tdate,tradingcode," + (("%s," * len(new_get_table_col_dict[table]))[:-1]) % tuple(
                        new_get_table_col_dict[table].keys()) + " from %s where tradingcode in (" % (table) + (
                              ("'%s'," * len(stock))[:-1]) % tuple(stock) + ") and tdate in (" + (
                              ("'%s'," * len(new_dates))[:-1]) % tuple(new_dates) + ")"
                df = self.dml_xquant_cusdata.getAllByPandas(conn_name, sql)
                df = xqfactor._fill_df(df, stock, new_dates, fill_na=fill_na, sort_option=sort_option)
                df.rename(columns=new_get_table_col_dict[table], inplace=True)
                df.replace([None], [np.nan], inplace=True)
                df_list.append(df)
            self.dml_xquant_cusdata.close(conn_name)
            df = pd.concat(df_list, axis=1)
            df.index.names = ['mddate', 'stock']
            if return_single_factor:
                df = df.iloc[:, 0]
                df = df.unstack()
            return df
        elif catalog_id_dict["libraryType"] == 2:
            if return_single_factor:
                raise Exception("查询高频因子不支持该参数设为True!")
            # 高频操作
            if not type(factor_names) == list:
                raise Exception("factor_names 请传入列表!")
            if not type(library_name) == str:
                raise Exception("library_name 请传入string类型!")
            if not type(stock) == str:
                raise Exception("查询高频因子请传入单只股票！")
            if not type(mddate) == str:
                raise Exception("查询高频因子请传入单个日期！")
            date = self.__time_standard(mddate)
            # 得到该库所有因子名
            factor_symbols = list(catalog_id_dict["factorInfo"].keys())
            factor_symbols_dict = self.__transformation(factor_symbols)
            factor_id_list = []
            for factor_name in factor_names:
                if factor_symbols_dict.get(factor_name) == None:
                    raise Exception("%s在%s库中不存在！" % (factor_name, library_name))
                factor_id_list.append(str(catalog_id_dict['factorInfo'][factor_name]['idInfo'][0]))
            # 判断可读权限即可
            self.ps.check_factor_permission(library_name=library_name, factor_names=factor_names, readable=True)
            self.__set_DataProvider()
            df = self.bd.get_factor_value(str(library_id), stock, date, factor_id_list)
            if df.empty:
                return df
            factor_id_list = df.columns.tolist()
            factor_value_dict = {}
            for factor_id in factor_id_list:
                for factor in catalog_id_dict['factorInfo']:
                    if catalog_id_dict['factorInfo'][factor]['idInfo'][0] == int(factor_id):
                        factor_value_dict[factor_id] = factor
            df.rename(columns=factor_value_dict, inplace=True)
            return df
        else:
            raise Exception("librarytype error！")

    def update_signal(self, library_name, stock, mddate, signal_values):
        """
        更新某一只股票某一天的信号值
        :param library_name: 信号库名
        :param stock: 股票
        :param mddate: 日期
        :param signal_values:信号值 （time为索引的dataframe）
        :return:
        """
        if type(signal_values) != pd.DataFrame:
            raise Exception("factor values 请传入dataframe!")
        if isinstance(mddate, int) or isinstance(mddate, str):
            if not is_valid_date(mddate, date_type='year_month_day'):
                raise Exception("【mddate】日期类型为YYYYMMDD格式，如 '20200330'")
        else:
            raise Exception("【mddate】日期类型为YYYYMMDD格式，如 '20200330'")
        date = self.__time_standard(mddate)
        if type(date) == list:
            date.sort()
            sday, eday = date[0], date[-1]
        else:
            sday, eday = date, date
        self.ps.check_factor_date_permission(sday, eday)
        if not isinstance(stock, str):
            raise Exception("stock 请传入string类型!")

        # 查找所有库名，判断用户输入的库名是否存在
        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("该库不存在！")
        catalog_id_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]
        library_id = catalog_id_dict['libraryId']
        factor_symbols = list(catalog_id_dict["factorInfo"].keys())
        if catalog_id_dict["libraryType"] != 2:
            raise Exception("%s不是高频因子库！" % (library_name))
        # 得到所有因子列表
        new_signal_values = copy.deepcopy(signal_values)
        factor_values_list = new_signal_values.columns.tolist()
        logger.debug(factor_values_list)
        factor_symbols_dict = self.__transformation(factor_symbols)
        for factor in factor_values_list:
            if factor_symbols_dict.get(factor) == None:
                raise Exception("factor doesn't exist：%s 因子不存在！" % (factor))
        self.ps.check_factor_permission(library_name=library_name, factor_names=factor_values_list)
        # 链接池key由时间戳生成
        conn_name = str(int(time.time())) + str(threading.get_ident())
        factor_id_dict = {}
        for factor in factor_values_list:
            factor_id_dict[factor] = str(catalog_id_dict['factorInfo'][factor]['idInfo'][0])
        new_signal_values.rename(columns=factor_id_dict, inplace=True)
        self.__set_DataProvider()
        high_frequency_flag = self.bd.update_factor_value(str(library_id), stock, date, new_signal_values)
        if not high_frequency_flag:
            raise Exception("大数据平台更新factor失败！")
        # 找出要更新的表、列
        new_update_table_col_dict = {}
        for factor in factor_values_list:
            if not new_update_table_col_dict.get(catalog_id_dict["factorInfo"][factor]["table"]):
                new_update_table_col_dict[catalog_id_dict["factorInfo"][factor]["table"]] = [
                    catalog_id_dict["factorInfo"][factor]["column"]]
            else:
                new_update_table_col_dict[catalog_id_dict["factorInfo"][factor]["table"]].append(
                    catalog_id_dict["factorInfo"][factor]["column"])
        logger.debug(new_update_table_col_dict)
        # 操作要更新的表、列
        try:
            for update_info in new_update_table_col_dict:
                # 有则更新，无则插入
                # high_frequency_sql = "insert into %s(symbol,date,"%(update_info) + ",".join(new_update_table_col_dict[update_info]) + ") select '%s','%s',"%(symbol,date) + (("%s,"*(len(new_update_table_col_dict[update_info])))[:-1])%("1","1") + " on duplicate key update " + (("%s = 1,"*len(new_update_table_col_dict[update_info]))[:-1])%tuple(new_update_table_col_dict[update_info])
                high_frequency_sql = "insert into %s(tradingcode,tdate," % (update_info) + ",".join(
                    new_update_table_col_dict[update_info]) + ") select '%s','%s'," % (stock, date) + (
                                         ("%s," * (len(new_update_table_col_dict[update_info])))[:-1]) % tuple(
                    ["1"] * len(new_update_table_col_dict[update_info])) + " on duplicate key update " + (
                                         ("%s = 1," * len(new_update_table_col_dict[update_info]))[:-1]) % tuple(
                    new_update_table_col_dict[update_info])
                logger.debug(high_frequency_sql)
                self.dml_xquant_cusdata.execute(conn_name, high_frequency_sql)
            self.dml_xquant_cusdata.commit(conn_name)
            self.dml_xquant_cusdata.close(conn_name)
            return True
        except:
            self.dml_xquant_cusdata.rollback(conn_name)
            self.dml_xquant_cusdata.close(conn_name)
            raise Exception("update signal error!")

    def get_signal(self, library_name, stock, mddate, signal_names):
        """
        在指定信号库中取出单个股票、单天的各信号值，返回dataframe
        :param library_name:信号库名
        :param stock:股票
        :param date:日期
        :param signal_names:信号名
        :return:dataframe
        """
        if isinstance(mddate, str):
            if not is_valid_date(mddate, date_type='year_month_day'):
                raise Exception("【mddate】日期为string类型的YYYYMMDD格式，如 '20200330'")
        else:
            raise Exception("【mddate】日期为string类型的YYYYMMDD格式，如 '20200330'")
        if not type(signal_names) == list:
            raise Exception("factor_names 请传入列表!")
        if not type(library_name) == str:
            raise Exception("library_name 请传入string类型!")
        if not type(stock) == str:
            raise Exception("stock 请传入string类型!")
        if not type(mddate) == str:
            raise Exception("查询信号值请传入单个日期！")

        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("The library_name doesn't exist!该库不存在!")
        date = self.__time_standard(mddate)
        if type(date) == list:
            date.sort()
            sday, eday = date[0], date[-1]
        else:
            sday, eday = date, date
        self.ps.check_factor_date_permission(sday, eday)
        catalog_id_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]
        library_id = catalog_id_dict['libraryId']
        # 得到该库所有因子名
        factor_symbols = list(catalog_id_dict["factorInfo"].keys())
        factor_symbols_dict = self.__transformation(factor_symbols)
        signal_id_list = []
        for factor_name in signal_names:
            if factor_symbols_dict.get(factor_name) == None:
                raise Exception("%s在%s库中不存在！" % (factor_name, library_name))
            signal_id_list.append(str(catalog_id_dict['factorInfo'][factor_name]['idInfo'][0]))
        if catalog_id_dict["libraryType"] != 2:
            raise Exception("%s不是高频因子库！" % (library_name))
        # 判断可读权限即可
        self.ps.check_factor_permission(library_name=library_name, factor_names=signal_names, readable=True)
        self.__set_DataProvider()
        df = self.bd.get_factor_value(str(library_id), stock, date, signal_id_list)
        factor_id_list = df.columns.tolist()
        factor_value_dict = {}
        for factor_id in factor_id_list:
            for factor in catalog_id_dict['factorInfo']:
                if catalog_id_dict['factorInfo'][factor]['idInfo'][0] == int(factor_id):
                    factor_value_dict[factor_id] = factor
        df.rename(columns=factor_value_dict, inplace=True)
        df.index.name = "mdate"
        return df

    @utils_set_timeout(60, "sql查询超时！请缩短查询区间！")
    def __search_by_stock_factor(self, table_col_dict, table, stock, datelist, conn_name):
        date_list = []
        sql = "select tdate from %s where tradingcode = '%s' and %s = 1 and tdate in (" % (
            table, stock, table_col_dict[table]) + (("'%s'," * len(datelist))[:-1]) % tuple(datelist) + ")"
        tdate = self.dml_xquant_cusdata.getAll(conn_name, sql)
        if len(tdate) > 1:
            for td in tdate[1:]:
                date_list.append(td[0])
        return date_list

    def search_by_stock_factor(self, library_name, stock, factor, datelist):
        """
        按因子库名、股票、因子查询指定日期列表中哪些日期有数据
        :param library_name: 因子库名
        :param stock:股票
        :param factor:因子
        :param datelist:日期列表
        :return:日期列表
        """

        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("该库不存在！")
        catalog_id_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]
        if catalog_id_dict["libraryType"] != 2:
            raise Exception("该库不是高频因子库")
        if type(datelist) != list:
            raise Exception("datelist 请传入列表!")
        for i in datelist:
            if not is_valid_date(i, date_type='year_month_day'):
                raise Exception("【datelist】的日期为YYYYMMDD格式，如 '20200330'")
        self.ps.check_factor_permission(library_name=library_name, factor_names=[factor], readable=True)
        datelist.sort()
        self.ps.check_factor_date_permission(datelist[0],datelist[-1])
        # 链接池key由时间戳生成
        conn_name = str(int(time.time())) + str(threading.get_ident())
        # 筛选高频因子的id和表、列
        table_col_dict = {}
        table_col_dict[catalog_id_dict.get('factorInfo')[factor]["table"]] = catalog_id_dict.get('factorInfo')[factor][
            "column"]
        date_list = []
        for table in table_col_dict.keys():
            dates = self.__search_by_stock_factor(table_col_dict, table, stock, datelist, conn_name)
            if dates:
                date_list.extend(dates)
        date_list = list(set(date_list))
        if date_list:
            date_list.sort()
        self.dml_xquant_cusdata.close(conn_name)
        return date_list

    @utils_set_timeout(60, "sql查询超时！请缩短查询区间！")
    def __search_by_stock_date(self, table, stock, date, conn_name):
        column_list = []
        sql = "select * from %s where tradingcode = '%s' and tdate = '%s'" % (table[0], stock, date)
        result = self.dml_xquant_cusdata.getAll(conn_name, sql)
        if len(result) == 1 or result == None:
            return column_list
        col = result[0][3:]
        val = result[1][3:]
        d = dict()
        for j in range(len(val)):
            if val[j]:
                d[col[j]] = val[j]
        for col in d.keys():
            column_list.append(table[0] + ":" + col)
        return column_list

    def search_by_stock_date(self, library_name, stock, mddate, factorlist):
        """
        按因子库名、股票、日期查询在指定因子列表中哪些因子有数据
        :param library_name: 因子库名
        :param stock: 股票
        :param mddate: 日期
        :param factorlist: 因子列表
        :return: 因子列表
        """

        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("该库不存在！")
        catalog_id_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]
        library_id = catalog_id_dict["libraryId"]
        if catalog_id_dict["libraryType"] != 2:
            raise Exception("该库不是高频因子库")
        self.ps.check_factor_permission(library_name=library_name, factor_names=factorlist, readable=True)
        if not type(factorlist) == list:
            raise Exception("factorlist 请传入列表!")
        if not is_valid_date(mddate, date_type='year_month_day'):
            raise Exception("【mddate】的日期为YYYYMMDD格式，如 '20200330'")
        date = self.__time_standard(mddate)
        if type(date) == list:
            date.sort()
            sday, eday = date[0], date[-1]
        else:
            sday, eday = date, date
        self.ps.check_factor_date_permission(sday, eday)
        permission_info = self.__jurisdictionData_dict.get("因子权限信息")
        cata_info = permission_info.get("目录可读写")
        cata_only_read_info = permission_info.get("目录可读")
        factor_info = permission_info.get("因子可读写")
        factor_only_read_info = permission_info.get("因子可读")
        catalogId = self.__jurisdictionData_dict.get("因子信息").get("jurisdictionData").get(library_name).get("catalogId")
        # 链接池key由时间戳生成
        conn_name = str(int(time.time())) + str(threading.get_ident())
        factor_list = []
        factor_cata_tmp = []
        dict_tmp = {}
        if catalogId in cata_info + cata_only_read_info:
            # 目录有权限
            # 从权限文件中找出因子对应表列的关系
            for factor_name in catalog_id_dict.get('factorInfo'):
                if not factor_cata_tmp:
                    factor_cata_tmp.append(catalog_id_dict.get('factorInfo')[factor_name]["idInfo"][0])
                dict_tmp[factor_name] = catalog_id_dict.get("factorInfo")[factor_name][
                                            "table"] + ":" + \
                                        catalog_id_dict.get("factorInfo")[factor_name]["column"]
        else:
            # 在目录无权限的情况下，获取有权限访问的因子
            for factor_name in catalog_id_dict.get('factorInfo'):
                if catalog_id_dict.get('factorInfo')[factor_name]["idInfo"][0] in factor_info + factor_only_read_info:
                    if not factor_cata_tmp:
                        factor_cata_tmp.append(catalog_id_dict.get('factorInfo')[factor_name]["idInfo"][0])
                    dict_tmp[factor_name] = catalog_id_dict.get("factorInfo")[factor_name][
                                                "table"] + ":" + \
                                            catalog_id_dict.get("factorInfo")[factor_name]["column"]
        if not factor_cata_tmp:
            raise Exception("%s因子库下无可访问因子！" % (library_name))
        table_list = list(set(self.dml_xquant.getAll(conn_name, "select table_name from %s where library_id=%s" % (
            self.tbl_factor_resource, library_id))[1:]))
        # 找到该因子的表和列
        table_column_list = []
        for table in table_list:
            column_list = self.__search_by_stock_date(table, stock, date, conn_name)
            table_column_list.extend(column_list)
        # 根据表和列，在权限文件中找出factor
        for factor in dict_tmp:
            if dict_tmp[factor] in table_column_list:
                factor_list.append(factor)
        new_factor_list = []
        for f in factorlist:
            if f in factor_list:
                new_factor_list.append(f)
        self.dml_xquant.close(conn_name)
        self.dml_xquant_cusdata.close(conn_name)
        return new_factor_list

    @utils_set_timeout(60, "sql查询超时！请缩短查询区间！")
    def __search_by_stock(self, table, stock, datelist, conn_name):
        dates = []
        sql = "select tdate from %s where tradingcode = '%s' and tdate in (" % (table[0], stock) + (
            ("'%s'," * len(datelist))[:-1]) % tuple(datelist) + ")"
        tdate = self.dml_xquant_cusdata.getAll(conn_name, sql)
        if len(tdate) > 1:
            for t in tdate[1:]:
                dates.append(t[0])
        return dates

    def search_by_stock(self, library_name, stock, datelist):
        """
        按因子库名、股票查询指定日期列表中哪些天有数据
        :param library_name:因子库名
        :param stock:股票
        :param datelist:日期列表
        :return:日期列表
        """

        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("该库不存在！")
        catalog_id_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]
        library_id = catalog_id_dict["libraryId"]
        if catalog_id_dict["libraryType"] != 2:
            raise Exception("该库不是高频因子库")
        if not type(datelist) == list:
            raise Exception("datelist 请传入列表!")
        for i in datelist:
            if not is_valid_date(i, date_type='year_month_day'):
                raise Exception("【datelist】的日期为YYYYMMDD格式，如 '20200330'")
        datelist.sort()
        self.ps.check_factor_date_permission(datelist[0],datelist[-1])
        permission_info = self.__jurisdictionData_dict.get("因子权限信息")
        cata_info = permission_info.get("目录可读写")
        cata_only_read_info = permission_info.get("目录可读")
        factor_info = permission_info.get("因子可读写")
        factor_only_read_info = permission_info.get("因子可读")
        catalogId = self.__jurisdictionData_dict.get("因子信息").get("jurisdictionData").get(library_name).get("catalogId")
        # 链接池key由时间戳生成
        conn_name = str(int(time.time())) + str(threading.get_ident())
        factor_cata_tmp = []
        date_list = []
        if catalogId in cata_info + cata_only_read_info:
            # 目录有权限
            for factor_name in catalog_id_dict.get('factorInfo'):
                factor_cata_tmp.append(catalog_id_dict.get('factorInfo')[factor_name]["idInfo"][0])
                if factor_cata_tmp:
                    break
        else:
            # 在目录无权限的情况下，获取有权限访问的因子
            for factor_name in catalog_id_dict.get('factorInfo'):
                if catalog_id_dict.get('factorInfo')[factor_name]["idInfo"][0] in factor_info + factor_only_read_info:
                    factor_cata_tmp.append(catalog_id_dict.get('factorInfo')[factor_name]["idInfo"][0])
                if factor_cata_tmp:
                    break
        if not factor_cata_tmp:
            raise Exception("%s因子库下无可访问因子！" % (library_name))
        table_list = list(set(self.dml_xquant.getAll(conn_name, "select table_name from %s where library_id=%s" % (
            self.tbl_factor_resource, library_id))[1:]))
        for table in table_list:
            dates = self.__search_by_stock(table, stock, datelist, conn_name)
            date_list.extend(dates)
        date_list = list(set(date_list))
        if date_list:
            date_list.sort()
        self.dml_xquant.close(conn_name)
        self.dml_xquant_cusdata.close(conn_name)
        return date_list

    @utils_set_timeout(60, "sql查询超时！请缩短查询区间！")
    def __search_by_date(self, table, date, stocklist, conn_name):
        symbols = []
        sql = "select tradingcode from %s where tdate = '%s' and tradingcode in (" % (table[0], date) + (
            ("'%s'," * (len(stocklist)))[:-1]) % tuple(stocklist) + ")"
        symbol = self.dml_xquant_cusdata.getAll(conn_name, sql)
        if len(symbol) > 1:
            for s in symbol[1:]:
                if self.__transformation(symbols).get(s[0]) == None:
                    symbols.append(s[0])
        return symbols

    def search_by_date(self, library_name, mddate, stocklist):
        """
        按因子库名、日期查询指定股票列表中哪些股票有数据
        :param library_name:因子库名
        :param mddate:日期
        :param stocklist:股票列表
        :return:股票列表
        """

        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("该库不存在！")
        catalog_id_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]
        library_id = catalog_id_dict["libraryId"]
        if catalog_id_dict["libraryType"] != 2:
            raise Exception("该库不是高频因子库")
        if not is_valid_date(mddate, date_type='year_month_day'):
            raise Exception("【mddate】的日期为YYYYMMDD格式，如 '20200330'")
        date = self.__time_standard(mddate)
        if type(date) == list:
            date.sort()
            sday, eday = date[0], date[-1]
        else:
            sday, eday = date, date
        self.ps.check_factor_date_permission(sday, eday)
        if not type(stocklist) == list:
            raise Exception("stocklist 请传入列表!")
        catalogId = self.__jurisdictionData_dict.get("因子信息").get("jurisdictionData").get(library_name).get("catalogId")
        # 链接池key由时间戳生成
        conn_name = str(int(time.time())) + str(threading.get_ident())
        permission_info = self.__jurisdictionData_dict.get("因子权限信息")
        cata_info = permission_info.get("目录可读写")
        cata_only_read_info = permission_info.get("目录可读")
        factor_info = permission_info.get("因子可读写")
        factor_only_read_info = permission_info.get("因子可读")
        factor_cata_tmp = []
        if catalogId in cata_info + cata_only_read_info:
            # 目录有权限
            for factor_name in catalog_id_dict.get('factorInfo'):
                factor_cata_tmp.append(catalog_id_dict.get('factorInfo')[factor_name]["idInfo"][0])
                if factor_cata_tmp:
                    break
        else:
            # 在目录无权限的情况下，获取有权限访问的因子
            for factor_name in catalog_id_dict.get('factorInfo'):
                if catalog_id_dict.get('factorInfo')[factor_name]["idInfo"][0] in factor_info + factor_only_read_info:
                    factor_cata_tmp.append(catalog_id_dict.get('factorInfo')[factor_name]["idInfo"][0])
                if factor_cata_tmp:
                    break
        if not factor_cata_tmp:
            raise Exception("%s因子库下无可访问因子！" % (library_name))
        table_list = list(set(self.dml_xquant.getAll(conn_name, "select table_name from %s where library_id=%s" % (
            self.tbl_factor_resource, library_id))[1:]))
        symbol_list = []
        for table in table_list:
            symbols = self.__search_by_date(table, date, stocklist, conn_name)
            symbol_list.extend(symbols)
        symbol_list = list(set(symbol_list))
        self.dml_xquant.close(conn_name)
        self.dml_xquant_cusdata.close(conn_name)
        return symbol_list

    def remove_factor_value(self, library_name, stock, mddate, factor_names):
        """
        删除指定因子库中的因子的值
        :param library_name:因子库
        :param stock:股票代码
        :param tdate:日期
        :param factor_names:因子名列表
        :return:
        """
        if type(factor_names) != list:
            raise Exception("factor values 请传入列表!")
        if not is_valid_date(mddate, date_type='year_month_day'):
            raise Exception("【mddate】的日期为YYYYMMDD格式，如 '20200330'")
        tdate = self.__time_standard(mddate)
        if type(tdate) == list:
            tdate.sort()
            sday, eday = tdate[0], tdate[-1]
        else:
            sday, eday = tdate, tdate
        self.ps.check_factor_date_permission(sday, eday)
        if not isinstance(stock, str):
            raise Exception("stock 请传入string类型!")
        # 查找所有库名，判断用户输入的库名是否存在

        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("该库不存在！")
        catalog_id_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]
        library_id = catalog_id_dict['libraryId']
        factor_symbols = list(catalog_id_dict["factorInfo"].keys())
        # 得到所有因子列表
        factor_symbols_dict = self.__transformation(factor_symbols)
        factor_id_list = []
        for factor in factor_names:
            if factor_symbols_dict.get(factor) == None:
                raise Exception("%s 因子不存在！" % (factor))
            if catalog_id_dict["libraryType"] == 2:
                factor_id_list.append(str(catalog_id_dict['factorInfo'][factor]['idInfo'][0]))
        self.ps.check_factor_permission(library_name=library_name, factor_names=factor_names)
        # 链接池key由时间戳生成
        conn_name = str(int(time.time())) + str(threading.get_ident())
        self.__set_DataProvider()
        if catalog_id_dict["libraryType"] == 2:
            high_frequency_flag = self.bd.remove_factor_value(str(library_id), stock, tdate, factor_id_list)
            if not high_frequency_flag:
                raise Exception("大数据平台删除因子值失败！")
        # 找出要更新的表、列
        new_update_table_col_dict = {}
        for factor in factor_names:
            if not new_update_table_col_dict.get(catalog_id_dict["factorInfo"][factor]["table"]):
                new_update_table_col_dict[catalog_id_dict["factorInfo"][factor]["table"]] = [
                    catalog_id_dict["factorInfo"][factor]["column"]]
            else:
                new_update_table_col_dict[catalog_id_dict["factorInfo"][factor]["table"]].append(
                    catalog_id_dict["factorInfo"][factor]["column"])
        row = 0
        # 操作要更新的表、列
        try:
            for update_info in new_update_table_col_dict:
                high_frequency_sql = "update %s set " % (update_info) + (
                    ("%s=null," * (len(new_update_table_col_dict[update_info])))[:-1]) % tuple(
                    new_update_table_col_dict[update_info]) + " where tradingcode='%s' and tdate='%s'" % (
                                         stock, tdate)
                self.dml_xquant_cusdata.execute(conn_name, high_frequency_sql)
                row += self.dml_xquant_cusdata.rowcount(conn_name)
            self.dml_xquant_cusdata.commit(conn_name)
            self.dml_xquant_cusdata.close(conn_name)
            logger.info("remove_factor_value ok! 共更新%d条记录" % (row))
            return True
        except:
            self.dml_xquant_cusdata.rollback(conn_name)
            self.dml_xquant_cusdata.close(conn_name)
            raise Exception("remove_factor_value error!")

    def get_library_info(self):
        """
        得到该用户所有的有权限访问的库信息和该库下面的所有因子信息
        :return:
        """

        permission_info = self.__jurisdictionData_dict.get("因子权限信息")
        cata_info = permission_info.get("目录可读写") + permission_info.get("目录可读")
        lib_info = self.__jurisdictionData_dict.get("因子信息").get("jurisdictionData")
        cata_info_dict = self.__transformation(cata_info)
        permission_dict = {}
        for lib_name in lib_info:
            if cata_info_dict.get(lib_info[lib_name].get("catalogId")):
                permission_dict[lib_name] = list(lib_info[lib_name]["factorInfo"].keys())
        return permission_dict



