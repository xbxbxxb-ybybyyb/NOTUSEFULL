import os
import datetime as dt
from multiprocessing import Pool
from loguru import logger
import xfactor.DataManager as DataManager
from xfactor.runner.BasicTaskManager import BasicTaskManager as TaskManager
import xfactor.FactorUtil as FactorUtil

'''
用作批量计算因子，时间跨度和因子个数均不限制
每日盘中或盘后计算，只计算一天，建议使用DailyRunner（为因子存储特殊优化）
run()会返回因子计算结果

options中的calc.num_cpus不设置或者设置为1时，将不采用并行化方式运行，该状态下可用来调试
'''


def run(factor_name_list, start_date, end_date, fix_config={}, input_factor_lib=None, output_factor_lib=None,
        save=False, options=None, fix_times=[]):
    calc_num_cpus = 1
    if options is not None and "calc.num_cpus" in options:
        calc_num_cpus = int(options["calc.num_cpus"])
    result = __calc_factor(factor_name_list, start_date, end_date, calc_num_cpus, fix_config, input_factor_lib,
                           None, None, fix_times)
    if save:
        if not os.path.exists(output_factor_lib):
            logger.error("因子库目录不存在:", output_factor_lib)
            raise Exception("因子库目录不存在:", output_factor_lib)
        elif not os.access(output_factor_lib, os.W_OK):
            logger.error("无因子库写入权限:", output_factor_lib)
            raise Exception("无因子库写入权限:", output_factor_lib)
        else:
            DataManager.save_factor(result, output_factor_lib)
            logger.info("因子已保存：output_factor_lib={}".format(output_factor_lib))
    return result


def __calc_factor(factor_name_list, start_date, end_date, calc_num_cpus, fix_config={}, input_factor_lib=None,
                  for_temp=None, with_temp=None, fix_times=[]):
    result = {}

    new_fix_config = {}
    for factor_name in factor_name_list:
        if factor_name not in fix_config:
            if len(fix_times) > 0:
                # fix_config中没有，fix_times也设置了，则以fix_times为准
                new_fix_config.update({factor_name: fix_times})
            else:
                # fix_config中没有，fix_times也没有,默认不传该因子的fix时点
                # 对于日频因子，本身不需要fix时点设置
                # 对于fix因子，如果不传fix时点，则默认为7个时间点
                continue
        else:
            if len(fix_times) > 0:
                # fix_config中有，fix_times也设置了，则取交集
                time_list = list(set(fix_times) & set(fix_config[factor_name]))
                if len(time_list) > 0:
                    new_fix_config.update({factor_name: time_list})
                else:
                    # 交集为空，则该因子不需要计算，在实盘中，指定了fix_times为单一时点，可以控制因子是否计算
                    factor_name_list.remove(factor_name)
            else:
                # fix_config中有，fix_times没有设置，以fix_config为准
                new_fix_config.update({factor_name: fix_config[factor_name]})

    task_manager = TaskManager(factor_name_list, start_date, end_date, new_fix_config, input_factor_lib)
    task_list = task_manager.generate_task(split_fix_factors=True)
    logger.info("计算开始：任务数={}, 进程数={}".format(len(task_list), calc_num_cpus))
    if calc_num_cpus == 1:
        task_results = [__execute_task(task, for_temp, with_temp) for task in task_list]
    else:
        pool = Pool(calc_num_cpus)
        task_ids = []
        for task in task_list:
            task_ids.append(pool.apply_async(__execute_task, (
                task, for_temp, with_temp
            )))
        pool.close()
        pool.join()
        task_results = [task_id.get() for task_id in task_ids]
    for sub_result in task_results:
        result = __merge_factor_values(result, sub_result)
    logger.info("全部计算完成")
    return result


# 运行指定task
def __execute_task(task, for_temp=None, with_temp=None):
    result = {}
    time1 = dt.datetime.now()
    database, data_info = DataManager.get_database_for_task(task, "offline")
    for factor_class in task["factor_class_list"]:
        factor_instance = FactorUtil.create_factor_instance(factor_class, task["fix_config"])
        sub_result = factor_instance.calc(database, data_info, task["calc_time_list"], task["full_datetime_list"],
                                          for_temp, with_temp)
        result = __merge_factor_values(result, sub_result)
    time2 = dt.datetime.now()
    logger.info("子任务完成：factors={}, start_date={}, end_date={}, calc_cost={}".format(
        list(result.keys()), task["calc_time_list"][0],
        task["calc_time_list"][-1],
        time2 - time1))
    return result


def __merge_factor_values(result, calc_result):
    for factor_name in calc_result:
        if factor_name in result:
            result[factor_name] = result[factor_name].append(calc_result[factor_name])
        else:
            result[factor_name] = calc_result[factor_name]
    return result
