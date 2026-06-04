import copy
import datetime as dt
from Utils_BT.SignalManager import SignalManager


class InputManager:
    def __init__(self, signal_csv_dir, bt_dir, param_dir, output_dir, executor_str, trigger_path):
        self.bt_dir = bt_dir
        self.signal_csv_dir = signal_csv_dir
        self.param_dir = param_dir
        self.output_dir = output_dir
        self.trigger_path = trigger_path

        self.__mock_trade_para = {
            "MAX_QUANTITY": 1000000,
            "MAX_AMOUNT": 8000000,
            "PRICE_LIMIT_MAX_AMOUNT": 3000000,
            "START_OPEN_TIME": dt.time(9, 30, 0),
            "LAST_OPEN_TIME": dt.time(14, 57, 0),
            "OPEN_WITHDRAW_SECONDS": 2.5,
            "TARGET_QUANTITY": 0,
            "TARGET_VALUE": 0
        }
        self.__executor_str = executor_str
        self.__symbols = None  # list[str]
        self.__target_quantities = None  # list[int]
        self.__target_values = None  # list[float]
        self.__start_date = None
        self.__end_date = None
        self.__open_long_aggr_qs = None  # list[float]
        self.__open_long_pass_qs = None  # list[float]
        self.__long_aggressive_trigger = None
        self.__long_passive_trigger = None
        self.__short_aggressive_trigger = None
        self.__short_passive_trigger = None

        self.__input_dict = {}
        self.__all_param_dict = {}
        self.__inputs = {}

    def set_symbols(self, symbols):
        """
        :param symbols: list[str]
        """
        self.__symbols = symbols

    def set_target_quantities(self, target_quantities):
        """
        :param target_quantities: list[int]
        """
        self.__target_quantities = target_quantities
        if len(self.__symbols) != len(self.__target_quantities):
            raise Exception('The length of symbols does not match the length of target_quantities!')

    def set_target_values(self, target_values):
        """
        :param target_values: list[float]
        """
        self.__target_values = target_values
        if len(self.__symbols) != len(self.__target_values):
            raise Exception('The length of symbols does not match the length of target_values!')

    def set_period(self, start_date, end_date):
        """
        :param start_date: str
        :param end_date: str
        """
        self.__start_date = int(start_date)
        self.__end_date = int(end_date)

    def get_symbols(self):
        """
        :return: list[str]
        """
        return self.__symbols

    def get_start_date(self):
        """
        :return: int
        """
        return self.__start_date

    def get_end_date(self):
        """
        :return: int
        """
        return self.__end_date

    def get_output_path(self, symbol):
        """
        :param symbol: str
        """
        return self.output_dir + symbol + '/'

    def get_input(self, symbol, key='all'):
        """
        :param symbol: str
        :param key: str
        :return: Input
        """
        return self.__inputs[symbol][key]

    def get_all_param_dict_from_symbol(self, symbol, key='all'):
        """
        :param symbol: str
        :param key: str
        :return: dict{str: list[dict{str: float}]}
        """
        return self.__all_param_dict[symbol][key]

    def generate_param_filename(self, symbol, suffix):
        """
        :param symbol: str
        :param suffix: str
        :return: str
        """
        return self.get_output_path(symbol) + 'selection_from_' + suffix + '.xlsx'

    def prepare_input_with_symbol(self, symbol, vwap_df):
        """
        :param symbol: str
        :param vwap_df: (pd.DataFrame, pd.DataFrame)
        """
        if symbol in self.__inputs:
            return

        target_qty = self.__load_target_qty(symbol)
        target_value = self.__load_target_value(symbol)

        mock_trade_para = copy.deepcopy(self.__mock_trade_para)
        mock_trade_para['TARGET_QUANTITY'] = target_qty
        mock_trade_para['TARGET_VALUE'] = target_value

        output_file_dir = self.get_output_path(symbol)

        signal_manager = self.__load_signal_manager_without_market_data(symbol)
        signal_manager.load_stock_data_in_pickle()
        signal_data = self.__prepare_signals(signal_manager)
        order_capacity = signal_manager.get_order_capacity()

        input_all = Input(symbol, signal_data, signal_manager.get_tick(), signal_manager.get_transaction(),
                          signal_manager.get_tick_dict(), order_capacity, mock_trade_para, self.__executor_str,
                          output_file_dir, vwap_df)
        self.__inputs.update({symbol: {'all': input_all}})

    def __load_target_qty(self, symbol):
        """
        :param symbol: str
        :return: int
        """
        index = self.__symbols.index(symbol)
        return self.__target_quantities[index]

    def __load_target_value(self, symbol):
        """
        :param symbol: str
        :return: float
        """
        index = self.__symbols.index(symbol)
        return self.__target_values[index]

    def __load_signal_manager_without_market_data(self, symbol):
        signal_manager = SignalManager(symbol, self.signal_csv_dir, self.bt_dir, self.param_dir)
        return signal_manager

    @staticmethod
    def __prepare_signals(signal_manager):
        """
        :param signal_manager: SignalManager
        :return: (pd.DataFrame, pd.DataFrame, pd.DataFrame)
        """
        signals = signal_manager.get_signals()
        signal_data = signals[['Timestamp', 'ave_long', 'ave_short']]
        return signal_data


class Input:
    __slots__ = ['__symbol', '__signal_data', '__tick', '__transaction', '__tick_dict', '__json_param',
                 '__mock_trade_para', '__executor_str', '__output_path_dir', '__vwap_df', '__signal_start_timestamp',
                 '__signal_end_timestamp']

    def __init__(self, symbol, signal_data, tick, transaction, tick_dict, json_param, mock_trade_para, executor_str,
                 output_path_dir, vwap_df):
        self.__symbol = symbol
        self.__signal_data = signal_data
        self.__tick = tick
        self.__transaction = transaction
        self.__tick_dict = tick_dict
        self.__json_param = json_param
        self.__mock_trade_para = mock_trade_para
        self.__executor_str = executor_str
        self.__output_path_dir = output_path_dir
        self.__vwap_df = vwap_df

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

    @property
    def vwap_df(self):
        return self.__vwap_df
