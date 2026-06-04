import ray
import multiprocessing as mp
from DataInterface.Config import TICK_SUFFIX, TRANSACTION_SUFFIX, ORDER_SUFFIX
from DataUpdate.DumpFileHbase import get_code_date_dict, TaskMeta, DumpFileHbase
from xquant.xqutils.helper import multicore_init


def task_scheduler(library, hdfs_path, tick, tran, order):

    taskList = []

    if tick:
        tick_code_date_dict = get_code_date_dict(hdfs_path, "Tick")
        for code, date_list in tick_code_date_dict.items():
            taskList.append(
                TaskMeta(
                    library,
                    hdfs_path,
                    TICK_SUFFIX,
                    code,
                    date_list
                )
            )

    if tran:
        tran_code_date_dict = get_code_date_dict(hdfs_path, "Transaction")
        for code, date_list in tran_code_date_dict.items():
            taskList.append(
                TaskMeta(
                    library,
                    hdfs_path,
                    TRANSACTION_SUFFIX,
                    code,
                    date_list
                )
            )

    if order:
        order_code_date_dict = get_code_date_dict(hdfs_path, "Order")
        for code, date_list in order_code_date_dict.items():
            taskList.append(
                TaskMeta(
                    library,
                    hdfs_path,
                    ORDER_SUFFIX,
                    code,
                    date_list
                )
            )

    return taskList

def run_meta_task(taskMeta):
    library = taskMeta.getLibrary()
    hdfs_path = taskMeta.getHdfsPath()
    data_type = taskMeta.getDataType()
    code = taskMeta.getCode()
    date_list = taskMeta.getDateList()

    dfh = DumpFileHbase(library, hdfs_path, data_type, code, date_list)

    dfh.run()

def run_ray(task_list, options={"ray.num_cpus": 10, "object_store_memory": 10 ** 9 * 10}):
    num_cpus = 4
    object_store_memory = 10**9*4
    task_num = len(task_list)
    if options is not None:
        if "ray.num_cpus" in options:
            num_cpus = min(int(options["ray.num_cpus"]), task_num)
        if "ray.object_store_memory" in options:
            object_store_memory = min(options["ray.object_store_memory"], 10**9*task_num)

    assert multicore_init() == True
    ray.init(num_cpus=num_cpus, object_store_memory=object_store_memory)
    execute_task = ray.remote(run_meta_task)
    ray.get([execute_task.remote(task) for task in task_list])

    ray.shutdown()


if __name__=="__main__":
    library = "ZeusDataLib"
    hdfs_path = "ZeusDataDump"
    tick = False
    tran = False
    order = True
    mode = "Ray"

    taskList = task_scheduler(library, hdfs_path, tick, tran, order)
    print(" Total Task Num: {} ".format(len(taskList)))

    if mode == "Local":
        for task in taskList:
            run_meta_task(task)

    elif mode == "MultiProcess":
        if len(taskList) > 0:
            assert multicore_init() == True
            pool = mp.Pool(processes=min(20, len(taskList)))
            for task in taskList:
                pool.apply_async(run_meta_task, (task, ))
            pool.close()
            pool.join()

    elif mode == "Ray":
        run_ray(taskList)






