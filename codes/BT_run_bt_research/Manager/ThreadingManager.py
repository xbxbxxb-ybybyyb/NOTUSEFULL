import os
import time
import json
from typing import List
#import Utils.Rpc.RemotePrint as rp
from Utils.MultiTasks import main_multiprocess
#from ModelSystem.SignalEvaluate import SignalEvaluate
from Manager.InputManager import InputManager
from Manager.ResultManager import ResultManager
from Utils.TaskMeta import TaskMeta
from QuantFramework import Job
from QuantFramework import Configuration
from xquant.xqutils.xqfile import HDFSFile


#hdfsfile = HDFSFile()


def func_run_single(context, task_meta, is_using_spark=True):
    if len(task_meta.get_symbols()) == 0:
        return
    symbol = task_meta.get_symbols()[0]
    input_manager = task_meta.get_input_manager()
    try:
        trigger_dict = load_trigger_dict(input_manager.trigger_json_dir, symbol, mode=2)
    except Exception as e:
        task_print(str(e) + '; return safely', is_using_spark)
        return

    #if not hdfsfile.exists('{}/{}/Data.pickle'.format(input_manager.bt_dir, symbol)):
    #    task_print('Data.pickle for {} does not exist; return safely'.format(symbol), is_using_spark)
    #    return

    #try:
    #    input_manager.reset_specific_parameters(trigger_dict)
    #    input_manager.prepare_input_with_symbol(symbol)
    #except Exception as e:
    #    return

    #input_all = input_manager.get_input(symbol, 'all')
    #se = SignalEvaluate(input_all, [(input_all.signal_data, trigger_dict)])
    #try:
    #    se.evaluate(show='all')
    #except Exception as e:
    #    task_print('{} error: {}'.format(symbol, str(e)), is_using_spark)
    #    return
    #print("Finish: {}".format(symbol))


class ThreadingManager:
    __slots__ = ['__input_manager', '__result_manager', '__result_keys', '__max_tasks',
                 '__symbols', '__results', '__exceeds_max_tasks', '__valid_symbols_params_splitted']

    def __init__(self, input_manager: 'InputManager', result_manager: 'ResultManager', max_tasks: int = 200):
        self.__input_manager = input_manager
        self.__result_manager = result_manager
        self.__result_keys = self.__result_manager.get_keys()
        self.__max_tasks: int = max_tasks
        self.__symbols: List[str] = input_manager.get_symbols()
        self.__results: List = []
        self.__exceeds_max_tasks: bool = True if len(self.__symbols) >= max_tasks else False
        self.__valid_symbols_params_splitted = None

    def start(self, mode):
        print('Programme is running...')
        start = time.perf_counter()

        task_metas = []
        for symbol in self.__symbols:
            task_metas.append(TaskMeta([symbol], self.__input_manager))

        if mode == "spark":
            config = Configuration()
            config.set_app_name('BackTest_')
            config.set_dst_dir(self.__input_manager.output_dir)
            config.set_env_dir(self.__get_env_dir())
            config.set_executor_instances(self.__max_tasks)
            job = Job(config, 'Overwrite')
            job.add_tasks(task_metas)
            job.set_func(func_run_single)
            job.start()

        elif mode == "local":
            self.task_single(task_metas)

        elif mode == "multiprocessing":
            main_multiprocess(task_single=self.task_single, para_list=task_metas, multiprocess_nums=20, is_sum_result=False)

        else:
            raise ValueError("mode只能在[spark, local, multiprocessing]中选择")

        end = time.perf_counter()
        print('running time: ' + str(round((end - start) / 60, 2)) + 'min')

    @staticmethod
    def task_single(task_metas_list):
        for i in task_metas_list:
            func_run_single("", i, is_using_spark=False)

    @staticmethod
    def __get_env_dir():
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def task_print(text, is_using_spark=True):
    if is_using_spark:
        rp.print(text)
    else:
        print(text)


def load_trigger_dict(trigger_json_dir, symbol, mode=1):
    """mode=1为实盘，mode=2为research"""
    hdfsfile = HDFSFile()
    if mode == 1:
        with hdfsfile.open("{}/{}.json".format(trigger_json_dir, symbol), 'rb') as f:
            trigger_dict = f.read()
            trigger_dict = json.loads(trigger_dict)
    else:
        print(1)
        with hdfsfile.open("{}/{}/triggerRatio.json".format(trigger_json_dir, symbol), 'rb') as f:
            print(2)
            trigger_dict = f.read()
            trigger_dict = json.loads(trigger_dict)
        trigger_dict["maxTurnoverPerOrder"] = 500000
        trigger_dict["maxExposure"] = 1000000
    return trigger_dict
