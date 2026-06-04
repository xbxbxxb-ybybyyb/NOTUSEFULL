import copy
import gc
import datetime as dt
from Utils_CV.SignalManager import SignalManager


class InputManager:
    def __init__(self, signal_csv_dir, bt_dir, param_dir, output_dir, executor_str):
        self.bt_dir = bt_dir
        self.signal_csv_dir = signal_csv_dir
        self.param_dir = param_dir
        self.output_dir = output_dir

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
        self.__param_reduction = None

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

    def set_quantiles(self, open_long_aggr_qs, open_long_pass_qs, open_short_aggr_qs, open_short_pass_qs, param_reduction=True, cross=True):
        """
        :param open_long_aggr_qs: list[float]
        :param open_long_pass_qs: list[float]
        :param param_reduction: bool
        """
        open_long_aggr_qs.sort()
        open_long_pass_qs.sort()
        open_short_aggr_qs.sort()
        open_short_pass_qs.sort()
        self.__open_long_aggr_qs = open_long_aggr_qs
        self.__open_long_pass_qs = open_long_pass_qs
        self.__open_short_aggr_qs = open_short_aggr_qs
        self.__open_short_pass_qs = open_short_pass_qs
        
        self.__param_reduction = param_reduction
        self.__is_cross = cross

    # def set_quantiles(self, open_long_aggr_qs, open_long_pass_qs, param_reduction=True):
        # open_long_aggr_qs.sort()
        # open_long_pass_qs.sort()
        # self.__open_long_aggr_qs = open_long_aggr_qs
        # self.__open_long_pass_qs = open_long_pass_qs
        # self.__param_reduction = param_reduction

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
        signal_data, signal_data_first, signal_data_second = self.__prepare_signals(signal_manager)
        order_capacity = signal_manager.get_order_capacity()

        input_all = Input(symbol, signal_data, signal_manager.get_tick(), signal_manager.get_transaction(),
                          signal_manager.get_tick_dict(), order_capacity, mock_trade_para, self.__executor_str,
                          output_file_dir, vwap_df)
        input_first = Input(symbol, signal_data_first, signal_manager.get_tick(), signal_manager.get_transaction(),
                            signal_manager.get_tick_dict(), order_capacity, mock_trade_para, self.__executor_str,
                            output_file_dir, vwap_df)
        input_second = Input(symbol, signal_data_second, signal_manager.get_tick(),
                             signal_manager.get_transaction(), signal_manager.get_tick_dict(), order_capacity,
                             mock_trade_para, self.__executor_str, output_file_dir, vwap_df)

        self.__inputs.update({symbol: {'all': input_all, 'first_half': input_first, 'second_half': input_second}})

    def prepare_param_set(self, symbol):
        self.__prepare_params(symbol)

    def __load_target_qty(self, symbol):
        index = self.__symbols.index(symbol)
        return self.__target_quantities[index]

    def __load_target_value(self, symbol):
        index = self.__symbols.index(symbol)
        return self.__target_values[index]

    def __load_signal_manager_without_market_data(self, symbol):
        signal_manager = SignalManager(symbol, self.signal_csv_dir, self.bt_dir, self.param_dir)
        return signal_manager

    def __prepare_params(self, symbol):
        if symbol not in self.__inputs:
            signal_manager = self.__load_signal_manager_without_market_data(symbol)
            signal_data, signal_data_first, signal_data_second = self.__prepare_signals(signal_manager)

            del signal_manager
            gc.collect()
        else:
            signal_data = self.__inputs[symbol]['all'].signal_data
            signal_data_first = self.__inputs[symbol]['first_half'].signal_data
            signal_data_second = self.__inputs[symbol]['second_half'].signal_data

        all_params_all = self.__prepare_full_params(signal_data)
        all_params_first = self.__prepare_full_params(signal_data_first)
        all_params_second = self.__prepare_full_params(signal_data_second)

        if not all_params_all:
            raise Exception(symbol + ": No params in ALL after filtration. It is safe to raise this exception.")
        else:
            self.__all_param_dict.setdefault(symbol, {}).update({'all': all_params_all})

        if not all_params_first:
            raise Exception(symbol + ": No params in FIRST after filtration. It is safe to raise this exception.")
        else:
            self.__all_param_dict.setdefault(symbol, {}).update({'first_half': all_params_first})

        if not all_params_second:
            raise Exception(symbol + ": No params in SECOND after filtration. It is safe to raise this exception.")
        else:
            self.__all_param_dict.setdefault(symbol, {}).update({'second_half': all_params_second})

    @staticmethod
    def __prepare_signals(signal_manager):
        """
        :param signal_manager: SignalManager
        :return: (pd.DataFrame, pd.DataFrame, pd.DataFrame)
        """
        signals = signal_manager.get_signals()
        signals_first = signal_manager.get_signals_from_first_half()
        signals_second = signal_manager.get_signals_from_second_half()
        signal_data = signals[['Timestamp', 'ave_long', 'ave_short']]
        signal_data_first = signals_first[['Timestamp', 'ave_long', 'ave_short']]
        signal_data_second = signals_second[['Timestamp', 'ave_long', 'ave_short']]
        return signal_data, signal_data_first, signal_data_second

    def __prepare_full_params(self, signal_data):
        """
        :param signal_data: pd.DataFrame
        :return: list[dict{str: float}]
        """
        long_aggrs = []
        long_passs = []
        short_aggrs = []
        short_passs = []
        for open_long_aggr_q in self.__open_long_aggr_qs:
            th = signal_data['ave_long'].quantile(open_long_aggr_q)
            long_aggrs.append((open_long_aggr_q, th))

        for open_long_pass_q in self.__open_long_pass_qs:
            th = signal_data['ave_long'].quantile(open_long_pass_q)
            long_passs.append((open_long_pass_q, th))
            
        for open_short_aggr_q in self.__open_short_aggr_qs:
            th = signal_data['ave_short'].quantile(open_short_aggr_q)
            short_aggrs.append((open_short_aggr_q, th))

        for open_short_pass_q in self.__open_short_pass_qs:
            th = signal_data['ave_short'].quantile(open_short_pass_q)
            short_passs.append((open_short_pass_q, th))
            
        if self.__param_reduction:
            all_params = []
            long_params = []
            short_params = []
            
            for aggr_q, aggr_th in long_aggrs:
                for pass_q, pass_th in long_passs:
                    if aggr_q <= pass_q:
                        continue
                    long_params.append([aggr_th, pass_th])   
                     
            for aggr_q, aggr_th in short_aggrs:
                for pass_q, pass_th in short_passs:
                    if aggr_q >= pass_q:
                        continue
                    short_params.append([aggr_th, pass_th])
            if self.__is_cross:                     
                for long_aggr_th, long_pass_th in long_params:
                    for short_aggr_th, short_pass_th in short_params:
                        inner_dict = self.__generate_trigger_dict(long_aggr_th, long_pass_th, short_aggr_th, short_pass_th)
                        all_params.append(inner_dict)
            else:
                for long_aggr_th, long_pass_th in long_params:
                    inner_dict = self.__generate_trigger_dict(long_aggr_th, long_pass_th, -long_aggr_th, -long_pass_th)
                    all_params.append(inner_dict)
                for short_aggr_th, short_pass_th in short_params:
                    inner_dict = self.__generate_trigger_dict(-short_aggr_th, -short_pass_th, short_aggr_th, short_pass_th)
                    all_params.append(inner_dict)
        else:
            all_params = []
            if self.__is_cross: 
                for long_aggr_q, long_aggr_th in long_aggrs:
                    for long_pass_q, long_pass_th in long_passs:
                        for short_aggr_q, short_aggr_th in short_aggrs:
                            for short_pass_q, short_pass_th in short_passs:
                                inner_dict = self.__generate_trigger_dict(long_aggr_th, long_pass_th, short_aggr_th, short_pass_th)
                                all_params.append(inner_dict)
            else:
                for long_aggr_q, long_aggr_th in long_aggrs:
                    for long_pass_q, long_pass_th in long_passs:
                        inner_dict = self.__generate_trigger_dict(long_aggr_th, long_pass_th, -long_aggr_th, -long_pass_th)
                        all_params.append(inner_dict)
                for short_aggr_q, short_aggr_th in short_aggrs:
                    for short_pass_q, short_pass_th in short_passs:
                        inner_dict = self.__generate_trigger_dict(-short_aggr_th, -short_pass_th, short_aggr_th, short_pass_th)
                        all_params.append(inner_dict)
        return all_params
        
        # long_aggrs = []
        # long_passs = []

        # for open_long_aggr_q in self.__open_long_aggr_qs:
            # th1 = signal_data['ave_long'].quantile(open_long_aggr_q)
            # th2 = signal_data['ave_short'].quantile(1 - open_long_aggr_q)
            # long_aggrs.append((open_long_aggr_q, th1, th2))

        # for open_long_pass_q in self.__open_long_pass_qs:
            # th1 = signal_data['ave_long'].quantile(open_long_pass_q)
            # th2 = signal_data['ave_short'].quantile(1 - open_long_pass_q)
            # long_passs.append((open_long_pass_q, th1, th2))

        # if self.__param_reduction:
            # all_params = []
            # for aggr_q, aggr_th, aggr_th2 in long_aggrs:
                # for pass_q, pass_th, pass_th2 in long_passs:
                    # if aggr_q <= pass_q:
                        # continue
                    # inner_dict = self.__generate_trigger_dict(aggr_th, pass_th, aggr_th2, pass_th2)
                    # all_params.append(inner_dict)
        # else:
            # all_params = []
            # for aggr_q, aggr_th, aggr_th2 in long_aggrs:
                # for pass_q, pass_th, pass_th2 in long_passs:
                    # inner_dict = self.__generate_trigger_dict(aggr_th, pass_th, aggr_th2, pass_th2)
                    # all_params.append(inner_dict)

        # return all_params

    @staticmethod
    def __generate_trigger_dict(open_long_aggr_th, open_long_pass_th, short_aggr_th, short_pass_th):
        """
        :param open_long_aggr_th: float
        :param open_long_pass_th: float
        :return: dict{str: float}
        """
        trigger_dict = {}
        trigger_dict['longAggressiveRatio'] = open_long_aggr_th
        trigger_dict['shortAggressiveRatio'] = short_aggr_th
        trigger_dict['longPassiveRatio'] = open_long_pass_th
        trigger_dict['shortPassiveRatio'] = short_pass_th
        return trigger_dict


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
