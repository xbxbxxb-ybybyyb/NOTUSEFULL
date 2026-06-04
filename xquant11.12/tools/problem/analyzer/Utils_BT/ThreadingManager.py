import os
import time
import uuid
from ModelSystem.SignalEvaluate import SignalEvaluate
from Utils_BT.HelperFunctions import *
from Utils_BT.InputManager import *
from Utils_BT.ResultManager import ResultManager
from Utils_BT.TaskMeta import TaskMeta
from xquant.xqutils.xqfile import HDFSFile
from xquant.compute.sparkmr import Configuration
from xquant.compute.sparkmr import Job


def func_run_single(context, task_meta):
    if len(task_meta.get_symbols()) == 0:
        return
    symbol = task_meta.get_symbols()[0]
    input_manager = task_meta.get_input_manager()
    result_manager = task_meta.get_result_manager()
    hf = HDFSFile()
    try:
        with hf.open(input_manager.trigger_json_dir + symbol + '.json', 'rb') as f:
            trigger_dict = f.read()
            trigger_dict = json.loads(trigger_dict)
    except Exception as e:
        print(str(e) + '; return safely')
        return
    if not hf.exists(input_manager.bt_dir + symbol + '/Data.pickle'):
        print('Data.pickle for ' + symbol + ' does not exist; return safely')
        return
    try:
        input_manager.prepare_input_with_symbol(symbol)
    except Exception as e:
        return
    input_all = input_manager.get_input(symbol, 'all')
    se = SignalEvaluate(input_all, [(input_all.signal_data, trigger_dict)])
    try:
        se.evaluate(show='all')
    except Exception as e:
        print('{} error: {}'.format(symbol, str(e)))
        return

class ThreadingManager:

    def __init__(self, input_manager: 'InputManager', result_manager: 'ResultManager'):
        self.__input_manager = input_manager
        self.__result_manager = result_manager
        self.__result_keys = self.__result_manager.get_keys()
        self.__symbols: List[str] = input_manager.get_symbols()

    def start(self):
        print('Programme is running...')
        start = time.perf_counter()
        context = None
        for symbol in self.__symbols:
            task_meta = TaskMeta([symbol], self.__input_manager, self.__result_manager)
            func_run_single(context, task_meta)

        end = time.perf_counter()
        print('running time: ' + str(round((end - start) / 60, 2)) + 'min')


class ThreadingManagerSpark:

    def __init__(self, input_manager: 'InputManager', result_manager: 'ResultManager', max_tasks: int = 200):
        self.__input_manager = input_manager
        self.__result_manager = result_manager
        self.__result_keys = self.__result_manager.get_keys()
        self.__max_tasks: int = max_tasks
        self.__symbols: List[str] = input_manager.get_symbols()
        self.__results: List = []
        self.__exceeds_max_tasks: bool = True if len(self.__symbols) >= max_tasks else False
        self.__valid_symbols_params_splitted = None

        self.__uuid = uuid.uuid1()

    def start(self):
        print('Programme is running...')
        start = time.perf_counter()

        task_metas = []
        for symbol in self.__symbols:
            task_metas.append(TaskMeta([symbol], self.__input_manager, self.__result_manager))

        config = Configuration()
        config.set_app_name(str(self.__uuid))
        config.set_dst_dir(self.__input_manager.output_dir)
        config.set_env_dir(self.__get_env_dir())
        config.set_executor_instances(self.__max_tasks)
        config.set_executor_memory("4G")

        job = Job(config, 'Overwrite')
        job.add_tasks(task_metas)
        job.set_func(func_run_single)
        job.start()

        end = time.perf_counter()
        print('running time: ' + str(round((end - start) / 60, 2)) + 'min')

    def __get_env_dir(self):
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


