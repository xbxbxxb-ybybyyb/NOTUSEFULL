import json
import ray
import multiprocessing as mp
from xquant.xqutils.helper import multicore_init
from xquant.compute.aimr import AIMR
from Common.TaskMeta import TaskMeta
from InferSignal.CalcSignal import run_meta_task
from InferSpark.CalcSignal import run_meta_task_numpy
from InferSpark.ExecutorSpark import SparkLauncher
from Utils.HelpFunc import split_calc_index_into_group


class CalculationScheduler:
    def __init__(self):
        self.signalConfig = None
        self.infer_type = "tensorflow"
        self.mode = "Local"
        self.aimr_num = 0
        self.cpus_num = 20
        self.max_executor_num = 400
        self.taskList = []

    def setSignalConfig(self, signalConfig):
        self.signalConfig = signalConfig
        self.infer_type = self.signalConfig.infer_type
        self.mode = self.signalConfig.mode
        self.aimr_num = self.signalConfig.aimr_num
        self.cpus_num = self.signalConfig.cpus_num
        self.max_executor_num = self.signalConfig.max_executor_num

    def setTaskList(self, taskList):
        self.taskList = taskList

    def startCalculation(self):
        """"""
        self.taskList = self.split_tasks()

        if self.infer_type == "numpy":
            if self.mode == "Local":
                for task in self.taskList:
                    run_meta_task_numpy(task)
            elif self.mode == "MultiProcess":
                assert multicore_init() == True
                pool = mp.Pool(processes=min(self.cpus_num, len(self.taskList)))
                for task in self.taskList:
                    pool.apply_async(run_meta_task_numpy, (task,))
                pool.close()
                pool.join()
            elif self.mode == "Ray":
                self.run_tasks_with_numpy_ray(self.taskList, options={"ray.num_cpus": self.cpus_num,
                                                    "object_store_memory": 10 ** 9 * self.cpus_num}
                                        )
            elif self.mode == "Spark":
                self.run_tasks_with_numpy_spark()
            else:
                raise Exception(" Only Support Local/Ray/MultiProcess/Spark with Numpy Model Inference ")
        else:
            if self.aimr_num == 0:
                if self.mode == "Local":
                    for task in self.taskList:
                        run_meta_task(task)
                elif self.mode == "MultiProcess":
                    assert multicore_init() == True
                    pool = mp.Pool(processes=min(self.cpus_num, len(self.taskList)))
                    for task in self.taskList:
                        pool.apply_async(run_meta_task, (task,))
                    pool.close()
                    pool.join()
                else:
                    self.run_tasks_with_ray(self.taskList, options={"ray.num_cpus": self.cpus_num,
                                            "object_store_memory": 10 ** 9 * self.cpus_num }
                    )
            else:
                self.run_tasks_with_aimr()

    def split_tasks(self):
        taskList = []
        for task in self.signalConfig.get_task_list():
            codeList, subStartDate, subEndDate = task
            taskList.append(
                    TaskMeta(
                        codeList,
                        subStartDate,
                        subEndDate,
                        self.signalConfig.model_name,
                        self.signalConfig.model_path,
                        self.signalConfig.factor_library_list,
                        self.signalConfig.factor_names_dict,
                        self.signalConfig.window_size_dict,
                        self.signalConfig.save,
                        self.signalConfig.save_library_list,
                        self.signalConfig.concat_1s_signal,
                        self.signalConfig.save_1s_library
                    )
                )
        return taskList

    @staticmethod
    def run_tasks_with_ray(task_list, options={"ray.num_cpus": 20, "object_store_memory": 10 ** 9 * 20}):
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

    def run_tasks_with_aimr(self):
        task_index_list = range(len(self.taskList))
        task_index_groups = split_calc_index_into_group(task_index_list, self.aimr_num)
        parallelList = ["{}-{}-{}-{}".format(task_index[0], task_index[-1], self.cpus_num, self.mode) for task_index in task_index_groups]

        params = {
            "parallel_list": parallelList,
            # "docker_version": "cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:prd_v3.0",
            # "docker_version": "cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:prd_gpu_v3.0",
            "tag": "xquant",
            "cpu": self.cpus_num,
            "gpu": 0,
            "memory": 1024 * self.cpus_num * 4
        }
        print(params)

        AIMR.runTasks("InferSignal/AIMRWorker.py", json.dumps(params))

    @staticmethod
    def run_tasks_with_numpy_ray(task_list, options={"ray.num_cpus": 20, "object_store_memory": 10 ** 9 * 20}):
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
        execute_task = ray.remote(run_meta_task_numpy)
        ray.get([execute_task.remote(task) for task in task_list])

        ray.shutdown()

    def run_tasks_with_numpy_spark(self):
        sparkLauncher = SparkLauncher()
        sparkLauncher.setTaskList(self.taskList)
        sparkLauncher.launch(self.max_executor_num)
