import os
import json
import multiprocessing
import queue
import time
import numpy as np
from collections import deque
from typing import Deque

import System.RemotePrint as rp
from ModelSystem.SignalEvaluate import SignalEvaluate
from Utils_BT.HelperFunctions import *
from Utils_BT.InputManager import *
from Utils_BT.ResultManager import ResultManager
from Utils_BT.TaskMeta import TaskMeta

from QuantFramework import Job
from QuantFramework import Configuration
from QuantFramework import HDFSFileHandler

from xquant.pyfile import Pyfile


def func_run_single(context, task_meta):
    if len(task_meta.get_symbols()) == 0:
        return
    symbol = task_meta.get_symbols()[0]
    input_manager = task_meta.get_input_manager()
    result_manager = task_meta.get_result_manager()
    py = Pyfile()
    try:
        with py.open(input_manager.trigger_json_dir + symbol + '.json', 'rb') as f:
            trigger_dict = f.read()
            trigger_dict = json.loads(trigger_dict)
    except Exception as e:
        rp.print(str(e) + '; return safely')
        return
    if not py.exists(input_manager.bt_dir + symbol + '/Data.pickle'):
        rp.print('Data.pickle for ' + symbol + ' does not exist; return safely')
        return
    try:
    # if True:
        input_manager.prepare_input_with_symbol(symbol)
    except Exception as e:
        return
    input_all = input_manager.get_input(symbol, 'all')
    se = SignalEvaluate(input_all, [(input_all.signal_data, trigger_dict)])
    try:
        se.evaluate(show='all')
    except Exception as e:
        rp.print('{} error: {}'.format(symbol, str(e)))
        return

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
        
    def start(self):
        print('Programme is running...')
        start = time.perf_counter()
        
        task_metas = []
        for symbol in self.__symbols:
            task_metas.append(TaskMeta([symbol], self.__input_manager, self.__result_manager))
        # print(self.__max_tasks)
        # res = self.__max_tasks - len(self.__symbols)
        # for i in range(res):
            # task_metas.append(TaskMeta([], self.__input_manager, self.__result_manager))
        
        config = Configuration()
        config.set_app_name(self.__get_app_name())
        config.set_dst_dir(self.__input_manager.output_dir)
        config.set_env_dir(self.__get_env_dir())
        config.set_executor_instances(self.__max_tasks)
        job = Job(config, 'Overwrite')
        job.add_tasks(task_metas)
        job.set_func(func_run_single)
        job.start()
        
        end = time.perf_counter()
        print('running time: ' + str(round((end - start) / 60, 2)) + 'min')
        
    def __get_app_name(self):
        path_name = self.__get_env_dir()
        path_name.split('/')
        index = path_name.index('repository')
        wid = path_name[index + 1]
        return 'BackTest_' + wid
        
    def __get_env_dir(self):
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

