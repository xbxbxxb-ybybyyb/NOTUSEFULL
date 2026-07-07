import xfactor.DataManager as DataManager
from xfactor.Runner.BasicTaskManager import BasicTaskManager as TaskManager
from xquant.factordata import FactorData
import datetime as dt

fa = FactorData()


# 纯串行计算，用于调试
def run(factor_name_list, start_date, end_date, input_factor_lib=None, output_factor_lib=None,
        save=False, options=None):
    result = {}
    task_manager = TaskManager(factor_name_list, start_date, end_date, input_factor_lib)
    task_list = task_manager.generate_task()
    print("task num:", len(task_list))
    task_results = [__execute_task(task) for task in task_list]
    for task_result in task_results:
        result = __merge_factor_values(result, task_result)
    if save:
        DataManager.save_factor(result, output_factor_lib)
    else:
        return result


# 运行指定task
def __execute_task(task):
    result = {}
    time1 = dt.datetime.now()
    database, data_info = DataManager.get_database_for_task(task)
    time2 = dt.datetime.now()
    print("Load data cost:", time2 - time1)
    for factor_instance in task["factor_instance_list"]:
        calc_result = factor_instance.calc(database, data_info, task["calc_time_list"], task["full_datetime_list"])
        result = __merge_factor_values(result, calc_result)
    time3 = dt.datetime.now()
    print("  Calculate factor cost:", time3 - time2)
    return result


def __merge_factor_values(result, calc_result):
    for factor_name in calc_result:
        if factor_name in result:
            result[factor_name] = result[factor_name].append(calc_result[factor_name])
        else:
            result[factor_name] = calc_result[factor_name]
    return result
