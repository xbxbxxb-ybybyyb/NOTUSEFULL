import copy
import datetime as dt
import os
import gc
from typing import Dict, List

import numpy as np
import pandas as pd

from Utils_CV.ParamManager import ParamManager
from Utils_CV.SignalManager import SignalManager


class InputManager:
    def __init__(self, signal_csv_dir='./', bt_dir='./', output_dir='./results/', executor_str: str = 'SignalExecutorTesting',
                 cross_valid=False):
        self.__input_dict: Dict[str, 'Input'] = {}
        self.__signal_csv_dir = signal_csv_dir
        self.__bt_dir = bt_dir
        self.output_dir = output_dir
        self.__executor_str = executor_str
        self.mock_trade_para = {"maxTurnoverPerOrder": 1000000, "maxExposure": 4000000, "maxRatePerOrder": 0.2,
                                "openWithdrawSeconds": 2.5, "closeWithdrawSeconds": 3, "buyLevel": 1, "sellLevel": 1,
                                "buyDeviation": 0, "sellDeviation": -0.01, "MIN_ORDER_QTY": 10, 'maxLose': 9999,
                                'start_open_time': dt.time(9, 31, 15), 'last_open_time': dt.time(15, 0, 0),
                                'initQty': 0}
        self.__all_param_dict: Dict[str, List[Dict[str, float]]] = {}
        self.__cross_valid = cross_valid
        self.__symbols: List[str] = None
        self.__init_quantities: List[int] = None
        self.__optimal_shift: List[float] = None
        self.__open_triggers: List[float] = None
        self.__close_triggers: List[float] = None
        self.__param_reduction: bool = True
        self.__inputs: Dict[str, Dict[str, 'Input']] = {}

    def set_symbols(self, symbols: List[str]) -> None:
        self.__symbols = symbols

    def set_init_quantity(self, init_quantities: List[int]) -> None:
        self.__init_quantities = init_quantities
        if len(self.__symbols) != len(self.__init_quantities):
            raise Exception('The length of symbols does not match the length of init_quantities!')

    def set_optimal_shift(self, optimal_shift: List[int]) -> None:
        self.__optimal_shift = optimal_shift
        if len(self.__symbols) != len(self.__optimal_shift):
            raise Exception('The length of symbols does not match the length of optimal shift !')

    def get_optimal_shift(self, symbol):
        index = self.__symbols.index(symbol)
        return self.__optimal_shift[index]

    def get_output_path(self, symbol):
        return self.output_dir + symbol + '/'

    def set_triggers(self, open_triggers, close_triggers, param_reduction=True):
        open_triggers.sort()
        close_triggers.sort()
        self.__open_triggers = open_triggers
        self.__close_triggers = close_triggers
        self.__param_reduction = param_reduction

    def generate_trigger_dict(self, symbol, open_trigger, close_trigger):
        trigger_dict = {}
        trigger_dict['longTriggerRatio'] = open_trigger
        shortTriggerRatio = -open_trigger  + self.get_optimal_shift(symbol)
        if shortTriggerRatio >= open_trigger:
            shortTriggerRatio = - open_trigger
        trigger_dict['shortTriggerRatio'] = shortTriggerRatio
        trigger_dict['longCloseRatio'] = close_trigger
        trigger_dict['shortCloseRatio'] = -close_trigger
        trigger_dict['longRiskRatio'] = close_trigger - 0.2
        trigger_dict['shortRiskRatio'] = -close_trigger + 0.2
        return trigger_dict
        
    def clear_symbol(self, symbol):
        self.__all_param_dict.pop(symbol, None)
        self.__inputs.pop(symbol, None)
        gc.collect()

    def prepare_input_with_symbol(self, symbol: str):
        if symbol not in self.__inputs:
            init_qty = self.__load_init_qty(symbol)
            mock_trade_para = copy.deepcopy(self.mock_trade_para)
            mock_trade_para['initQty'] = init_qty
            output_file_dir = self.get_output_path(symbol)
            signal_manager = self.__load_signal_manager_without_market_data(symbol)
            signal_manager.load_stock_data_in_pickle()
            signal_data, signal_data_first, signal_data_second = self.__prepare_signals(signal_manager)
            order_capacity = signal_manager.get_order_capacity()
            input_all = Input(symbol, signal_data, signal_manager.get_tick(), signal_manager.get_transaction(),
                              signal_manager.get_tick_dict(), order_capacity, mock_trade_para, self.__executor_str, output_file_dir)
            input_first = Input(symbol, signal_data_first, signal_manager.get_tick(), signal_manager.get_transaction(),
                                signal_manager.get_tick_dict(), order_capacity, mock_trade_para, self.__executor_str, output_file_dir)
            input_second = Input(symbol, signal_data_second, signal_manager.get_tick(),
                                 signal_manager.get_transaction(),
                                 signal_manager.get_tick_dict(), order_capacity, mock_trade_para, self.__executor_str, output_file_dir)
            self.__inputs.update({symbol: {'all': input_all, 'first_half': input_first, 'second_half': input_second}})

    def prepare_param_set(self, symbol):
        self.__prepare_params(symbol)

    def get_input(self, symbol: str, key: str = 'all'):
        return self.__inputs[symbol][key]

    def __load_init_qty(self, symbol):
        index = self.__symbols.index(symbol)
        return self.__init_quantities[index]

    def __load_signal_manager_without_market_data(self, symbol):
        signal_manager = SignalManager(symbol, self.__signal_csv_dir, self.__bt_dir)
        return signal_manager

    def __prepare_params(self, symbol):
        if self.__param_reduction:
            signal_manager = self.__load_signal_manager_without_market_data(symbol)
            signal_data, _, _ = self.__prepare_signals(signal_manager)
            all_params = self.__my_param_reduction(symbol, signal_data)
            # MEMORY RELEASE
            del signal_manager
            # gc.collect()
        else:
            param_manager = ParamManager(self.__open_triggers, self.__close_triggers)
            all_params = param_manager.get_all_param_dicts()
        if not all_params:
            all_params = [{'longTriggerRatio': 999999, 'longCloseRatio': 0,
                           'longRiskRatio': -0.2, 'shortTriggerRatio': -999999,
                           'shortCloseRatio': 0, 'shortRiskRatio': 0.2}]
        self.__all_param_dict.update({symbol: all_params})

    def __my_param_reduction(self, symbol: str, signal_data: pd.DataFrame) -> List[Dict[str, float]]:
        all_param_dict = []
        ave_long = signal_data.ix[:, 1]
        ave_short = signal_data.ix[:, 2]
        max_trigger = np.percentile(ave_long, 99.999)
        min_trigger = np.percentile(ave_long, 95)
        min_close =  np.percentile(ave_short, 0.001)
        max_close =  np.percentile(ave_short, 5)
#        for trigger_ratio in self.__open_triggers:
#            for close_ratio in self.__close_triggers:
#                if trigger_ratio > max_trigger or trigger_ratio < min_trigger:
#                    continue
#                if close_ratio > max_close or close_ratio < min_close:
#                    continue
#                if -close_ratio >= trigger_ratio:
#                    continue
        for trigger_ratio in self.__open_triggers:
            if trigger_ratio > max_trigger:
                continue
            for close_ratio in self.__close_triggers:
                if close_ratio > 0.8 * trigger_ratio or close_ratio < -0.8 * trigger_ratio:
                    continue
                shortTrigger = - trigger_ratio + self.get_optimal_shift(symbol)
                if shortTrigger >= trigger_ratio:
                    shortTrigger = - trigger_ratio
                inner_dict = {'longTriggerRatio': trigger_ratio, 'longCloseRatio': close_ratio,
                              'longRiskRatio': close_ratio - 0.2, 'shortTriggerRatio': shortTrigger,
                              'shortCloseRatio': -close_ratio, 'shortRiskRatio': -close_ratio + 0.2}
                all_param_dict.append(inner_dict)

        if not all_param_dict:
            redefined_open_triggers = np.arange(min_trigger, max_trigger, 0.2)
            redefined_close_triggers = np.arange(min_close, max_close, 0.2)
            for trigger_ratio in redefined_open_triggers:
                for close_ratio in redefined_close_triggers:
                    if -close_ratio >= trigger_ratio:
                        continue
                    shortTrigger = - trigger_ratio + self.get_optimal_shift(symbol)
                    if shortTrigger >= trigger_ratio:
                        shortTrigger = - trigger_ratio
                    inner_dict = {'longTriggerRatio': trigger_ratio, 'longCloseRatio': close_ratio,
                                  'longRiskRatio': close_ratio - 0.2, 'shortTriggerRatio': shortTrigger,
                                  'shortCloseRatio': -close_ratio, 'shortRiskRatio': -close_ratio + 0.2}
                    all_param_dict.append(inner_dict)

        return all_param_dict

    # def __my_param_reduction(self, symbol: str, signal_data: pd.DataFrame) -> List[Dict[str, float]]:
    #     all_param_dict = []
    #     ave_long = signal_data.ix[:, 1]
    #     ave_short = signal_data.ix[:, 2]
    #     max_trigger = np.percentile(ave_long, 99.999)
    #     min_trigger = np.percentile(ave_long, 95)
    #     min_close =  np.percentile(ave_short, 0.001)
    #     max_close =  np.percentile(ave_short, 15)
    #     for trigger_ratio in self.__open_triggers:
    #         for close_ratio in self.__close_triggers:
    #             if trigger_ratio > max_trigger or trigger_ratio < min_trigger:
    #                 continue
    #             if close_ratio > max_close or close_ratio < min_close:
    #                 continue
    #             if -close_ratio >= trigger_ratio:
    #                 continue
    #             shortTrigger = - trigger_ratio + self.get_optimal_shift(symbol)
    #             if shortTrigger >= trigger_ratio:
    #                 shortTrigger = - trigger_ratio
    #             inner_dict = {'longTriggerRatio': trigger_ratio, 'longCloseRatio': close_ratio,
    #                           'longRiskRatio': close_ratio - 0.2, 'shortTriggerRatio': shortTrigger,
    #                           'shortCloseRatio': -close_ratio, 'shortRiskRatio': -close_ratio + 0.2}
    #             all_param_dict.append(inner_dict)
    #
    #     if not all_param_dict:
    #         # redefined_open_triggers = np.arange(min_trigger, max_trigger, 0.1)
    #         # redefined_close_triggers = np.arange(min_close, max_close, 0.1)
    #         # for trigger_ratio in redefined_open_triggers:
    #         #     for close_ratio in redefined_close_triggers:
    #         #         if -close_ratio >= trigger_ratio:
    #         #             continue
    #         #         shortTrigger = - trigger_ratio + self.get_optimal_shift(symbol)
    #         #         if shortTrigger >= trigger_ratio:
    #         #             shortTrigger = - trigger_ratio
    #         #         inner_dict = {'longTriggerRatio': trigger_ratio, 'longCloseRatio': close_ratio,
    #         #                       'longRiskRatio': close_ratio - 0.2, 'shortTriggerRatio': shortTrigger,
    #         #                       'shortCloseRatio': -close_ratio, 'shortRiskRatio': -close_ratio + 0.2}
    #         #         all_param_dict.append(inner_dict)
    #
    #         open_triggers = [0, 0.1, 0.2, 0.3, 0.4, 0.5]
    #         close_triggers = [-0.4, -0.3, -0.2, -0.1, 0]
    #         max_trigger = np.percentile(ave_long, 99.9999)
    #         max_close = np.percentile(ave_short, 20)
    #         min_trigger_open = max(round(min_trigger, 1) - 0.1, 0.6)
    #         max_trigger_open = min(3.0, round(max_trigger, 1))
    #         min_trigger_close = max(-2.9, round(min_close, 1))
    #         max_trigger_close = min(round(max_close, 1) + 0.1, -0.5)
    #         if round(max_close, 1) < min(close_triggers):
    #             close_triggers = []
    #         if round(min_trigger, 1) > max(open_triggers):
    #             open_triggers = []
    #         start = min_trigger_open
    #         while start <= max_trigger_open:
    #             if not start in open_triggers:
    #                 open_triggers.append(start)
    #             start += 0.1
    #
    #         start = min_trigger_close
    #         while start <= max_trigger_close:
    #             if not start in close_triggers:
    #                 close_triggers.append(start)
    #             start += 0.1
    #
    #         for trigger_ratio in open_triggers:
    #             for close_ratio in close_triggers:
    #                 if trigger_ratio > max_trigger or trigger_ratio < min_trigger:
    #                     continue
    #                 if close_ratio > max_close or close_ratio < min_close:
    #                     continue
    #                 if -close_ratio >= trigger_ratio:
    #                     continue
    #                 shortTrigger = - trigger_ratio + self.get_optimal_shift(symbol)
    #                 if shortTrigger >= trigger_ratio:
    #                     shortTrigger = - trigger_ratio
    #                 inner_dict = {'longTriggerRatio': trigger_ratio, 'longCloseRatio': close_ratio,
    #                               'longRiskRatio': close_ratio - 0.2, 'shortTriggerRatio': shortTrigger,
    #                               'shortCloseRatio': -close_ratio, 'shortRiskRatio': -close_ratio + 0.2}
    #                 all_param_dict.append(inner_dict)
    #
    #     return all_param_dict

    def __prepare_signals(self, signal_manager: 'SignalManager'):
        signals = signal_manager.get_signals()
        signals_first = signal_manager.get_signals_from_first_half()
        signals_second = signal_manager.get_signals_from_second_half()
        signal_data = signals[['Timestamp', 'ave_long', 'ave_short']]
        signal_data_first = signals_first[['Timestamp', 'ave_long', 'ave_short']]
        signal_data_second = signals_second[['Timestamp', 'ave_long', 'ave_short']]
        return signal_data, signal_data_first, signal_data_second

    def get_all_param_dict_from_symbol(self, symbol):
        return self.__all_param_dict[symbol]

    def generate_param_filename(self, symbol: str, suffix: str):
        return self.output_dir + symbol + '/selection_from_' + suffix + '.xlsx'

    def is_cross_validation(self):
        return self.__cross_valid

    def get_symbols(self):
        return self.__symbols


class Input:

    def __init__(self, symbol, signal_data, tick, transaction, tick_dict, json_param, mock_trade_para, executor_str,
                 output_path_dir):
        self.__symbol = symbol
        self.__signal_data = signal_data
        self.__tick = tick
        self.__transaction = transaction
        self.__tick_dict = tick_dict
        self.__json_param = json_param
        self.__mock_trade_para = mock_trade_para
        self.__executor_str = executor_str
        self.__output_path_dir = output_path_dir

    @property
    def symbol(self):
        return self.__symbol

    @property
    def signal_data(self):
        return self.__signal_data

    @signal_data.setter
    def signal_data(self, signal_data):
        self.__signal_data = signal_data

    @property
    def tick(self):
        return self.__tick

    @property
    def transaction(self):
        return self.__transaction

    @property
    def tick_dict(self):
        return self.__tick_dict
        
    @property
    def json_param(self):
        return self.__json_param

    @property
    def mock_trade_para(self):
        return self.__mock_trade_para

    @property
    def executor_str(self):
        return self.__executor_str

    @property
    def output_path_dir(self):
        return self.__output_path_dir
