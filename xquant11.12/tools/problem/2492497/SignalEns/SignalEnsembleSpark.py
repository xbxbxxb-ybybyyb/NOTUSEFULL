#-*- coding:utf-8 -*-
# author: 015629
# datetime:2022/12/13 15:46
import gc
import os
import uuid
from xquant.compute.sparkmr import Configuration
from xquant.compute.sparkmr import Job
from SignalEns.SignalEnsemble import SignalEnsemble
USER_ID = "015629"


class TaskMeta(object):
    def __init__(self, code, start_date, end_date, ensemble_mode, library_list, tag_type_list, save, save_library, save_tag_type, check, update_missing):
        self.code = code
        self.start_date = start_date
        self.end_date = end_date
        self.ensemble_mode = ensemble_mode
        self.library_list = library_list
        self.tag_type_list = tag_type_list
        self.save = save
        self.save_library = save_library
        self.save_tag_type = save_tag_type
        self.check = check
        self.update_missing = update_missing

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
        code = taskMeta.code
        start_date = taskMeta.start_date
        end_date = taskMeta.end_date
        ensemble_mode = taskMeta.ensemble_mode
        library_list = taskMeta.library_list
        tag_type_list = taskMeta.tag_type_list
        save = taskMeta.save
        save_library = taskMeta.save_library
        save_tag_type = taskMeta.save_tag_type
        check = taskMeta.check
        update_missing = taskMeta.update_missing

        exe = SignalEnsemble(code, start_date, end_date, ensemble_mode, library_list, tag_type_list, save, save_library, save_tag_type, check, update_missing)
        exe.run()

        gc.collect()

    def __getSparkConf(self, maxExecutorNum):
        config = Configuration()
        config._Configuration__config["framework"]["{}.executor.instances".format(
            config._Configuration__team_id)] = "{}".format(maxExecutorNum)
        config.set_app_name(str(self.__uuid))
        config.set_dst_dir("{}/Trash/{}/".format(USER_ID, self.__uuid))
        config.set_env_dir(self.__get_env_dir())
        config.set_executor_instances(str(min(len(self.__taskList), maxExecutorNum)))
        config.set_executor_memory("4G")

        return config

    @staticmethod
    def __get_env_dir():
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))