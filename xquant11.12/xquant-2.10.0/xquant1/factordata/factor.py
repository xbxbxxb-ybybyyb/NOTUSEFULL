import copy
import os
import sys
import math
import json
from quanthbase import DataProvider
import datetime
import time
from .db import DML_mysql
import numpy as np
import pandas as pd
from xquant1.setXquantEnv import xquantEnv, testEnv
import re
from xquant1.factordata import xqfactor
from .storageConfig import StorageConfig
from xquant1.conf.DubboConf import *
import logging
import threading
from .factorenum import *
from xquant1.xqutils.utils import statisticLog
from xquant1.conf.DubboConf import get_jurisdictionData,get_xquantConfig
from xquant1.xqutils.tracking import factor_statistic
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("factordata")

logging.getLogger('kazoo').setLevel(logging.CRITICAL)


class FactorData():
    @statisticLog('factordata', 'FactorData')
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
            self.mod = "staging"
        elif xquantEnv == 1:
            self.mod = "online"
        else:
            raise Exception("mod error")
        self.bd = None
        self.__jurisdictionData_dict = None
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

    def __set_ZlGoalDailyTargetDubboService(self):
        if not self.ZlGoalDailyTargetDubboService:
            self.ZlGoalDailyTargetDubboService = set_ZlGoalDailyTargetDubboService()


    def __set_query_gogoal_from_oracle(self):
        if not self.query_gogoal_from_oracle:
            self.query_gogoal_from_oracle = set_query_gogoal_from_oracle()


    def __set_query_wind_from_oracle(self):
        if not self.query_wind_from_oracle:
            self.query_wind_from_oracle = set_query_wind_from_oracle()


    def __set_user_provider_remove_factor(self):
        if not self.user_provider_remove_factor:
            self.user_provider_remove_factor = set_user_provider_remove_factor()

    def __set_user_provider_add_factor(self):
        if not self.user_provider_add_factor:
            self.user_provider_add_factor = set_user_provider_add_factor()


    def __set_user_provider_create_library(self):
        if not self.user_provider_create_library:
            self.user_provider_create_library = set_user_provider_create_library()



    def __set_jurisdictionData_dict(self):
        if not self.__jurisdictionData_dict:
            self.__jurisdictionData_dict = get_jurisdictionData()

    def __set_userAccount(self):
        if not self.userAccount:
            self.userAccount = get_xquantConfig().get("userAccount")

    def __set_DataProvider(self):
        if not self.bd:
            self.bd = DataProvider(self.mod)

    def __check_permission(self, library_name, factor_names=None, readable=False):
        '''
        判断对库、因子有无操作权限
        :return: bool
        '''
        self.__set_jurisdictionData_dict()
        permission_info = self.__jurisdictionData_dict.get("因子权限信息")
        factor_data = self.__jurisdictionData_dict.get("因子信息").get("jurisdictionData").get(library_name).get("factorInfo")
        catalogId = self.__jurisdictionData_dict.get("因子信息").get("jurisdictionData").get(library_name).get("catalogId")
        cata_info = permission_info.get("目录可读写")
        factor_info = permission_info.get("因子可读写")
        cata_only_read_info = permission_info.get("目录可读")
        factor_only_read_info = permission_info.get("因子可读")
        if not readable:
            if not catalogId in cata_info:
                raise Exception("Permission Denied: %s因子库无读写权限！" % (library_name))
        if factor_names:
            factor_dict = {}
            cata_dict = {}
            for factor_name in factor_names:
                if factor_data.get(factor_name) == None:
                    raise Exception("Factor does not exist: %s因子库中不存在%s因子" % (library_name, factor_name))
                factor_dict[factor_name] = factor_data.get(factor_name).get("idInfo")[0]
                cata_dict[factor_name] = factor_data.get(factor_name).get("idInfo")[1:]
            permission_list = []
            if not readable:
                __tmp_dict = self.__transformation(factor_info)
                __tmp_dict_two = self.__transformation(cata_info)
            else:
                __tmp_dict = self.__transformation(factor_info + factor_only_read_info)
                __tmp_dict_two = self.__transformation(cata_info + cata_only_read_info)
            for factor in factor_dict:
                if __tmp_dict.get(factor_dict[factor]) == None:
                    for cata in cata_dict[factor]:
                        if __tmp_dict_two.get(cata):
                            permission_list.append(factor)
                else:
                    permission_list.append(factor)
            no_permission_list = []
            permission_list_dict = self.__transformation(permission_list)
            for factor in factor_names:
                if permission_list_dict.get(factor) == None:
                    no_permission_list.append(factor)
            if no_permission_list:
                if not readable:
                    raise Exception("Permission Denied: " + str(no_permission_list) + "因子无读写权限！")
                else:
                    raise Exception("Permission Denied: " + str(no_permission_list) + "因子无读取权限！")

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
        if not library_type in StorageConfig.keys():
            raise Exception("library_type 设置错误！请重新设置！目前只支持T+0和Alpha!")
        if not self.__naming_specification(library_name):
            raise Exception("library_name 命名不规范！请以字母开头且只能包含字母,数字和下划线！")
        # 得到所有库名
        self.__set_jurisdictionData_dict()
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
        if not type(factor_names) == list:
            raise Exception("factor_names 请传入列表！")
        for factor in factor_names:
            if not self.__naming_specification(factor):
                raise Exception("%s因子命名不规范！" % str(factor))
        # 查找所有库名，判断用户输入的库名是否存在
        self.__set_jurisdictionData_dict()
        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("library_name doesn't exists! %s不存在！" % str(library_name))
        self.__check_permission(library_name=library_name)
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
        if not type(factor_names) == list:
            raise Exception("factor_names 请传入列表！")
        self.__set_jurisdictionData_dict()
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
        self.__check_permission(library_name=library_name, factor_names=factor_names)
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
        if not self.__naming_specification(library_name):
            raise Exception("library_name 命名不规范！请以字母开头且只能包含字母,数字和下划线！")
        # 得到所有库名
        self.__set_jurisdictionData_dict()
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
        if not type(signal_names) == list:
            raise Exception("factor_names 请传入列表！")
        for signal in signal_names:
            if not self.__naming_specification(signal):
                raise Exception("%s信号命名不规范！" % str(signal))
        self.__set_jurisdictionData_dict()
        # 查找所有库名，判断用户输入的库名是否存在
        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("library_name doesn't exists! %s不存在！" % str(library_name))
        self.__check_permission(library_name=library_name)
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
        if not type(signal_names) == list:
            raise Exception("signal_names 请传入列表！")
        self.__set_jurisdictionData_dict()
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
        self.__check_permission(library_name=library_name, factor_names=signal_names)
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
                    raise Exception("调用dubbo接口失败，无法创建因子库: ", result[0].get("response").get("result"))
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
        sql = "delete from {} where tdate between {} and {}".format(tablename, startday, endday)
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
        # print(value_multi_df.head())
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
        # sql = "insert into xx5_1553658017(symbol, date ,column1) select %s,%s,%s on duplicate key update column1 = %s;"
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

    @statisticLog('factordata', 'FactorData')
    def update_factor_value(self, library_name, factor_values, stock=None, mddate=None, delete_range=False):
        """
        更新指定因子库中的因子值
        :param library_name: 因子库名
        :param factor_values: stock，mddate两列索引的dataframe
        :param stock: 股票
        :param mddate: 日期
        :return:
        """
        # 查找所有库名，判断用户输入的库名是否存在
        self.__set_jurisdictionData_dict()
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
            self.__check_permission(library_name=library_name, factor_names=factor_values_list)
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
                for startidx in tqdm(range(0, len(factor_values), update_batch_size), desc="update_factor_progress"):
                    sub_value_df = value_multi_df[startidx:startidx + update_batch_size]
                    if  delete_range:
                        self.__append_factor_after_delete(sub_value_df, table_name, conn_name)
                    else:
                        self.__update_factor(table_name, sub_value_df, conn_name)

            # for i in finally_update_table_col_dict:
            #     columns = finally_update_table_col_dict[i].columns.tolist()
            #     total_ = len(finally_update_table_col_dict[i])
            #     # 每20000条commit一次
            #     if total_ <= 20000:
            #         if not append:
            #             v1 = finally_update_table_col_dict[i].values
            #             new_df = finally_update_table_col_dict[i].reset_index(["stock", "mddate"])
            #             v2 = new_df.values
            #             new_value = np.hstack((v2, v1)).tolist()
            #             try:
            #                 self.__low_frequency_update_factor(i, columns, new_value, conn_name)
            #                 self.dml_xquant_cusdata.commit(conn_name)
            #             except Exception as e:
            #                 self.dml_xquant_cusdata.rollback(conn_name)
            #                 raise Exception(e)
            #         else:
            #             flag = self.dml_xquant_cusdata.df_to_mysql(finally_update_table_col_dict[i],i,conn_name)
            #             if not flag:
            #                 raise Exception("【WARNING】sql执行失败！")
            #     else:
            #         for number in range(0, total_, 20000):
            #             if not append:
            #                 commit_tmp = finally_update_table_col_dict[i][number:number + 20000]
            #                 v1 = commit_tmp.values
            #                 new_df = commit_tmp.reset_index(["stock", "mddate"])
            #                 v2 = new_df.values
            #                 new_value = np.hstack((v2, v1)).tolist()
            #                 try:
            #                     self.__low_frequency_update_factor(i, columns, new_value, conn_name)
            #                     self.dml_xquant_cusdata.commit(conn_name)
            #                 except Exception as e:
            #                     self.dml_xquant_cusdata.rollback(conn_name)
            #                     raise Exception(e)
            #             else:
            #                 flag = self.dml_xquant_cusdata.df_to_mysql(finally_update_table_col_dict[i], i,conn_name)
            #                 if not flag:
            #                     raise Exception("【WARNING】sql执行失败！")
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
            self.__check_permission(library_name=library_name, factor_names=factor_values_list)
            factor_id_dict = {}
            for factor in factor_values_list:
                factor_id_dict[factor] = str(catalog_id_dict['factorInfo'][factor]['idInfo'][0])
            new_factor_values.rename(columns=factor_id_dict, inplace=True)
            # 链接池key由时间戳生成
            conn_name = str(int(time.time())) + str(threading.get_ident())
            self.__set_DataProvider()
            high_frequency_flag = self.bd.update_factor_value(str(library_id), stock, date, new_factor_values)
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
        self.__set_jurisdictionData_dict()
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
            2500:[]
        }
        for factor in factor_names:
            # 将对应的因子放到对应的列表中
            basic_factor_dict[basic_info_dict[factor]['idInfo'][-2]].append(factor)
        df_list = []
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

    def __get_operation_data(self, stock, mddate, factor_name, fill_na):
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
            df_result = xqfactor._fill_df(df_result, stock, mddate, fill_na=fill_na)
            df_result.index.names = ["mddate", "stock"]
            df_result.sort_index(inplace=True)
            return df_result, 200
        except Exception as e:
            return get_result["msg"], 500

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

    def __get_stock(self, c_name, date):
        '查询全量股'
        sql_use = """
                    select a.S_INFO_WINDCODE from asharedescription a 
                    where s_info_windcode not like 'A%' and s_info_windcode not like 'T%' 
                    and a.S_INFO_LISTBOARDNAME in ('主板', '创业板', '中小企业板', '科创板')
                    and  '{0}'>=a.S_INFO_LISTDATE and a.S_INFO_LISTDATE is not null""".format(date)
        df = self.dml_xquant_wind.getAllByPandas(c_name, sql_use)
        self.dml_xquant_wind.close(c_name)
        stock_list = df['S_INFO_WINDCODE'].tolist()
        return stock_list

    @factor_statistic('factordata')
    def get_factor_value(self, library_name, stock=None, mddate=None, factor_names=None, statement_type=STYPE.COMBINED,
                         stock_type=1, block_type=4, fill_na=False, use_mysql=False,return_single_factor=False, daily_bar_num = 242, **kwargs):
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
        if return_single_factor and len(factor_names)>1:
            raise Exception("use_single_factor参数只能在因子个数为一个时设为True!")
        if return_single_factor:
            fill_na = True
        if library_name[:4] == "WIND":
            if return_single_factor:
                raise Exception("查询万得落地库因子不支持该参数设为True!")
            # result = self.__get_wind_source(library_name, **kwargs)
            if use_mysql and xqfactor.judge_table_in_mysql(library_name[5:]):
                result = xqfactor.get_mysql_source(library_name, **kwargs)
            else:
                result = self.__get_wind_source(library_name, **kwargs)
            return result
        elif library_name[:6] == "GOGOAL":
            if return_single_factor:
                raise Exception("查询朝阳永续一致预期因子不支持该参数设为True!")
            # result = self.__get_wind_source(library_name, **kwargs)
            if use_mysql and xqfactor.judge_table_in_mysql(library_name[7:]):
                result = xqfactor.get_mysql_source(library_name, **kwargs)
            else:
                result = self.__get_wind_source(library_name, **kwargs)
            return result
        else:
            # 链接池key由时间戳生成
            conn_name = str(int(time.time())) + str(threading.get_ident())
            if mddate == None or factor_names == None:
                raise Exception("mddate，factor_names 参数不能为空！")
            if not stock:
                max_date = sorted(mddate)[-1]
                stock = self.__get_stock(conn_name, max_date)
            self.__set_jurisdictionData_dict()
            DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
            if not library_name in DB_names:
                raise Exception("library_name doesn't exist: %s因子库不存在！" % library_name)
            catalog_id_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]
            library_id = catalog_id_dict['libraryId']
            if catalog_id_dict["libraryType"] == 1:
                # 非高频操作
                if not type(factor_names) == list:
                    raise Exception("factor names 请传入列表!")
                if not type(mddate) == list:
                    raise Exception("mddate 请传入列表!")
                if not type(stock) == list:
                    raise Exception("stock 请传入列表!")
                DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
                if not library_name in DB_names:
                    raise Exception("该库不存在！")
                # 得到该库所有因子名
                factor_symbols = list(catalog_id_dict["factorInfo"].keys())
                factor_symbols_dict = self.__transformation(factor_symbols)
                for factor_name in factor_names:
                    if factor_symbols_dict.get(factor_name) == None:
                        raise Exception("factor_name doesn't exist: %s因子不存在！" % factor_name)
                # 判断可读权限即可
                self.__check_permission(library_name=library_name, factor_names=factor_names, readable=True)
                new_dates = []
                for dt in mddate:
                    dt = self.__time_standard(dt)
                    new_dates.append(dt)
                # 针对基础因子操作：
                if library_name == self.basic_factor:
                    if not return_single_factor and daily_bar_num==240:
                        raise Exception("【Error】当前查询条件不支持！原因为当daily_bar_num参数置为240时，仅适合查询单个分钟因子并且return_single_factor为True的场景！")
                    basic_df = self.__get_basic_factor(stock, new_dates, factor_names, statement_type, stock_type,
                                                       block_type, fill_na, daily_bar_num = daily_bar_num)
                    if return_single_factor and daily_bar_num!=240:
                        #daily_bar_num为240时，已经是普通的dataframe，不需要unstack
                        basic_df = basic_df.iloc[:,0]
                        basic_df = basic_df.unstack()
                    return basic_df
                # 针对运营数据操作
                if library_name == self.operation_data:
                    operation_data = self.__get_operation_data(stock, new_dates, factor_names, fill_na)
                    df = operation_data[0]
                    if operation_data[1] != 200:
                        raise Exception(operation_data[0])
                    if return_single_factor:
                        df = df.iloc[:, 0]
                        df = df.unstack()
                    return df
                # 针对factor_vip数据操作
                if library_name == self.factor_vip:
                    factor_vip_data = xqfactor.get_factor_vip_data(stock, mddate, factor_names, statement_type,"wind_vip", fill_na)
                    if return_single_factor:
                        factor_vip_data = factor_vip_data.iloc[:,0]
                        factor_vip_data = factor_vip_data.unstack()
                    return factor_vip_data
                if library_name == self.wind_us:
                    factor_vip_data = xqfactor.get_factor_vip_data(stock, mddate, factor_names, statement_type,"wind_vip_us", fill_na)
                    if return_single_factor:
                        factor_vip_data = factor_vip_data.iloc[:, 0]
                        factor_vip_data = factor_vip_data.unstack()
                    return factor_vip_data
                if library_name == self.wind_commodity:
                    factor_vip_data = xqfactor.get_factor_vip_data(stock, mddate, factor_names, statement_type,"wind_vip_commodity", fill_na)
                    if return_single_factor:
                        factor_vip_data = factor_vip_data.iloc[:, 0]
                        factor_vip_data = factor_vip_data.unstack()
                    return factor_vip_data
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
                    sql = "select tdate,tradingcode," + (("%s," * len(new_get_table_col_dict[table]))[:-1]) % tuple(
                        new_get_table_col_dict[table].keys()) + " from %s where tradingcode in (" % (table) + (
                              ("'%s'," * len(stock))[:-1]) % tuple(stock) + ") and tdate in (" + (
                              ("'%s'," * len(new_dates))[:-1]) % tuple(new_dates) + ")"
                    df = self.dml_xquant_cusdata.getAllByPandas(conn_name, sql)
                    df = xqfactor._fill_df(df, stock, new_dates, fill_na=fill_na)
                    df.rename(columns=new_get_table_col_dict[table], inplace=True)
                    df.replace([None], [np.nan], inplace=True)
                    df_list.append(df)
                self.dml_xquant_cusdata.close(conn_name)
                df = pd.concat(df_list, axis=1)
                # df.sort_index(inplace=True)
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
                self.__check_permission(library_name=library_name, factor_names=factor_names, readable=True)
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

    @statisticLog('factordata', 'FactorData')
    def update_signal(self, library_name, stock, mddate, signal_values):
        """
        更新某一只股票某一天的信号值
        :param library_name: 信号库名
        :param stock: 股票
        :param mddate: 日期
        :param signal_values:信号值 （time为索引的dataframe）
        :return:
        范例：
        from xquant.factordata import FactorData
        s = FactorData()
        high_list = []
        for i in range(1, 40):
            high_list.append("high" + str(i))
        d1 = {
            "time": ["20190328"],
        }
        for i in high_list:
        d1[i] = [1]
        df1.set_index("time", inplace=True)
        s.update_signal("xx_high_23",df1, "SH001", "20190325")
        """
        if type(signal_values) != pd.DataFrame:
            raise Exception("factor values 请传入dataframe!")
        date = self.__time_standard(mddate)
        if not isinstance(stock, str):
            raise Exception("stock 请传入string类型!")
        self.__set_jurisdictionData_dict()
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
        self.__check_permission(library_name=library_name, factor_names=factor_values_list)
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

    @statisticLog('factordata', 'FactorData')
    def get_signal(self, library_name, stock, mddate, signal_names):
        """
        在指定信号库中取出单个股票、单天的各信号值，返回dataframe
        :param library_name:信号库名
        :param stock:股票
        :param date:日期
        :param signal_names:信号名
        :return:dataframe
        范例：
        from xquant.factordata import FactorData
        s = FactorData()
        df = s.get_signal("xx_high_23","SH001", "20190325","high1")
        print(df)
        """
        if not type(signal_names) == list:
            raise Exception("factor_names 请传入列表!")
        if not type(library_name) == str:
            raise Exception("library_name 请传入string类型!")
        if not type(stock) == str:
            raise Exception("stock 请传入string类型!")
        if not type(mddate) == str:
            raise Exception("查询信号值请传入单个日期！")
        self.__set_jurisdictionData_dict()
        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("The library_name doesn't exist!该库不存在!")
        date = self.__time_standard(mddate)
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
        self.__check_permission(library_name=library_name, factor_names=signal_names, readable=True)
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

    @statisticLog('factordata', 'FactorData')
    def search_by_stock_factor(self, library_name, stock, factor, datelist):
        """
        按因子库名、股票、因子查询指定日期列表中哪些日期有数据
        :param library_name: 因子库名
        :param stock:股票
        :param factor:因子
        :param datelist:日期列表
        :return:日期列表
        范例：
        from xquant.factordata import FactorData
        s = FactorData()
        tdate_list = s.search_by_stock_factor("xx_high_23","SH001", "high2", ["20190325"])
        print(tdate_list)
        """
        self.__set_jurisdictionData_dict()
        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("该库不存在！")
        catalog_id_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]
        if catalog_id_dict["libraryType"] != 2:
            raise Exception("该库不是高频因子库")
        if type(datelist) != list:
            raise Exception("datelist 请传入列表!")
        self.__check_permission(library_name=library_name, factor_names=[factor], readable=True)
        # 链接池key由时间戳生成
        conn_name = str(int(time.time())) + str(threading.get_ident())
        # 筛选高频因子的id和表、列
        table_col_dict = {}
        table_col_dict[catalog_id_dict.get('factorInfo')[factor]["table"]] = catalog_id_dict.get('factorInfo')[factor][
            "column"]
        date_list = []
        for table in table_col_dict.keys():
            sql = "select tdate from %s where tradingcode = '%s' and %s = 1 and tdate in (" % (
                table, stock, table_col_dict[table]) + (("'%s'," * len(datelist))[:-1]) % tuple(datelist) + ")"
            tdate = self.dml_xquant_cusdata.getAll(conn_name, sql)
            if len(tdate) > 1:
                for td in tdate[1:]:
                    if self.__transformation(date_list).get(td[0]) == None:
                        date_list.append(tdate[1][0])
        self.dml_xquant_cusdata.close(conn_name)
        return date_list

    @statisticLog('factordata', 'FactorData')
    def search_by_stock_date(self, library_name, stock, mddate, factorlist):
        """
        按因子库名、股票、日期查询在指定因子列表中哪些因子有数据
        :param library_name: 因子库名
        :param stock: 股票
        :param mddate: 日期
        :param factorlist: 因子列表
        :return: 因子列表
        范例：
        from xquant.factordata import FactorData
        s = FactorData()
        factor_list = s.search_by_date("xx_high30","20190325", ["SH001", "SH002"])
        print(factor_list)
        """
        self.__set_jurisdictionData_dict()
        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("该库不存在！")
        catalog_id_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]
        library_id = catalog_id_dict["libraryId"]
        if catalog_id_dict["libraryType"] != 2:
            raise Exception("该库不是高频因子库")
        self.__check_permission(library_name=library_name, factor_names=factorlist, readable=True)
        if not type(factorlist) == list:
            raise Exception("factorlist 请传入列表!")
        date = self.__time_standard(mddate)
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
            sql = "select * from %s where tradingcode = '%s' and tdate = '%s'" % (table[0], stock, date)
            result = self.dml_xquant_cusdata.getAll(conn_name, sql)
            if len(result) == 1 or result == None:
                continue
            col = result[0][3:]
            val = result[1][3:]
            d = dict()
            for j in range(len(val)):
                if val[j]:
                    d[col[j]] = val[j]
            for col in d.keys():
                table_column_list.append(table[0] + ":" + col)
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
        self.__set_jurisdictionData_dict()
        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("该库不存在！")
        catalog_id_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]
        library_id = catalog_id_dict["libraryId"]
        if catalog_id_dict["libraryType"] != 2:
            raise Exception("该库不是高频因子库")
        if not type(datelist) == list:
            raise Exception("datelist 请传入列表!")
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
            sql = "select tdate from %s where tradingcode = '%s' and tdate in (" % (table[0], stock) + (
                ("'%s'," * len(datelist))[:-1]) % tuple(datelist) + ")"
            tdate = self.dml_xquant_cusdata.getAll(conn_name, sql)
            if len(tdate) > 1:
                for t in tdate[1:]:
                    if self.__transformation(date_list).get(t[0]) == None:
                        date_list.append(t[0])
        self.dml_xquant.close(conn_name)
        self.dml_xquant_cusdata.close(conn_name)
        return date_list

    @statisticLog('factordata', 'FactorData')
    def search_by_date(self, library_name, mddate, stocklist):
        """
        按因子库名、日期查询指定股票列表中哪些股票有数据
        :param library_name:因子库名
        :param mddate:日期
        :param stocklist:股票列表
        :return:股票列表
        范例：
        from xquant.factordata import FactorData
        s = FactorData()
        stock_list = s.search_by_date("xx_high30","20190325", ["SH001", "SH002"])
        print(stock_list)
        """
        self.__set_jurisdictionData_dict()
        DB_names = list(self.__jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        if not library_name in DB_names:
            raise Exception("该库不存在！")
        catalog_id_dict = self.__jurisdictionData_dict["因子信息"]["jurisdictionData"][library_name]
        library_id = catalog_id_dict["libraryId"]
        if catalog_id_dict["libraryType"] != 2:
            raise Exception("该库不是高频因子库")
        date = self.__time_standard(mddate)
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
            sql = "select tradingcode from %s where tdate = '%s' and tradingcode in (" % (table[0], date) + (
                ("'%s'," * (len(stocklist)))[:-1]) % tuple(stocklist) + ")"
            symbol = self.dml_xquant_cusdata.getAll(conn_name, sql)
            if len(symbol) > 1:
                for s in symbol[1:]:
                    if self.__transformation(symbol_list).get(s[0]) == None:
                        symbol_list.append(s[0])
        self.dml_xquant.close(conn_name)
        self.dml_xquant_cusdata.close(conn_name)
        return symbol_list

    @statisticLog('factordata', 'FactorData')
    def remove_factor_value(self, library_name, stock, mddate, factor_names):
        """
        删除指定因子库中的因子的值
        :param library_name:因子库
        :param stock:股票代码
        :param tdate:日期
        :param factor_names:因子名列表
        :return:
        范例：
        from xquant.factordata import FactorData
        s = FactorData()
        s.remove_factor_value("xx_high_23","SH001","20190325",["high1","high31"])
        """
        if type(factor_names) != list:
            raise Exception("factor values 请传入列表!")
        tdate = self.__time_standard(mddate)
        if not isinstance(stock, str):
            raise Exception("stock 请传入string类型!")
        # 查找所有库名，判断用户输入的库名是否存在
        self.__set_jurisdictionData_dict()
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
        self.__check_permission(library_name=library_name, factor_names=factor_names)
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

    @statisticLog('factordata', 'FactorData')
    def get_library_info(self):
        """
        得到该用户所有的有权限访问的库信息和该库下面的所有因子信息
        :return:
        """
        self.__set_jurisdictionData_dict()
        permission_info = self.__jurisdictionData_dict.get("因子权限信息")
        cata_info = permission_info.get("目录可读写") + permission_info.get("目录可读")
        lib_info = self.__jurisdictionData_dict.get("因子信息").get("jurisdictionData")
        cata_info_dict = self.__transformation(cata_info)
        permission_dict = {}
        for lib_name in lib_info:
            if cata_info_dict.get(lib_info[lib_name].get("catalogId")):
                permission_dict[lib_name] = list(lib_info[lib_name]["factorInfo"].keys())
        return permission_dict

    @statisticLog('factordata', 'FactorData')
    def tradingday(self, startTime, endTime, frequency='DAY', dayType=None, dateType='TRADINGDAYS'):
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

            - dayType 日期类型

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

            - dateType 日历类型

                ============   ========
                类型名称       类型说明
                ALLDAYS        日历日
                TRADINGDAYS    交易日
                ============   ========
        """
        tradingdays = xqfactor.tradingDay(startTime, endTime, frequency=frequency, dayType=dayType, dateType=dateType)
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
            参数说明：
            - IndexType 指数代码

                ============  ===========  =============
                类型名称      类型说明     数据开始日期
                HS300         沪深300指数   20050411
                ZZ500         中证500指数   20100104
                SH50          上证50指数    20100104
                ============  ===========  =============

            - IndustryType 行业分类代码

                ========  ==============
                类型名称  类型说明
                CSRC      证监会行业分类
                CITICS    中信行业分类
                SW        申万行业分类
                ========  ==============
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
        #规范报告期，前一个实际公告日期，应小于后一个实际公告日期
        new_days = []
        tdate = tdate[::-1]
        for didx, day in enumerate(publish_days[::-1]):
            #从最新日期往前推
            if pd.isnull(day):
                if self.__is_report_day(tdate[didx]):
                    #如果报告期的实际公告日期缺失，用报告期代替
                    new_days.append(tdate[didx])
                else:
                    new_days.append(day)
            else:
                new_days.append(day)
        return new_days[::-1]


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

            df_dict  = df.to_dict()
            data_result = {}#存放最终的计算数据

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
                                quaterDate = int(report_dts[d])- math.floor(int(report_dts[d]) / 10000) * 10000
                                import traceback
                                try:
                                    if quaterDate == 1231:
                                        data_result[factor][(day, stock)] = data[(report_dts[d], stock)]
                                    elif quaterDate == 930:
                                        data_result[factor][(day, stock)] = data[report_dts[d], stock] + data[report_dts[d-3], stock] - \
                                                                   data[report_dts[d-4], stock]
                                    elif quaterDate == 630:
                                        data_result[factor][(day, stock)]  = data[report_dts[d], stock] + data[report_dts[d-2], stock] - \
                                                                   data[report_dts[d-4], stock]
                                    elif quaterDate == 331:
                                        data_result[factor][(day, stock)]  = data[report_dts[d], stock] + data[report_dts[d-1], stock] - \
                                                                   data[report_dts[d-4], stock]

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
        df_result = df_result.stack("stock")

        return df_result
