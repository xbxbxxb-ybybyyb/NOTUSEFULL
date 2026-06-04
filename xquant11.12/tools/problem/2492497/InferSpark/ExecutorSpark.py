import os
import uuid
import gc
from InferSpark.CalcSignal import CalcSignal
from xquant.compute.sparkmr import Configuration
from xquant.compute.sparkmr import Job


class SparkLauncher:
    def __init__(self):
        self.__uuid = uuid.uuid1()

        self.__taskList = None

    def setTaskList(self, taskList):
        self.__taskList = taskList

    def launch(self, maxExecutorNum):
        config = self.__getSparkConf(maxExecutorNum)
        job = Job(config, mode="OverWrite")
        job._Job__executor_task_num = 1
        job.add_tasks(self.__taskList)
        job.set_func(self.func)
        job.start()

    @staticmethod
    def func(context, taskMeta):
        os.environ["OPENBLAS_NUM_THREADS"] = "1"
        os.environ["MKL_NUM_THREADS"] = "1"

        codeList = taskMeta.codeList
        startDate = taskMeta.startDate
        endDate = taskMeta.endDate
        modelName = taskMeta.modelName
        modelPath = taskMeta.modelPath
        factorLibraryList = taskMeta.factorLibraryList
        factorNamesDict = taskMeta.factorNamesDict
        windowSizeDict = taskMeta.windowSizeDict
        save = taskMeta.save
        saveLibraryList = taskMeta.saveLibraryList
        concat1sSignal = taskMeta.concat1sSignal
        save1sLibrary = taskMeta.save1sLibrary

        for code in codeList:
            cs = CalcSignal(code, startDate, endDate, modelName, modelPath, factorLibraryList, factorNamesDict,
                            windowSizeDict, save, saveLibraryList, concat1sSignal, save1sLibrary)
            cs.calculate()

            gc.collect()

    def __getSparkConf(self, maxExecutorNum):
        config = Configuration()
        config.set_app_name(str(self.__uuid))
        config.set_dst_dir("013050/Trash/{}/".format(self.__uuid))
        config.set_env_dir(self.__get_env_dir())
        config.set_executor_instances(str(min(len(self.__taskList), maxExecutorNum)))
        config.set_executor_memory("5G")
#        config.set_driver_memory('32G')

        return config

    @staticmethod
    def __get_env_dir():
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))