from FactorProvider.conf.DubboConf import get_jurisdictionData, get_xquantConfig
from FactorProvider.storage.db import DML_mysql
import threading
import time
from FactorProvider.conf.DubboConf import get_userid
import datetime
import calendar
import os
import gc
from FactorProvider.setEnv import sysFlag

class Permission():
    __instance = None
    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            return cls.__instance
        else:
            obj = object.__new__(cls, *args, **kwargs)
            cls.__instance = obj
            return cls.__instance
        
        
    def __init__(self):
        self.__jurisdictionData_dict = None
        self.tdate = None

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

    def __set_jurisdictionData_dict(self):
        if not self.__jurisdictionData_dict:
            self.__jurisdictionData_dict = get_jurisdictionData()

    def __set_timeRight(self):
        if not self.tdate:
            if sysFlag == "xquant" or sysFlag == "big_data":
                _xquantConfig = get_xquantConfig()
                time_right = _xquantConfig["timeRight"].split('-')
                self.tdate = [int(i) for i in time_right]
            else:
                self.tdate = None


    def __check_xquant_factor_permission(self, library_name, factor_names=None, readable=False):
        '''
        判断对库、因子有无操作权限
        :return: bool
        '''
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
    #获取权限文件
    def get_jurisdictionData_dict(self):
        self.__set_jurisdictionData_dict()
        return self.__jurisdictionData_dict

    #判断因子访问权限
    def check_factor_permission(self, library_name, factor_names=None, readable=False):
        if sysFlag == "xquant":
            self.__set_jurisdictionData_dict()
            self.__check_xquant_factor_permission(library_name,factor_names,readable)
        else:
            pass

    def __get_delta_date(self,beforeOfDay):
        #根据偏移量，计算前n天
        today = datetime.datetime.now()
        # 计算偏移量
        offset = datetime.timedelta(days=-beforeOfDay)
        # 获取想要的日期的时间
        re_date = (today + offset).strftime('%Y%m%d')
        return re_date

    #针对mdcprovider里面的函数处理
    def order_mdc_date(self,datelist):
        year = int(datelist[:4])
        month = int(datelist[4:])
        begin_date = str(year) + str(month).zfill(2) + str(1).zfill(2)
        end_date = str(year) + str(month).zfill(2) + str(calendar.monthrange(year, month)[1]).zfill(2)
        return begin_date,end_date


    #时间权限
    def __check_xquant_factor_date_permission(self, begin_date, end_date):
        self.__set_timeRight()
        begin_date, end_date = str(begin_date), str(end_date)
        if len(self.tdate) != 2:
            #数据库中未录入时间权限信息，则时间不做限制
            return

        allow_begin_days = self.tdate[0]
        allow_end_days = self.tdate[1]
        allow_begin_date = self.__get_delta_date(allow_begin_days)
        allow_end_date = self.__get_delta_date(allow_end_days)
        if allow_end_date == datetime.datetime.strftime(datetime.datetime.now(),'%Y%m%d'):
            return
        if begin_date < allow_begin_date or end_date > allow_end_date:
            raise Exception("该用户有权限访问的时间区间为{0}~{1}".format(allow_begin_date,allow_end_date))

    def check_factor_date_permission(self, begin_date, end_date):
        if sysFlag == "xquant":
            self.__check_xquant_factor_date_permission(begin_date,end_date)
        else:
            pass