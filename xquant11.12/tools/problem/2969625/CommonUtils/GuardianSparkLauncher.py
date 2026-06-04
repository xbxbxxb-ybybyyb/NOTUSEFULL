import os
import time
import traceback

from xquant.compute.sparkmr import Configuration
from xquant.compute.sparkmr import Job
from xquant.compute.sparkmr import remote_print
from xquant.factordata import FactorData

from CommonUtils.Guardian import Guardian
from CommonUtils.Guardian import update_check_result

s = FactorData()


class TaskMeta:
    def __init__(self, stock: str, start_date: str, end_date: str):
        self.__stock = stock
        self.__start_date = start_date
        self.__end_date = end_date

    def get_stock(self):
        return self.__stock

    def get_start_date(self):
        return self.__start_date

    def get_end_date(self):
        return self.__end_date


class GuardianSparkLauncher:
    def __init__(self, user_id, stock_list, target, asset_type, factor_lib, data_lib, factor_list, factor_config, start_date,
                 end_date, intermediate_log_path, max_executors, mirror_lib, epsilon, threshold, task_list=None,
                 tick_lib=None, anchor_to_tick=False, verbose=False):
        # 并行化作业的名称
        self.__app_name = "FactorGuardian_{}".format(int(time.time()))
        # 并行化作业的输出结果目录，该目录是HDFS上的目录，015619是用户工号
        self.__dst_dir = "{}/sparkMain/{}".format(user_id, int(time.time()))
        # 设置工程代码目录，工程代码目录指的是该程序代码的目录
        # self.__env_dir = os.path.dirname(os.path.abspath(__file__))
        self.__env_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 自定义参数
        self.__user_id = user_id
        self.__target = target
        self.__asset_type = asset_type
        self.__factor_lib = factor_lib
        self.__data_lib = data_lib
        self.__stock_list = stock_list
        self.__factor_list = factor_list
        self.__factor_config = factor_config
        self.__start_date = start_date
        self.__end_date = end_date
        self.__intermediate_log_path = intermediate_log_path
        self.__max_executors = max_executors
        self.__mirror_lib = mirror_lib
        self.__epsilon = epsilon
        self.__threshold = threshold
        self.__task_list = task_list
        self.__tick_lib = tick_lib
        self.__anchor_to_tick = anchor_to_tick
        self.__verbose = verbose

    def start(self):
        taskmeta_list = []
        if self.__task_list is None:
            if self.__target in ["Completeness", "NonExistence"]:
                for stock in self.__stock_list:
                    taskmeta_list.append(TaskMeta(stock, self.__start_date, self.__end_date))
            elif self.__target in ["Invalid", "Consistency"]:
                for stock in self.__stock_list:
                    date_list = s.tradingday(self.__start_date, self.__end_date)
                    for date in date_list:
                        taskmeta_list.append(TaskMeta(stock, date, date))
        else:
            for stock, sdate, edate in self.__task_list:
                taskmeta_list.append(TaskMeta(stock, sdate, edate))

        config = Configuration()
        config.set_app_name(self.__app_name)
        config.set_dst_dir(self.__dst_dir)
        config.set_env_dir(self.__env_dir)
        config.set_executor_instances(self.__max_executors)
        job = Job(config, mode="Increment")
        job.add_tasks(taskmeta_list)
        job.set_func(self.func)
        job.start()

    def func(self, context, taskmeta):
        stock = taskmeta.get_stock()
        start_date = taskmeta.get_start_date()
        end_date = taskmeta.get_end_date()

        fg = Guardian(self.__asset_type, self.__factor_lib, self.__data_lib, stock, self.__factor_list,
                      self.__factor_config, start_date, end_date, self.__tick_lib, self.__anchor_to_tick)
        if self.__target == "Completeness":
            check_result_sub = fg.check_completeness_1by1()
        elif self.__target == "Invalid":
            check_result_sub = fg.check_invalid(self.__threshold)
        elif self.__target == "Consistency":
            check_result_sub = fg.check_consistency(self.__mirror_lib, self.__epsilon)
        elif self.__target == "NonExistence":
            check_result_sub = fg.check_nonexistence()
        else:
            raise ValueError("Unknown checking target.")
        if len(check_result_sub) > 0:
            update_check_result(self.__user_id, check_result_sub, stock, start_date, end_date, self.__intermediate_log_path)
        if self.__verbose:
            remote_print(stock, start_date, end_date, "finished.")

    @staticmethod
    def __get_env_dir():
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))