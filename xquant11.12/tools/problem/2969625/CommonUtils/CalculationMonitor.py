# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
import os
import pickle
import numpy as np
import datetime as dt
from xquant.xqutils.helper import link
import traceback


def check_completeness(mode, user_id, asset_type, factor_lib, data_lib, code_list, factor_list, factor_config, start_date,
                       end_date, task_list=None, tick_lib=None, anchor_to_tick=False):
    from CommonUtils.Guardian import Guardian, collect_check_result
    from CommonUtils.GuardianSparkLauncher import GuardianSparkLauncher
    from xquant.xqutils.xqfile import HDFSFile
    hf = HDFSFile()

    if task_list is None:
        task_list = [(code, start_date, end_date) for code in code_list]
    else:
        task_list = [(each[0], each[1], each[1]) for each in task_list]

    if mode == "Local":
        unfinished_task_set = set()
        unfinished_factor_set = set()
        for code, sdate, edate in task_list:
            fg = Guardian(asset_type, factor_lib, data_lib, code, factor_list, factor_config, sdate, edate, tick_lib, anchor_to_tick)
            check_result_sub = fg.check_completeness_1by1()
            if len(check_result_sub) > 0:
                unfinished_task_set = set(unfinished_task_set).union(set([(each[0], each[1]) for each in check_result_sub]))
                unfinished_factor_set = unfinished_factor_set.union(set([each[2] for each in check_result_sub]))
        check_result = (sorted(unfinished_factor_set), sorted(unfinished_task_set))
    else:
        intermediate_log_path = f"Factor_{asset_type}_Daily_{factor_lib}_{end_date}"
        print(intermediate_log_path)
        check_result_file = f"factor_{asset_type.lower()}_daily_check_result_{factor_lib}_{end_date}"

        if hf.exists("/FactorCheckLog/" + intermediate_log_path):
            hf.delete("/FactorCheckLog/" + intermediate_log_path, recursive=True)

        spm = GuardianSparkLauncher(user_id, code_list, "Completeness", asset_type, factor_lib, data_lib, factor_list,
                                    factor_config, start_date, end_date, intermediate_log_path, 600, None, None, None,
                                    task_list=task_list, tick_lib=tick_lib, anchor_to_tick=anchor_to_tick)
        spm.start()

        update_flag, check_result = collect_check_result(user_id, intermediate_log_path, check_result_file, return_check_result=True)
    return check_result


class CalculationMonitor:
    def __init__(self, asset_type, ptype, start_date, end_date, code_list, tick_library, tick_factor_list,
                 minute_library=None, minute_factor_list=None, tick_tag_list=None, minute_tag_list=None):
        self.__asset_type = asset_type
        self.__ptype = ptype
        self.__start_date = str(start_date)
        self.__end_date = str(end_date)
        self.__code_length = len(code_list)

        self.__tick_library = tick_library
        self.__tick_factor_length = len(tick_factor_list)

        self.__minute_library = minute_library if minute_library is not None else ""
        self.__minute_factor_length = len(minute_factor_list) if minute_factor_list is not None else 0

        self.__tick_tag_length = len(tick_tag_list) if tick_tag_list is not None else 0
        self.__minute_tag_length = len(minute_tag_list) if minute_tag_list is not None else 0

        self.__lm = link.LinkMessage()

        self.__start_time = dt.datetime.now()
        self.__end_time = None

    def print_launch_info(self):
        if self.__ptype in ["Daily", "Deposit"]:
            message = f"{self.__start_date}-{self.__end_date} {self.__asset_type}: Code: {self.__code_length}, " \
                f"Tick factor: {self.__tick_factor_length}, Minute factor: {self.__minute_factor_length}, " \
                f"Tick tag: {self.__tick_tag_length}, Minute tag: {self.__minute_tag_length}. Calculation start"
        elif self.__ptype in ["Patch"]:
            message = "Task: {}, Factors: {}. Patching start.".format(self.__code_length, self.__tick_factor_length)
        else:
            raise Exception("Unknown print type.")

        print(message)
        self.__lm.sendMessage(message)

    def print_finish_info(self, addtional_info=None):
        self.__end_time = dt.datetime.now()
        if self.__ptype in ["Daily", "Deposit"]:
            message = \
                "{}-{} {} factor updated: {} stocks, {} tick factors and {} tick tags to library {}, " \
                "{} minute factors and {} minute tags to library {}. " \
                "Task start {}, end {}, time costs(min): {}".format(
                    self.__start_date, self.__end_date, self.__asset_type, self.__code_length,
                    self.__tick_factor_length, self.__tick_tag_length, self.__tick_library,
                    self.__minute_factor_length, self.__minute_tag_length, self.__minute_library,
                    dt.datetime.strftime(self.__start_time, "%Y/%m/%d %H:%M:%S"),
                    dt.datetime.strftime(self.__end_time, "%Y/%m/%d %H:%M:%S"),
                    np.round((self.__end_time - self.__start_time).total_seconds() / 60))
        elif self.__ptype in ["Patch"]:
            message = "Filling factors value of task file: {} finished. Task: {}, factors: {}.".format(
                addtional_info, self.__code_length, self.__tick_factor_length)
        else:
            raise Exception("Unknown print type.")

        print(message)
        self.__lm.sendMessage(message)

    def print_check_info(self, frequency, update_flag, mode, try_times=1):
        if mode == 'SH':
            lib = self.__tick_library if frequency == "Tick" else self.__minute_library
            if not update_flag:
                message = "Library: {}, date: {}-{}, SH factors updated unsuccessfully, please check! Try times {}".format(
                    lib, self.__start_date, self.__end_date, try_times)
            else:
                message = "Library: {}, date: {}-{}, SH factors updated successfully".format(
                    lib, self.__start_date, self.__end_date)
            print(message)
            self.__lm.sendMessage(message)
        elif mode == 'SZ':
            lib = self.__tick_library if frequency == "Tick" else self.__minute_library
            if not update_flag:
                message = "Library: {}, date: {}-{}, SZ factors updated unsuccessfully, please check! Try times {}".format(
                    lib, self.__start_date, self.__end_date, try_times)
            else:
                message = "Library: {}, date: {}-{}, SZ factors updated successfully".format(
                    lib, self.__start_date, self.__end_date)
            print(message)
            self.__lm.sendMessage(message)


    def print_update_flag(self, update_flag, mode):
        if update_flag:
            if mode == 'SH':
                path = "/data/user/018106/FactorCheck/DailyTrack"
                os.makedirs(path, exist_ok=True)
                with open(os.path.join(path, f"{self.__tick_library}_{self.__start_date}_{self.__end_date}_SH.pickle"), "wb") as f:
                    pickle.dump("Succcess.", f)
            if mode == 'SZ':
                path = "/data/user/018106/FactorCheck/DailyTrack"
                os.makedirs(path, exist_ok=True)
                with open(os.path.join(path, f"{self.__tick_library}_{self.__start_date}_{self.__end_date}_SZ.pickle"), "wb") as f:
                    pickle.dump("Succcess.", f)
    def load_update_flag(self, mode):
        if mode == 'SH':
            path = "/data/user/018106/FactorCheck/DailyTrack"
            if os.path.exists(os.path.join(path, f"{self.__tick_library}_{self.__start_date}_{self.__end_date}_SH.pickle")):
                return True
            else:
                return False
        if mode == 'SZ':
            path = "/data/user/018106/FactorCheck/DailyTrack"
            if os.path.exists(os.path.join(path, f"{self.__tick_library}_{self.__start_date}_{self.__end_date}_SZ.pickle")):
                return True
            else:
                return False

    def print_unexpected_info(self):
        self.__lm.sendMessage("{}-{} {}: Unexpected error!".format(self.__start_date, self.__end_date, self.__asset_type))
        print(traceback.format_exc())
