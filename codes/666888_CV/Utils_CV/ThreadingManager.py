import os
import json
# import multiprocessing
# import queue
import time
import numpy as np
from collections import deque
from typing import Deque, List, Dict

# import System.RemotePrint as rp
from ModelSystem.SignalEvaluate import SignalEvaluate
from Utils_CV.HelperFunctions import *
from Utils_CV.InputManager import *
from Utils_CV.ResultManager import ResultManager
from Utils_CV.TaskMeta import TaskMeta

# from QuantFramework import Job
# from QuantFramework import Configuration
from xquant.compute.sparkmr import Job
from xquant.compute.sparkmr import Configuration
from xquant.compute.sparkmr import remote_print

# from QuantFramework import HDFSFileHandler
# from QuantFramework import remote_print
# import psutil

from xquant.pyfile import Pyfile


def func_dump_symbol_params(context, task_meta):
    if len(task_meta.get_symbols()) == 0:
        return
    symbol = task_meta.get_symbols()[0]
    input_manager = task_meta.get_input_manager()
    try:
    # if True:
        input_manager.prepare_param_set(symbol)
    except Exception as e:
        import traceback
        remote_print(e, traceback.print_exc())
        return
    all_param_dict = input_manager.get_all_param_dict_from_symbol(symbol)
    py = Pyfile()
    with py.open(input_manager.output_dir + 'TEMP/' + symbol + '.json', 'wb') as f:
        json.dump(all_param_dict, f)
        

def func_run_seperate_params(context, task_meta):
    # process = psutil.Process(os.getpid())
    # remote_print('Used Memory:',process.memory_info().rss / 1024 / 1024 / 1024,'GB')
    py = Pyfile()
    symbols = task_meta.get_symbols()
    for i in range(len(symbols)):
        symbol = symbols[i]
        params = task_meta.get_params()[i]
        sid = task_meta.get_symbol_id()[i]
        input_manager = task_meta.get_input_manager()
        try:
            input_manager.prepare_input_with_symbol(symbol)
        except Exception as e:
            import traceback
            remote_print(traceback.print_exc())
            continue
        input_all = input_manager.get_input(symbol, 'all')
        input_first = input_manager.get_input(symbol, 'first_half')
        input_second = input_manager.get_input(symbol, 'second_half')
        filename = input_manager.output_dir + 'TEMP/' + symbol + '_' + str(sid) + '.json'
        if input_manager.is_cross_validation():
            results_first = []
            results_second = []
            for trigger_dict in params:
                se_first = SignalEvaluate(input_first, [(input_first.signal_data, trigger_dict)])
                result_first = se_first.evaluate()
                results_first.append(result_first)
                se_second = SignalEvaluate(input_second, [(input_second.signal_data, trigger_dict)])
                result_second = se_second.evaluate()
                results_second.append(result_second)
            with py.open(filename, 'wb') as f:
                json.dump([results_first, results_second], f)
            del se_first
            del se_second
        else:
            results = []
            for trigger_dict in params:
                se = SignalEvaluate(input_all, [(input_all.signal_data, trigger_dict)])
                result = se.evaluate()
                results.append(result)
            with py.open(filename, 'wb') as f:
                json.dump([results], f)
            del se
        del input_all
        del input_first
        del input_second
        input_manager.clear_symbol(symbol)
        # process = psutil.Process(os.getpid())
        # remote_print('Used Memory:',process.memory_info().rss / 1024 / 1024 / 1024,'GB finished ' + str(i + 1) + ' Symbol ' + symbol)
            

# def func_run_output_results(context, task_meta):
    # symbol = task_meta.get_symbols()[0]
    # input_manager = task_meta.get_input_manager()
    # result_manager = task_meta.get_result_manager()
    # input_manager.prepare_input_with_symbol(symbol)
    # input_all = input_manager.get_input(symbol, 'all')
    # input_first = input_manager.get_input(symbol, 'first_half')
    # input_second = input_manager.get_input(symbol, 'second_half')
    # result_list = task_meta.get_params()
    # if input_manager.is_cross_validation():
        # results_first = result_list[0]
        # results_second = result_list[1]
        # result_manager.set_results_for_symbol(symbol, results_first)
        # trigger_dict_first = result_manager.find_best_param(symbol, input_manager.output_dir, 'first')
        # best_open_trigger_first = trigger_dict_first['longTriggerRatio']
        # best_close_trigger_first = trigger_dict_first['longCloseRatio']
        # best_trigger_dict_first = InputManager.generate_trigger_dict(best_open_trigger_first, best_close_trigger_first)
        # result_manager.set_results_for_symbol(symbol, results_second)
        # trigger_dict_second = result_manager.find_best_param(symbol, input_manager.output_dir, 'second')
        # best_open_trigger_second = trigger_dict_second['longTriggerRatio']
        # best_close_trigger_second = trigger_dict_second['longCloseRatio']
        # best_trigger_dict_second = InputManager.generate_trigger_dict(best_open_trigger_second, best_close_trigger_second)
        # se = SignalEvaluate(input_second, [(input_second.signal_data, best_trigger_dict_first)])
        # se.evaluate(show='second')
        # se = SignalEvaluate(input_first, [(input_first.signal_data, best_trigger_dict_second)])
        # se.evaluate(show='first')
        # se = SignalEvaluate(input_all, [(input_first.signal_data, best_trigger_dict_second), (input_second.signal_data, best_trigger_dict_first)])
        # se.evaluate(show='merged')
        # best_trigger_to_dump = best_trigger_dict_second
    # else:
        # result_manager.set_results_for_symbol(symbol, results)
        # trigger_dict = result_manager.find_best_param(symbol, input_manager.output_dir, 'all')
        # best_open_trigger = trigger_dict['longTriggerRatio']
        # best_close_trigger = trigger_dict['longCloseRatio']
        # best_trigger_dict = InputManager.generate_trigger_dict(best_open_trigger, best_close_trigger)
        # se = SignalEvaluate(input_all, [(input_all.signal_data, best_trigger_dict)])
        # se.evaluate(show='all')
        # best_trigger_to_dump = best_trigger_dict
    # # DUMP TRIGGER JSON
    # py = Pyfile()
    # json_path = input_all.output_path_dir + 'triggerRatio.json'
    # if py.exists(json_path):
        # py.delete(json_path)
    # with py.open(json_path, 'wb') as f:
        # json.dump(best_trigger_to_dump, f)
    # rp.print(symbol + ' finished.')


def func_run_output_results(context, task_meta):
    symbol = task_meta.get_symbols()[0]
    input_manager = task_meta.get_input_manager()
    result_manager = task_meta.get_result_manager()
    try:
        input_manager.prepare_input_with_symbol(symbol)
    except Exception as e:
        # import traceback
        # remote_print(traceback.print_exc())
        return
    input_all = input_manager.get_input(symbol, 'all')
    input_first = input_manager.get_input(symbol, 'first_half')
    input_second = input_manager.get_input(symbol, 'second_half')
    best_trigger = task_meta.get_params()
    if input_manager.is_cross_validation():
        best_trigger_dict_first = best_trigger[0]
        best_trigger_dict_second = best_trigger[1]
        se = SignalEvaluate(input_second, [(input_second.signal_data, best_trigger_dict_first)])
        se.evaluate(show='second')
        se = SignalEvaluate(input_first, [(input_first.signal_data, best_trigger_dict_second)])
        se.evaluate(show='first')
        se = SignalEvaluate(input_all, [(input_first.signal_data, best_trigger_dict_second), (input_second.signal_data, best_trigger_dict_first)])
        se.evaluate(show='merged')
        best_trigger_to_dump = best_trigger_dict_second
    else:
        best_trigger_dict = best_trigger[0]
        se = SignalEvaluate(input_all, [(input_all.signal_data, best_trigger_dict)])
        se.evaluate(show='all')
        best_trigger_to_dump = best_trigger_dict
    # DUMP TRIGGER JSON
    py = Pyfile()
    json_path = input_all.output_path_dir + 'triggerRatio.json'
    if py.exists(json_path):
        py.delete(json_path)
    with py.open(json_path, 'wb') as f:
        json.dump(best_trigger_to_dump, f)
    # rp.print(symbol + ' finished.')


class ThreadingManager:
    __slots__ = ['__input_manager', '__result_manager', '__result_keys', '__max_tasks',
                 '__symbols', '__results', '__exceeds_max_tasks', '__symbol_file_id']

    def __init__(self, input_manager: 'InputManager', result_manager: 'ResultManager', max_tasks: int = 200):
        self.__input_manager = input_manager
        self.__result_manager = result_manager
        self.__result_keys = self.__result_manager.get_keys()
        self.__max_tasks: int = max_tasks
        self.__symbols: List[str] = input_manager.get_symbols()
        self.__results: List = []
        self.__exceeds_max_tasks: bool = True if len(self.__symbols) >= max_tasks else False
        self.__symbol_file_id = None
        
    def start_dump_symbol_params(self):
        task_metas = []
        for symbol in self.__symbols:
            task_metas.append(TaskMeta([symbol], self.__input_manager, self.__result_manager))
        if len(task_metas) < self.__max_tasks:
            res = self.__max_tasks - len(task_metas)
            for i in range(res):
                task_metas.append(TaskMeta([], self.__input_manager, self.__result_manager))

        config = Configuration()
        config.set_app_name(self.__get_app_name())
        config.set_dst_dir(self.__input_manager.output_dir + 'TEMP/')
        config.set_env_dir(self.__get_env_dir())
        config.set_executor_instances(str(min(self.__max_tasks, 600)))
        # config.set_executor_instances(str(min(self.__max_tasks, 300)))
        config.set_executor_memory('4G')
        job = Job(config, 'Overwrite')
        job.add_tasks(task_metas)
        job.set_func(func_dump_symbol_params)
        job.start()

    def pre_process_params(self):
        task_metas = []
        params_path = self.__get_temp_dir()
        py = Pyfile()
        files = py.listdir(params_path)
        total_list = []
        symbol_file_id = {}
        for file in files:
            symbol = file[0: 9]
            symbol_file_id.update({symbol: -1})
            with py.open(params_path + file, 'rb') as f:
                data = f.read()
                data = json.loads(data)
            for trigger_ratio in data:
                total_list.append((symbol, trigger_ratio))
        splitted_list = np.array_split(total_list, self.__max_tasks)
        for core_num_list in splitted_list:
            prepare_dict: Dict[str, List[Dict[str, float]]] = {}
            for symbol_param in core_num_list:
                symbol = symbol_param[0]
                param = symbol_param[1]
                if symbol not in prepare_dict.keys():
                    prepare_dict.update({symbol: []})
                    prepare_dict[symbol].append(param)
                    symbol_file_id[symbol] += 1
                else:
                    prepare_dict[symbol].append(param)
            symbols = []
            params = []
            ids = []
            for symbol in prepare_dict.keys():
                symbols.append(symbol)
                params.append(prepare_dict[symbol])
                ids.append(symbol_file_id[symbol])
            task_meta = TaskMeta(symbols, self.__input_manager, self.__result_manager, params, ids)
            task_metas.append(task_meta)
        self.__symbol_file_id = symbol_file_id
        return task_metas
        
    def start_running_seperate_params(self):
        task_metas = self.pre_process_params()

        config = Configuration()
        config.set_app_name(self.__get_app_name())
        config.set_dst_dir(self.__input_manager.output_dir + 'TEMP/')
        config.set_env_dir(self.__get_env_dir())
        config.set_executor_instances(str(min(self.__max_tasks, 600)))
        # config.set_executor_instances(str(min(self.__max_tasks, 300)))
        config.set_executor_memory('4G')
        job = Job(config, 'OverWrite')
        job.add_tasks(task_metas)
        job.set_func(func_run_seperate_params)
        job.start()
        py = Pyfile()
        with py.open(self.__get_temp_dir() + 'valid_symbol_ids.json', 'wb') as f:
            json.dump(self.__symbol_file_id, f)
        
    def merge_results(self):
        py = Pyfile()
        if self.__symbol_file_id is None:
            with py.open(self.__get_temp_dir() + 'valid_symbol_ids.json', 'rb') as f:
                data = f.read()
                self.__symbol_file_id = json.loads(data)
        merged = {}
        params_path = self.__get_temp_dir()
        output_path = self.__get_output_dir()
        if self.__input_manager.is_cross_validation():
            for symbol in self.__symbol_file_id.keys():
                length = self.__symbol_file_id[symbol]
                results_first = []
                results_second = []
                for i in range(length + 1):
                    with py.open(params_path + symbol + '_' + str(i) + '.json', 'rb') as f:
                        data = f.read()
                        data = json.loads(data)
                    results_first += data[0]
                    results_second += data[1]
                # merged.update({symbol: [results_first, results_second]})
                self.__result_manager.set_results_for_symbol(symbol, results_first)
                trigger_dict_first = self.__result_manager.find_best_param(symbol, output_path, 'first')
                best_open_trigger_first = trigger_dict_first['longTriggerRatio']
                best_close_trigger_first = trigger_dict_first['longCloseRatio']
                best_trigger_dict_first = InputManager.generate_trigger_dict(best_open_trigger_first, best_close_trigger_first)
                self.__result_manager.set_results_for_symbol(symbol, results_second)
                trigger_dict_second = self.__result_manager.find_best_param(symbol, output_path, 'second')
                best_open_trigger_second = trigger_dict_second['longTriggerRatio']
                best_close_trigger_second = trigger_dict_second['longCloseRatio']
                best_trigger_dict_second = InputManager.generate_trigger_dict(best_open_trigger_second, best_close_trigger_second)
                merged.update({symbol: [best_trigger_dict_first, best_trigger_dict_second]})
                # best_trigger_to_dump = best_trigger_dict_second
                # json_path = output_path + symbol + '/triggerRatio.json'
                # if py.exists(json_path):
                    # py.delete(json_path)
                # with py.open(json_path, 'wb') as f:
                    # json.dump(best_trigger_to_dump, f)
        else:
            for symbol in self.__symbol_file_id.keys():
                length = self.__symbol_file_id[symbol]
                results = []
                for i in range(length + 1):
                    with py.open(params_path + symbol + '_' + str(i) + '.json', 'rb') as f:
                        data = f.read()
                        data = json.loads(data)
                    results += data[0]
                # merged.update({symbol: [results]})
                self.__result_manager.set_results_for_symbol(symbol, results)
                trigger_dict = self.__result_manager.find_best_param(symbol, output_path, 'all')
                best_open_trigger = trigger_dict['longTriggerRatio']
                best_close_trigger = trigger_dict['longCloseRatio']
                best_trigger_dict = InputManager.generate_trigger_dict(best_open_trigger, best_close_trigger)
                merged.update({symbol: [best_trigger_dict]})
        self.__result_manager.clear_all()
        return merged
        
    def start_output_final_result(self):
        s_time = time.perf_counter()
        merged = self.merge_results()
        e_time = time.perf_counter()
        print('merging time: ' + str(round((e_time - s_time) / 60, 2)) + 'min')
        
        task_metas = []
        for symbol in merged.keys():
            task_metas.append(TaskMeta([symbol], self.__input_manager, self.__result_manager, merged[symbol]))
        
        config = Configuration()
        config.set_app_name(self.__get_app_name())
        config.set_dst_dir(self.__input_manager.output_dir)
        config.set_env_dir(self.__get_env_dir())
        config.set_executor_instances(str(min(self.__max_tasks, 600)))
        # config.set_executor_instances(str(min(self.__max_tasks, 300)))
        config.set_executor_memory('4G')
        job = Job(config, 'Increment')
        job.add_tasks(task_metas)
        job.set_func(func_run_output_results)
        job.start()
        

    def start(self):
        print('Programme is running...')
        start = time.perf_counter()
        self.start_dump_symbol_params()
        self.start_running_seperate_params()
        self.start_output_final_result()
        end = time.perf_counter()
        print('running time: ' + str(round((end - start) / 60, 2)) + 'min')
        # py.delete(self.__get_temp_dir(), recursive=True)

    def __generate_task_metas(self) -> List['TaskMeta']:
        task_metas = []
        symbols = split_assign_symbols(self.__symbols, self.__max_tasks)
        for symbol_list in symbols:
            task_meta = TaskMeta(symbol_list, self.__input_manager, self.__result_manager)
            task_metas.append(task_meta)
        return task_metas
        
    def __get_app_name(self):
        path_name = self.__get_env_dir()
        path_name.split('/')
        index = path_name.index('repository')
        wid = path_name[index + 1]
        return 'BackTest_' + wid
        
    def __get_env_dir(self):
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    def __get_temp_dir(self):
        params_path = self.__input_manager.output_dir
        while params_path[0] == '/':
            params_path = params_path[1: ]
        index = params_path.index('/')
        params_path = params_path[index + 1: ]
        params_path += 'TEMP/'
        return params_path
        
    def __get_output_dir(self):
        params_path = self.__input_manager.output_dir
        while params_path[0] == '/':
            params_path = params_path[1: ]
        index = params_path.index('/')
        params_path = params_path[index + 1: ]
        return params_path
