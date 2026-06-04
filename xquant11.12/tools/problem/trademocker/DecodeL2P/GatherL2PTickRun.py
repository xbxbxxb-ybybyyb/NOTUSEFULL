#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/1/26 20:22
import ray
import gc
import datetime as dt
import multiprocessing as mp
from xquant.xqutils.helper import multicore_init
from Utils.HelpFunc import get_cbond_stock_map
from DecodeL2P.TaskMeta import TaskMeta
from DecodeL2P.SparkLauncher import SparkLauncher
from DecodeL2P.GatherL2PTick import GatherL2PTickData


def task_scheduler(l2pLibrary, stockList, cbondList, date, save, saveLibrary):

    taskList = []
    for stock, cbond in zip(stockList, cbondList):
        taskList.append(
            TaskMeta(
                l2pLibrary,
                stock,
                cbond,
                date,
                save,
                saveLibrary
            )
        )
    return taskList

def run_meta_task(taskMeta):
    l2pLibrary = taskMeta.getL2PLibrary()
    stock = taskMeta.getStock()
    cbond = taskMeta.getCBond()
    date = taskMeta.getDate()
    save = taskMeta.getSave()
    saveLibrary = taskMeta.getSaveLibrary()

    gtd = GatherL2PTickData(l2pLibrary, stock, cbond, save, saveLibrary)
    gtd.run(date)

    gc.collect()

def run_ray(task_list, options={"ray.num_cpus": 20, "object_store_memory": 10 ** 9 * 20}):
    num_cpus = 8
    object_store_memory = 10**9 * 8
    task_num = len(task_list)
    if options is not None:
        if "ray.num_cpus" in options:
            num_cpus = min(int(options["ray.num_cpus"]), task_num)
        if "ray.object_store_memory" in options:
            object_store_memory = min(options["ray.object_store_memory"], 10**9*num_cpus)

    assert multicore_init() == True
    ray.init(num_cpus=num_cpus, object_store_memory=object_store_memory)
    execute_task = ray.remote(run_meta_task)
    ray.get([execute_task.remote(task) for task in task_list])

    ray.shutdown()

def run_spark(taskList, maxExecutorNum):
    sparkLauncher = SparkLauncher()
    sparkLauncher.setTaskList(taskList)
    sparkLauncher.launch(maxExecutorNum)

def get_daily_level2plus_cbond(trading_day):
    from xquant.factordata import FactorData
    from xquant.bonddata import BondData
    fa = FactorData()
    bd = BondData()
    code_list = bd.get_bond_set(trading_day, "kzz")
    code_list = [c for c in code_list if c.endswith(".SZ")]
    daily_df = fa.get_factor_value("Basic_factor", code_list, [trading_day], ["trade_status", "volume"],
                                        category="bond").droplevel(0)
    daily_df = daily_df[((~daily_df["trade_status"].isnull()) & (daily_df["trade_status"] != "待核查")
                         & (daily_df["trade_status"] != "停牌") & (daily_df["trade_status"] != "0")
                         & (daily_df["volume"] != 0) )]
    cbond_list = sorted(daily_df.index.tolist())
    return cbond_list


if __name__ == "__main__":
    today = dt.datetime.today().strftime('%Y%m%d')
    l2pLibrary = "ZGLevel2PlusTicks"
    date = "20210518"
    save = True
    saveLibrary = "ZGLevel2PlusDataLib"
    mode = "Ray"
    maxExecutorNum = 300

    cbondList = get_daily_level2plus_cbond(date)
    cbond_stock_map = get_cbond_stock_map(cbondList, "CBOND")
    stockList = [cbond_stock_map.get(cbond) for cbond in cbondList]

    taskList = task_scheduler(l2pLibrary, stockList, cbondList, date, save, saveLibrary)
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

    elif mode == "Spark":
        run_spark(taskList, maxExecutorNum)
