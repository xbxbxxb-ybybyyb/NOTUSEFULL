import os
import uuid
from HFDataLoader.DumpTickFileHbase import DumpTickFileHbase
from xquant.compute.sparkmr import Configuration
from xquant.compute.sparkmr import Job


class SparkLauncher:
    def __init__(self):
        self.__uuid = uuid.uuid1()

        self.__taskList = None

    def setTaskList(self, taskList):
        self.__taskList = taskList

    def launch(self):
        config = self.__getSparkConf()
        job = Job(config, mode="OverWrite")
        job.add_tasks(self.__taskList)
        job.set_func(self.func)
        job.start()

    @staticmethod
    def func(context, taskMeta):
        marketDataLibrary = taskMeta.getMarketDataLibrary()
        hdfsPath = taskMeta.getHdfsPath()
        stock = taskMeta.getStock()
        dateList = taskMeta.getDateList()
        hbase = taskMeta.getHbase()
        env = taskMeta.getEnv()

        dtfh = DumpTickFileHbase(marketDataLibrary, hdfsPath, stock, dateList, hbase, env)
        dtfh.run_dump()

    def __getSparkConf(self):
        config = Configuration()
        config.set_app_name(str(self.__uuid))
        config.set_dst_dir("015629/Trash/{}/".format(self.__uuid))
        config.set_env_dir(self.__get_env_dir())
        config.set_executor_instances(str(min(len(self.__taskList), 600)))
        config.set_executor_memory("4G")

        return config

    @staticmethod
    def __get_env_dir():
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
