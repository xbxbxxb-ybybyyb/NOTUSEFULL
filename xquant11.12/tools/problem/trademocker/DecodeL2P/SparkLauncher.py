import os
import uuid
from DecodeL2P.GatherL2PTick import GatherL2PTickData
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
        l2pLibrary = taskMeta.getL2PLibrary()
        stock = taskMeta.getStock()
        cbond = taskMeta.getCBond()
        date = taskMeta.getDate()
        save = taskMeta.getSave()
        saveLibrary = taskMeta.getSaveLibrary()

        gtd = GatherL2PTickData(l2pLibrary, stock, cbond, save, saveLibrary)

        gtd.run(date)

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
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
