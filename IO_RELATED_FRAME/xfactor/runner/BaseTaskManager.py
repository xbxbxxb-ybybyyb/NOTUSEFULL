from abc import abstractmethod
import pandas as pd
import os
import settings
import json
import xfactor.FactorUtil as FactorUtil
from xfactor.Util import get_trading_day


class BaseTaskManager(object):
    max_date_num_per_task = 100
    max_factor_num_per_task = 1

    def __init__(self, factor_name_list, start_date, end_date, fix_config, input_factor_lib=None):
        self.factor_class_list = FactorUtil.get_factor_class_list(factor_name_list)
        self.start_date = start_date
        self.end_date = end_date
        self.input_factor_lib = input_factor_lib
        self.fix_config = fix_config
        # 根据最大计算时间跨度，将计算时间进行分组
        self.calc_time_groups = self.split_calc_datetime_into_group()
        self.calc_factor_groups = self.split_calc_factor_into_group()
        self.full_datetime_list = self.__get_full_datetime_list()
        # self.stock_list = self.__get_stock_list()

    @abstractmethod
    def split_calc_datetime_into_group(self):
        return None

    @abstractmethod
    def split_calc_factor_into_group(self):
        return None

    @staticmethod
    def __get_stock_list():
        with open(os.path.join(settings.DAILY_DATA_PATH, "tools", "stock_list.json"), "r") as f:
            stock_list = json.load(f)
        return stock_list

    # 获取全部交易日列表，包括lag部分的日期
    def __get_full_datetime_list(self):
        max_data_exceed = FactorUtil.get_max_data_exceed(self.factor_class_list)
        start_date2 = self.start_date
        end_date2 = get_trading_day(self.end_date, 2)[-1]
        if max_data_exceed > 0:
            start_date2 = int(get_trading_day(self.start_date, -(max_data_exceed + 1))[0])
        full_datetime_list = get_trading_day(start_date2, end_date2)
        return full_datetime_list

    # 生成task
    def generate_task(self, split_fix_factors=False):
        # split_fix_factors = True, 需要将fix因子的七个时间点分割到对应的task中
        # 主要用来为单个因子，时间跨度较大的计算提升并发度，尤其是入库计算
        task_list = []
        for calc_time_group in self.calc_time_groups:
            if split_fix_factors and len(self.factor_class_list) == 1:
                # 只有一个因子需要计算时，才可以按fix_times进行任务分割
                this_factor_class = self.factor_class_list[0]
                if this_factor_class.factor_type == "FIX":
                    this_factor_name = this_factor_class.get_factor_class_name()
                    this_fix_times = ["1000", "1030", "1100", "1300", "1330", "1400", "1430"]
                    if this_factor_name in self.fix_config:
                        this_fix_times = self.fix_config[this_factor_name]
                    for fix_time in this_fix_times:
                        task_list.append({
                            "factor_class_list":  [this_factor_class],
                            "fix_config": {this_factor_name: [fix_time]},
                            "calc_time_list": calc_time_group,
                            "full_datetime_list": self.full_datetime_list,
                            "input_factor_lib": self.input_factor_lib
                        })
                elif this_factor_class.factor_type == "DAY":
                    task_list.append({
                        "factor_class_list": [this_factor_class],
                        "fix_config": self.fix_config,
                        "calc_time_list": calc_time_group,
                        "full_datetime_list": self.full_datetime_list,
                        "input_factor_lib": self.input_factor_lib
                    })
            else:
                for calc_factor_group in self.calc_factor_groups:
                    task_list.append({
                        "factor_class_list": calc_factor_group,
                        "fix_config": self.fix_config,
                        "calc_time_list": calc_time_group,
                        "full_datetime_list": self.full_datetime_list,
                        "input_factor_lib": self.input_factor_lib
                    })
        return task_list

