import copy
import datetime as dt
from typing import Dict, List
from DataIO.DataManager import DataManager
from Utils_BT.SignalManager import SignalManager


class InputManager:
    def __init__(self, start_date: str, end_date: str, signal_library: str,
                 bt_dir: str="", output_dir: str="", executor_str: str = 'SignalExecutorTesting', data_config=None,
                 use_l2p: bool=False, trigger_json_dir: str='', cross_valid: bool=False):
        self.start_date = start_date
        self.end_date = end_date
        self.signal_library = signal_library
        self.bt_dir = bt_dir
        self.output_dir = output_dir
        self.executor_str = executor_str
        self.data_config = data_config
        self.use_l2p = use_l2p
        self.trigger_json_dir = trigger_json_dir
        self.mock_trade_para = {"maxTurnoverPerOrder": 1000000, "maxExposure": 4000000, "maxRatePerOrder": 0.2,
                                "openWithdrawSeconds": 2.5, "closeWithdrawSeconds": 3, "buyLevel": 1, "sellLevel": 1,
                                "buyDeviation": 0, "sellDeviation": -0.01, "MIN_ORDER_QTY": 10, 'maxLoss': 9999,
                                'start_open_time': dt.time(9, 31, 15), 'last_open_time': dt.time(15, 0, 0),
                                'initQty': 0}
        self.__all_param_dict: Dict[str, List[Dict[str, float]]] = dict()
        self.__cross_valid = cross_valid
        self.__symbols: List[str] = None
        self.__init_quantities: List[int] = None
        self.__optimal_shift: List[float] = None
        self.__open_triggers: List[float] = None
        self.__close_triggers: List[float] = None
        self.__param_reduction: bool = True
        self.__inputs: Dict[str, Dict[str, 'Input']] = dict()

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
        trigger_dict = dict()
        trigger_dict['longTriggerRatio'] = open_trigger
        short_trigger_ratio = - open_trigger + self.get_optimal_shift(symbol)
        if short_trigger_ratio >= open_trigger:
            short_trigger_ratio = - open_trigger
        trigger_dict['shortTriggerRatio'] = short_trigger_ratio
        trigger_dict['longCloseRatio'] = close_trigger
        trigger_dict['shortCloseRatio'] = -close_trigger
        trigger_dict['longRiskRatio'] = close_trigger - 0.2
        trigger_dict['shortRiskRatio'] = -close_trigger + 0.2
        return trigger_dict

    def prepare_input_with_symbol(self, symbol: str):
        if symbol not in self.__inputs:
            init_qty = self.__load_init_qty(symbol)
            mock_trade_para = copy.deepcopy(self.mock_trade_para)
            mock_trade_para['initQty'] = init_qty
            output_file_dir = self.get_output_path(symbol)

            data_manager = DataManager(symbol, self.start_date, self.end_date, self.data_config)
            data_manager.prepare_data_with_freq()
            signal_manager = self.__load_signal_manager(symbol)
            signal_data = self.__prepare_signals(signal_manager, data_manager.get_target_timestamp_dict())
            order_capacity = signal_manager.get_order_capacity()

            input_all = Input(symbol, signal_data, data_manager.get_tick(), data_manager.get_transaction(),
                              data_manager.get_tick_dict(), data_manager.get_freq_tick_dict(),
                              order_capacity, mock_trade_para, self.executor_str,
                              output_file_dir, self.use_l2p)
            self.__inputs.update({symbol: {'all': input_all}})

    def get_input(self, symbol: str, key: str = 'all'):
        return self.__inputs[symbol][key]

    def __load_init_qty(self, symbol):
        index = self.__symbols.index(symbol)
        return self.__init_quantities[index]

    def __load_signal_manager(self, symbol):
        signal_manager = SignalManager(symbol, self.start_date, self.end_date, self.signal_library, self.bt_dir)
        return signal_manager

    def __prepare_signals(self, signal_manager: 'SignalManager', target_timestamp_dict: Dict):
        signals = signal_manager.get_signals()
        signals["TargetTimestamp"] = [target_timestamp_dict.get(i) for i in signals["Timestamp"].tolist()]
        signal_data = signals[['Timestamp', 'ave_long', 'ave_short', "TargetTimestamp"]]
        return signal_data

    def get_all_param_dict_from_symbol(self, symbol):
        return self.__all_param_dict[symbol]

    def generate_param_filename(self, symbol: str, suffix: str):
        return self.get_output_path(symbol) + 'selection_from_' + suffix + '.xlsx'

    def is_cross_validation(self):
        return self.__cross_valid

    def get_symbols(self):
        return self.__symbols


class Input:

    def __init__(self, symbol, signal_data, tick, transaction, tick_dict, freq_tick_dict, json_param, mock_trade_para, executor_str,
                 output_path_dir, use_l2p=False):
        self.__symbol = symbol
        self.__signal_data = signal_data
        self.__tick = tick
        self.__transaction = transaction
        self.__tick_dict = tick_dict
        self.__freq_tick_dict = freq_tick_dict
        self.__json_param = json_param
        self.__mock_trade_para = mock_trade_para
        self.__executor_str = executor_str
        self.__output_path_dir = output_path_dir
        self.__use_l2p = use_l2p

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
    def freq_tick_dict(self):
        return self.__freq_tick_dict
        
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

    @property
    def use_l2p(self):
        return self.__use_l2p
