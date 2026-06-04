import pickle
from xquant.xqutils.helper import multicore_init
import multiprocessing as mp
from HFDataLoader.DumpTickFileHbase import DumpTickFileHbase, get_codeDateDict_HDFS
from HFDataLoader.DumpTickFileHbase import DumpTickFileHbase2, get_codeDateDict_NAS


def run_meta_task(lib_name, hdfs_path, code, date_list, hbase, env):
    dtfh = DumpTickFileHbase(lib_name, hdfs_path, code, date_list, hbase, env)
    dtfh.run_dump()

def run_meta_task2(lib_name, nas_path, code, date_list):
    dtfh = DumpTickFileHbase2(lib_name, nas_path, code, date_list)
    dtfh.run_dump()


if __name__=="__main__":
    lib_name = "XHFDataLib"
    hdfs_path = "HFDataDump/T"
    nas_path = "/data/user/015629/HFDataDump/T"
    hbase = True
    env = "Docker"
    flag = "HDFS" # "NAS"
    isMultiProcess = False

    if flag == "HDFS":

        codeDateDict = get_codeDateDict_HDFS(hdfs_path=hdfs_path, save=False)
        # with open('/data/user/015629/MISC/codeDateDictHDFS.pkl', 'rb') as f:
        #     codeDateDict = pickle.load(f)

        if not isMultiProcess:
            for code, date_list in codeDateDict.items():
                if len(date_list) > 0:
                    run_meta_task(lib_name, hdfs_path, code, date_list, hbase, env)

        else:
            task_list = []
            for code, date_list in codeDateDict.items():
                if len(date_list) > 0:
                    task = (lib_name, hdfs_path, code, date_list, hbase, env, )
                    task_list.append(task)

            if len(task_list) > 0:
                assert multicore_init() == True
                pool = mp.Pool(processes=min(20, len(task_list)))
                for task in task_list:
                    pool.apply_async(run_meta_task, task)
                pool.close()
                pool.join()

    if flag == "NAS":
        codeDateDict = get_codeDateDict_NAS(nas_path=nas_path, save=False)
        # with open('/data/user/015629/MISC/codeDateDictNAS.pkl', 'rb') as f:
        #     codeDateDict = pickle.load(f)

        if not isMultiProcess:
            for code, date_list in codeDateDict.items():
                if len(date_list) > 0:
                    run_meta_task2(lib_name, nas_path, code, date_list)

        else:
            task_list = []
            for code, date_list in codeDateDict.items():
                if len(date_list) > 0:
                    task = (lib_name, nas_path, code, date_list, hbase, env,)
                    task_list.append(task)

            if len(task_list) > 0:
                assert multicore_init() == True
                pool = mp.Pool(processes=min(20, len(task_list)))
                for task in task_list:
                    pool.apply_async(run_meta_task, task)
                pool.close()
                pool.join()




