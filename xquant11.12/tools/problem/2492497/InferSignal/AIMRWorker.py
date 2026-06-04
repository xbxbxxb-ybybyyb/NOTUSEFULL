#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/7/22 9:58
import ray
import multiprocessing as mp
from xquant.xqutils.helper import multicore_init
from xquant.compute.aimr import AIMR
from Common.TaskMeta import TaskMeta
from SignalConfig import SignalConfig
from InferSignal.CalcSignal import run_meta_task


def work():
    start_index, end_index, cpus_num, mode = AIMR.getParam().split("-")
    start_index, end_index, cpus_num = int(start_index), int(end_index), int(cpus_num)

    signalConfig = SignalConfig(enable=False)
    task_list = signalConfig.task_list[start_index: end_index + 1]

    taskList = []
    for task in task_list:
        codeList, subStartDate, subEndDate = task
        taskList.append(
            TaskMeta(
                codeList,
                subStartDate,
                subEndDate,
                signalConfig.model_name,
                signalConfig.model_path,
                signalConfig.factor_library_list,
                signalConfig.factor_names_dict,
                signalConfig.window_size_dict,
                signalConfig.save,
                signalConfig.save_library_list,
                signalConfig.concat_1s_signal,
                signalConfig.save_1s_library
            )
        )

    assert multicore_init() == True

    if mode == "MultiProcess":
        pool = mp.Pool(processes=min(cpus_num, len(taskList)))
        for task in taskList:
            pool.apply_async(run_meta_task, (task,))
        pool.close()
        pool.join()

    elif mode == "Ray":
        object_store_memory = 10 ** 9 * cpus_num
        ray.init(num_cpus=cpus_num, object_store_memory=object_store_memory)
        execute_task = ray.remote(run_meta_task)
        ray.get([execute_task.remote(task) for task in taskList])
        ray.shutdown()

    else:
        raise ValueError(" Not Supported Run Mode {} with AIMR ".format(mode))

if __name__ == "__main__":
    work()
