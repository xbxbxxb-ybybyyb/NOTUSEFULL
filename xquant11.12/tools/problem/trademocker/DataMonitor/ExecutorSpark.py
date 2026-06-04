import os
import uuid
import gc
from DataMonitor.Executor import Executor
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
        job.add_tasks(self.__taskList)
        job.set_func(self.func)
        job.start()

    @staticmethod
    def func(context, taskMeta):
        library = taskMeta.getLibrary()
        code = taskMeta.getCode()
        dataSource = taskMeta.getDataSource()
        startDate = taskMeta.getStartDate()
        endDate = taskMeta.getEndDate()
        daily = taskMeta.getDaily()
        minute = taskMeta.getMinute()
        tick = taskMeta.getTick()
        tran = taskMeta.getTran()
        order = taskMeta.getOrder()
        overwrite = taskMeta.getOverwrite()
        monitor = taskMeta.getMonitor()
        hbase = taskMeta.getHbase()
        saveFile = taskMeta.getSaveFile()
        savePath = taskMeta.getSavePath()
        saveCheck = taskMeta.getSaveCheck()
        saveCheckPath = taskMeta.getSaveCheckPath()
        updateMissing = taskMeta.getUpdateMissing()

        Executor(library, code, dataSource, startDate, endDate, daily, minute, tick, tran, order,
             overwrite, monitor, hbase, saveFile, savePath, saveCheck, saveCheckPath, updateMissing)

        gc.collect()

    def __getSparkConf(self, maxExecutorNum):
        config = Configuration()
        config.set_app_name(str(self.__uuid))
        config.set_dst_dir("015629/Trash/{}/".format(self.__uuid))
        config.set_env_dir(self.__get_env_dir())
        config.set_executor_instances(str(min(len(self.__taskList), maxExecutorNum)))
        config.set_executor_memory("4G")

        return config

    @staticmethod
    def __get_env_dir():
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))