import xfactor.FactorUtil as FactorUtil
from abc import abstractmethod
from xquant.factordata import FactorData
import datetime as dt
import json



class BaseTaskManager(object):
    max_date_num_per_task = 100
    max_factor_num_per_task = 1
    fa = FactorData()

    def __init__(self, factor_name_list, start_date, end_date, input_factor_lib=None):
        self.factor_class_list = FactorUtil.get_factor_class_list(factor_name_list)
        self.start_date = start_date
        self.end_date = end_date
        self.input_factor_lib = input_factor_lib

        # 根据最大计算时间跨度，将计算时间进行分组
        self.calc_time_groups = self.split_calc_datetime_into_group()
        self.calc_factor_groups = self.split_calc_factor_into_group()

        self.full_datetime_list = self.__get_full_datetime_list()

        today = dt.datetime.today().strftime("%Y%m%d")
        #TODO 有时候无法获取今天的股票池，所以改成前一天， 目前需要处理可转债股票，以后信息技术部优化接口
        last_day = self.fa.tradingday(today, -2)[0]
        stock_list = self.fa.hset('MARKET', last_day, "ALLA_HIS")["stock"].tolist()
        self.stock_list = list(filter((lambda x: x[0]!="T" and x[0]!="A"), stock_list))

    @abstractmethod
    def split_calc_datetime_into_group(self):
        return None

    @abstractmethod
    def split_calc_factor_into_group(self):
        return None

    # 获取全部交易日列表，包括lag部分的日期
    def __get_full_datetime_list(self):
        max_data_exceed = FactorUtil.get_max_data_exceed(self.factor_class_list)
        start_date2 = self.start_date
        if max_data_exceed > 0:
            start_date2 = int(self.fa.tradingday(self.start_date, -(max_data_exceed + 1))[0])
        full_datetime_list = self.fa.tradingday(start_date2, self.end_date)
        return full_datetime_list

    # 生成task
    def generate_task(self):
        task_list = []
        for calc_time_group in self.calc_time_groups:
            for calc_factor_group in self.calc_factor_groups:
                task_list.append({
                    "factor_instance_list": self.create_factor_instance(calc_factor_group),
                    "stock_list": self.stock_list,
                    "calc_time_list": calc_time_group,
                    "full_datetime_list": self.full_datetime_list,
                    "input_factor_lib" : self.input_factor_lib
                })
        return task_list

    @staticmethod
    def create_factor_instance(factor_class_list):
        factor_instance_list = list()
        for factor_class in factor_class_list:
            with open("./config.json") as f:
                fix_config = json.load(f)
            factor_class_name = factor_class.get_factor_class_name()
            if factor_class_name in fix_config:
                args = {"fix_time": fix_config[factor_class_name]}
                factor_instance = factor_class(**args)
            else:
                factor_instance = factor_class()
            factor_instance_list.append(factor_instance)
        return factor_instance_list
