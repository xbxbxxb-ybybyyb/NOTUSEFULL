import os
import time
import DataAPI.DataToolkit as dtk
import System.RemotePrint as rp
from typing import List
from ModelSystem.SignalEvaluate import SignalEvaluate
from Utils_CV.InputManager import *
from Utils_CV.ResultManager import ResultManager
from Utils_CV.TaskMeta import TaskMeta
from QuantFramework import Job
from QuantFramework import Configuration
from xquant.pyfile import Pyfile


def func_run_single(context, task_meta):
    py = Pyfile()
    if len(task_meta.get_symbols()) == 0:
        return
    symbol = task_meta.get_symbols()[0]
    input_manager = task_meta.get_input_manager()
    result_manager = task_meta.get_result_manager()
    if not py.exists(input_manager.bt_dir + symbol + '/Data.pickle'):
        rp.print('Data.pickle for ' + symbol + ' does not exist; return safely')
        return
    buy_vwap_df, sell_vwap_df = task_meta.get_params()

    try:
        input_manager.prepare_input_with_symbol(symbol, (buy_vwap_df, sell_vwap_df))
    except Exception as e:
        rp.print(symbol + ' exception: ' + repr(e))
        return
    input_all = input_manager.get_input(symbol, 'all')
    input_first = input_manager.get_input(symbol, 'first_half')
    input_second = input_manager.get_input(symbol, 'second_half')

    try:
        input_manager.prepare_param_set(symbol)
    except Exception as e:
        rp.print(repr(e))
        return

    output_path = input_manager.output_dir
    params_first = input_manager.get_all_param_dict_from_symbol(symbol, 'first_half')
    params_second = input_manager.get_all_param_dict_from_symbol(symbol, 'second_half')
    results_first = []
    results_second = []

    rp.print('Start looping the first half of {}'.format(symbol))
    for trigger in params_first:
        se_first = SignalEvaluate(input_first, [(input_first.signal_data, trigger)])
        result = se_first.evaluate()
        results_first.append(result)
    del se_first

    rp.print('Start looping the second half of {}'.format(symbol))
    for trigger in params_second:
        se_second = SignalEvaluate(input_second, [(input_second.signal_data, trigger)])
        result = se_second.evaluate()
        results_second.append(result)
    del se_second

    rp.print('Start running the best params of {}'.format(symbol))
    result_manager.set_results_for_symbol(symbol, results_first)
    best_param_for_second = result_manager.find_best_param(symbol, output_path, 'first')
    se = SignalEvaluate(input_second, [(input_second.signal_data, best_param_for_second)])
    se.evaluate(show='second')

    result_manager.set_results_for_symbol(symbol, results_second)
    best_param_for_first = result_manager.find_best_param(symbol, output_path, 'second')
    se = SignalEvaluate(input_first, [(input_first.signal_data, best_param_for_first)])
    se.evaluate(show='first')

    se = SignalEvaluate(input_all, [(input_first.signal_data, best_param_for_first),
                                    (input_second.signal_data, best_param_for_second)])
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
        # config.set_executor_instances(str(self.__max_tasks))
        config.set_executor_instances("50")
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
