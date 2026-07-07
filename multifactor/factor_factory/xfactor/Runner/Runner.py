import ray
import xfactor.DataManager as DataManager
from xfactor.Runner.DailyUpdateTaskManager import TaskManager as TaskManager
from xfactor.Runner.DailyUpdateTaskManager import BasicTaskManager as BasicTaskManager
from xquant.factordata import FactorData
import datetime as dt
import itertools

fa = FactorData()


# 用于每日更新因子
def run(factor_name_list, start_date, end_date, input_factor_lib=None, output_factor_lib=None,
        save=False, options=None):
    result = {}

    num_cpus = 4
    if options is not None and "ray.num_cpus" in options:
        num_cpus = int(options["ray.num_cpus"])
    ray.init(num_cpus=num_cpus)

    time1 = dt.datetime.now()
    if len(factor_name_list) <= 3:
        task_manager = BasicTaskManager(factor_name_list, start_date, end_date, input_factor_lib)
    else:
        task_manager = TaskManager(factor_name_list, start_date, end_date, input_factor_lib)

    task_list = task_manager.generate_task()

    # undo_ids = []
    # for task in task_list:
    #     undo_ids.extend(__execute_task(task))

    id_lists = ray.get([__execute_task.remote(task) for task in task_list])
    undo_ids = list(itertools.chain(*id_lists))

    time2 = dt.datetime.now()
    print("Total tiny task num:", len(undo_ids))
    print("prepare time cost:", time2 - time1)
    while len(undo_ids):
        done_ids, undo_ids = ray.wait(undo_ids, min(200, len(undo_ids)))
        sub_results = ray.get(done_ids)
        result = __merge_factor_values(result, sub_results)
    time3 = dt.datetime.now()

    print("calc time cost:", time3 - time2)
    ray.shutdown()
    if save:
        DataManager.save_factor(result, output_factor_lib)
    else:
        return result


# 运行指定task
@ray.remote
def __execute_task(task):
    database, data_info = DataManager.get_database_for_task(task)

    database_id = ray.put(database)
    data_info_id = ray.put(data_info)
    calc_time_list_id = ray.put(task["calc_time_list"])
    full_time_list_id = ray.put(task["full_datetime_list"])

    return [
        __execute_calculator.remote(factor_instance, database_id, data_info_id, calc_time_list_id, full_time_list_id)
        for factor_instance in task["factor_instance_list"]]


@ray.remote
def __execute_calculator(calculator_instance, database, data_info, calc_time_list, full_datetime_list):
    return calculator_instance.calc(database, data_info, calc_time_list, full_datetime_list)


def __merge_factor_values(result, sub_results):
    for sub_result in sub_results:
        for factor_name in sub_result:
            if factor_name in result:
                result[factor_name] = result[factor_name].append(sub_result[factor_name])
            else:
                result[factor_name] = sub_result[factor_name]
    return result
