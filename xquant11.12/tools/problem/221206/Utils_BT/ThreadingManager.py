import os
import time
import json
import DataAPI.DataToolkit as dtk
import System.RemotePrint as rp
from typing import List
from ModelSystem.SignalEvaluate import SignalEvaluate
from Utils_BT.InputManager import *
from Utils_BT.ResultManager import ResultManager
from Utils_BT.TaskMeta import TaskMeta
from QuantFramework import Job
from QuantFramework import Configuration
from xquant.pyfile import Pyfile


def func_run_single(context, task_meta):
    trigger_names = ["longAggressiveRatio", "longPassiveRatio", "shortAggressiveRatio", "shortPassiveRatio"]
    if len(task_meta.get_symbols()) == 0:
        return
    symbol = task_meta.get_symbols()[0]
    input_manager = task_meta.get_input_manager()
    py = Pyfile()

    try:
        with py.open(input_manager.trigger_path + symbol + '.json', 'rb') as f:
            trigger_dict = f.read()
            trigger_dict = json.loads(trigger_dict)
    except Exception as e:
        rp.print(str(e))
        return
    trigger_dict = {k: float(v) for k, v in trigger_dict.items() if k in trigger_names}

    if not py.exists(input_manager.bt_dir + symbol + '/Data.pickle'):
        rp.print('Data.pickle for ' + symbol + ' does not exist; return safely')
        return
    buy_vwap_df, sell_vwap_df = task_meta.get_params()

    try:
    # if True:
        input_manager.prepare_input_with_symbol(symbol, (buy_vwap_df, sell_vwap_df))
    except Exception as e:
        rp.print(symbol + ' exception: ' + repr(e))
        return
    input_all = input_manager.get_input(symbol, 'all')

    se = SignalEvaluate(input_all, [(input_all.signal_data, trigger_dict)])
    se.evaluate(show='all')


class ThreadingManager:
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

        buy_vwap_df = dtk.get_panel_daily_pv_df(
            self.__symbols,
            self.__input_manager.get_start_date(),
            self.__input_manager.get_end_date(),
            'buy_vwap'
        )
        sell_vwap_df = dtk.get_panel_daily_pv_df(
            self.__symbols,
            self.__input_manager.get_start_date(),
            self.__input_manager.get_end_date(),
            'sell_vwap'
        )
        # signals_dict = hf.load_signals(self.__input_manager.bt_dir, self.__symbols, self.__input_manager.signal_csv_dir)

        task_metas = []
        for symbol in self.__symbols:
            task_metas.append(
                TaskMeta([symbol], self.__input_manager, self.__result_manager, (buy_vwap_df, sell_vwap_df))
            )

        config = Configuration()
        config.set_app_name(self.__get_app_name())
        config.set_dst_dir(self.__input_manager.output_dir)
        config.set_env_dir(self.__get_env_dir())
        config.set_executor_instances(self.__max_tasks)
        config.set_executor_memory('5G')
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
