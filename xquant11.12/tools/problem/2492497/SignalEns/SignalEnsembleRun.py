#-*- coding:utf-8 -*-
# author: 015629
# datetime:2022/12/13 15:46
import gc
import ray
import pandas as pd
import multiprocessing as mp
from xquant.xqutils.helper import multicore_init
from SignalEns.SignalEnsemble import SignalEnsemble
from SignalEns.SignalEnsembleSpark import TaskMeta, SparkLauncher
from xquant.factordata import FactorData
fa = FactorData()


def task_scheduler(code_list, start_date, end_date, ensemble_mode, library_list, tag_type_list, save, save_library, save_tag_type, check, update_missing):
    taskList = []
    for code in code_list:
        taskList.append(
            TaskMeta(code, start_date, end_date, ensemble_mode, library_list, tag_type_list, save, save_library, save_tag_type, check, update_missing)
                )
    return taskList

def run_meta_task(taskMeta):
    code = taskMeta.code
    start_date = taskMeta.start_date
    end_date = taskMeta.end_date
    ensemble_mode = taskMeta.ensemble_mode
    library_list = taskMeta.library_list
    tag_type_list = taskMeta.tag_type_list
    save = taskMeta.save
    save_library = taskMeta.save_library
    save_tag_type = taskMeta.save_tag_type
    check = taskMeta.check
    update_missing = taskMeta.update_missing

    exe = SignalEnsemble(code, start_date, end_date, ensemble_mode, library_list, tag_type_list, save, save_library, save_tag_type,
                         check, update_missing)
    exe.run()

    gc.collect()

def run_ray(task_list, options={"ray.num_cpus": 20, "object_store_memory": 10 ** 9 * 20}):
    num_cpus = 8
    object_store_memory = 10 ** 9 * 8
    task_num = len(task_list)
    if options is not None:
        if "ray.num_cpus" in options:
            num_cpus = min(int(options["ray.num_cpus"]), task_num)
        if "ray.object_store_memory" in options:
            object_store_memory = min(options["ray.object_store_memory"], 10 ** 9 * num_cpus)

    assert multicore_init() == True
    ray.init(num_cpus=num_cpus, object_store_memory=object_store_memory)
    execute_task = ray.remote(run_meta_task)
    ray.get([execute_task.remote(task) for task in task_list])
    ray.shutdown()

def run_spark(taskList, maxExecutorNum):
    sparkLauncher = SparkLauncher()
    sparkLauncher.setTaskList(taskList)
    sparkLauncher.launch(maxExecutorNum)


if __name__ == "__main__":
    start_date = "20221213"
    end_date = "20221213"
    ensemble_mode = "Concat"
    # library_list = ["Albest20220201Order036Signals", "LightGBMRegr_DataSZ_Ev20220201Sample_036"]
    # tag_type_list = ["Common", "NChangeTime"]
    library_list = ["LightGBMRegr_DataSZ_Ev20220201Sample_036", "LightGBMRegr_DataSZ_Ev20220201Sample_147", "LightGBMRegr_DataSZ_Ev20220201Sample_25"]
    tag_type_list = ["NChangeTime", "NChangeTime", "NChangeTime"]
    save = True
    # save_library = "Albest20220201_LightGBMRegr_EvSample_036"
    # save_tag_type = "Common"
    save_library = "LightGBMRegr_DataSZ_Ev20220201Sample_1"
    save_tag_type = "NChangeTime"
    check = False
    update_missing = False

    mode = "Spark"
    maxExecutorNum = 1000

    # code_list = fa.hset("INDEX", "20220601", "ZZ800")["stock"].tolist() + fa.hset("INDEX", "20220601", "ZZ1000")["stock"].tolist()
    # code_list = sorted([c for c in code_list if c.endswith(".SZ")])
    code_list = pd.read_excel("/data/user/015629/CreateDailyEasyParamsNoBatchTick/Easy_20221213_Sim/easy_sim_20221213_5161206_no.xlsx")["证券代码"].tolist()
    taskList = task_scheduler(code_list, start_date, end_date, ensemble_mode, library_list, tag_type_list, save, save_library, save_tag_type, check, update_missing)
    print(" Total Task Num: {} ".format(len(taskList)))

    if mode == "Local":
        for task in taskList:
            run_meta_task(task)

    elif mode == "MultiProcess":
        if len(taskList) > 0:
            assert multicore_init() == True
            pool = mp.Pool(processes=min(24, len(taskList)))
            for task in taskList:
                pool.apply_async(run_meta_task, (task, ))
            pool.close()
            pool.join()

    elif mode == "Ray":
        run_ray(taskList)

    elif mode == "Spark":
        run_spark(taskList, maxExecutorNum)
