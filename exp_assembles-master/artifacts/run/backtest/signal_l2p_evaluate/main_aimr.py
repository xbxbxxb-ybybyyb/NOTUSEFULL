from xquant.compute.aimr import AIMR
import time
import datetime
import json
import os
import uuid
import os
import uuid

param_file = os.path.join("./aimr_params_tmp.txt")  # 用于子docker加载标的列表

num_cpus = 30  # 每个docker的cpu数
num_memory = 5 * num_cpus * 1000  # 每个docker的内存数
node_parallel_loops = 1

def write_param_list(symbol_list, label_name, exp_name, version_alias):
    params = {
        "label_name": label_name,
        "exp_name": exp_name,
        "version_alias": version_alias,
        "symbol_list": symbol_list
    }
    json.dump(params, open(param_file, "w"))


def load_param_dict(param_id):
    params = json.load(open(param_file, "r"))
    pairs_all = params["symbol_list"]
    print(pairs_all)
    start_idx = num_cpus * node_parallel_loops * param_id  # 一个docker开始处理的标的个数
    pairs = pairs_all[start_idx:start_idx + num_cpus * node_parallel_loops]
    params["symbol_list"] = pairs
    return params

if __name__ == '__main__':

    print("start")
    t1 = time.time()

    # （1）设置回测标的
    # 研究信号路径
    exp_list = [
        # ("LabelFirstPeak_th10_60s", "KG101_model", 'HS_tick2'),
        ("LabelFirstPeak_th10_120s", "exp_l3_hs300_flying5_levelone_noflying", 'LabelFirstPeak_th10_120s_factor10__hs300mid_sh53_levelone_noflying_log2'),
        # ("LabelFirstPeakAdjust0_th10_60s", "exp_l3_hs300_new_flying5_levelone",
        #  'LabelFirstPeakAdjust0_th10_60s_factor133_arbitrade0_120_log2')
    ]
    label_name, exp_name, version_alias = exp_list[0]
    symbol_list = ['688037.SH']#backtest_params.get_valid_symbols()

    # （2）设置回测并发
    #  最佳实践，每个docker运行本身都会占用CPU和docker，尽量起一个较大的docker，在docker内并发运行多组标的。
    node_process_symbols = num_cpus * node_parallel_loops # 每个docker处理的标的个数，乘以node_parallel_loops相当于每个cpu处理node_parallel_loops个标的任务
    groups = len(symbol_list)//node_process_symbols+1 if not len(symbol_list)%node_process_symbols==0 else len(symbol_list)//node_process_symbols

    params = {
        "parallel_list": list(range(groups)), #元素的个数就是docker的个数
        "tag":"xquant",
        "cpu": num_cpus,
        "gpu":0,
        "memory": num_memory,
        "docker_version":"cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:dol_genesis_cpu"
    }
    print("需要启动的docker数目为：{}, 单个docker的cpus {} , memory {} GB, 并发度 {}，每个docker处理的标的数：{}".format(groups, num_cpus, num_memory/1000, num_cpus, node_process_symbols))
    print("Warning: 若资源不够，docker会排队启动...")


    # （3）启动AIMR并行Docker
    entry_file = 'shell_parallel_xbrain_backtest_updw.py' # 每个docker的入口文件
    write_param_list(symbol_list, label_name, exp_name, version_alias)

    #job.py文件为用户自定义的并行任务文件
    status_iterator = AIMR.runTasksYieldStatus(entry_file,json.dumps(params))
    for status_df in status_iterator:
        """
        执行next(status_iterator)表示接着上一次的结果继续运行AIMR任务,由于最大并行度subtask_limit_num限制，可能还有子任务未创建。
        若所有子任务都已经创建，则仅返回最新的未完成任务的状态；若还有子任务未创建，执行next(status_iterator)则先创建任务，再返回最新的未完成任务的状态；
        """
        print("运行已耗时：", time.time()-t1)
        print(status_df)
        """
        parallel_params表示AIMR每个子任务的并行化参数，返回的状态含义如下：
            parallel_params为0-10，表示运行成功的任务(不会在status_df中显示）；
            parallel_params为9，表示运行失败的任务，并有具体的出错原因；
            parallel_params为10-12，表示运行中的任务；
            parallel_params为13-16，表示任务创建完毕，正在调度到AI平台执行；
            parallel_params为17-19，表示未创建的任务，需调用next(status_iterator)继续创建任务。
           pycharm_group       start_time             parallel_params  status status_detail                                job_id
        0  1314476_pqryLzle 2021-09-14 18:49:58               9      运行出错        OOM错误  472e7658-54a7-48e0-9170-88d3a1c1b2be
        1  1314476_pqryLzle 2021-09-14 18:50:39               10     运行中          None  80415289-892b-4893-8bd2-39ecb772d28e
        2  1314476_pqryLzle 2021-09-14 18:50:54               11     运行中          None  b659456b-1715-460c-8569-bc8e09c8fac9
        3  1314476_pqryLzle 2021-09-14 18:50:56               12     运行中          None  9c7ecadf-8443-4602-949f-4fd187f2b63d
        4  1314476_pqryLzle 2021-09-14 18:51:11               13  下发AI平台          None  30f71ccc-f879-4080-a0a3-25b021828648
        5  1314476_pqryLzle 2021-09-14 18:51:11               44  下发AI平台          None  ef29647e-04e4-4083-8fef-99e2aaa4dce6
        6  1314476_pqryLzle 2021-09-14 18:51:22               15  下发AI平台          None  ee5bed74-ab57-4636-af18-60158e52c52e
        7  1314476_pqryLzle 2021-09-14 18:51:27               66  下发AI平台          None  6877d061-0c67-4404-9dab-4154bf6aac19
        8        None                       NaT               17     准备中          None                                  None
        9        None                       NaT               18     准备中          None                                  None
        10       None                       NaT               18     准备中          None                                  None
        """
    print("总耗时", time.time()-t1)


    ####################################################
