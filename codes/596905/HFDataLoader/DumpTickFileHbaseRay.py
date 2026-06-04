import ray
import pickle
import itertools
from HFDataLoader.DumpTickFileHbase import DumpTickFileHbase
from HFDataLoader.DumpTickFileHbase import DumpTickFileHbase2
from HFDataLoader.DumpTickFileHbase import get_codeDateDict_HDFS, get_codeDateDict_NAS
from xquant.xqutils.helper import multicore_init


def run_meta_task(lib_name, hdfs_path, code, date_list, hbase, env):
    dtfh = DumpTickFileHbase(lib_name, hdfs_path, code, date_list, hbase, env)
    dtfh.run_dump()

def run_meta_task2(lib_name, nas_path, code, date_list):
    dtfh = DumpTickFileHbase2(lib_name, nas_path, code, date_list)
    dtfh.run_dump()

@ray.remote
def execute_task(task):
    run_meta_task(task["lib_name"], task["hdfs_path"], task["code"], task["date_list"], task["hbase"], task["env"])

@ray.remote
def execute_task2(task):
    run_meta_task2(task["lib_name"], task["nas_path"], task["code"], task["date_list"])


def run_ray(task_list, execute_task, options={"ray.num_cpus": 10, "object_store_memory": 10 ** 9 * 10}):
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
    ray.get([execute_task.remote(task) for task in task_list])

    # id_lists = ray.get([execute_task.remote(task) for task in task_list])
    # undo_ids = list(itertools.chain(*id_lists))
    # print("Total tiny task num:", len(undo_ids))
    #
    # while len(undo_ids):
    #     done_ids, undo_ids = ray.wait(undo_ids, min(200, len(undo_ids)))
    #     ray.get(done_ids)

    ray.shutdown()


if __name__=="__main__":
    lib_name = "XHFDataLib"
    hdfs_path = "HFDataDump/T"
    nas_path = "/data/user/015629/HFDataDump/T"
    hbase = True
    env = "Docker"

    flag = "HDFS" # "NAS"

    if flag == "HDFS":
        codeDateDict = get_codeDateDict_HDFS(hdfs_path=hdfs_path, save=False)
        # with open('/data/user/015629/MISC/codeDateDictHDFS.pkl', 'rb') as f:
        #     codeDateDict = pickle.load(f)

        task_list = []
        for code, date_list in codeDateDict.items():
            if len(date_list) > 0:
                task = dict()
                task["lib_name"] = lib_name
                task["hdfs_path"] = hdfs_path
                task["code"] = code
                task["date_list"] = date_list
                task["hbase"] = hbase
                task["env"] = env
                task_list.append(task)

        run_ray(task_list, execute_task)

#############################################################################
    if flag == "NAS":

        codeDateDict = get_codeDateDict_NAS(nas_path=nas_path, save=False)
        # with open('/data/user/015629/MISC/codeDateDictNAS.pkl', 'rb') as f:
        #     codeDateDict = pickle.load(f)

        task_list = []
        for code, date_list in codeDateDict.items():
            if len(date_list) > 0:
                task = dict()
                task["lib_name"] = lib_name
                task["nas_path"] = nas_path
                task["code"] = code
                task["date_list"] = date_list
                task_list.append(task)

        run_ray(task_list, execute_task2)







