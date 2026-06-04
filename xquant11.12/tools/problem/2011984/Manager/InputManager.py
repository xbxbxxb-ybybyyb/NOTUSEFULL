"""InputManager——update @2022.4.13"""

import datetime as dt
from DataAPI.DataView import file_exist, load_pickle_file, load_json_file
from DataAPI.GetXQuantData import getXQuantTickData2, getXQuantTransactionData2
from DataAPI.TradingDay import trading_day
from Manager.SignalManager import SignalManager
from Manager.ParamManager import ParamManager
from Manager.UtilsModel.SimpleDataConverter import SimpleDataConverter
from Manager.Data1S.DataManager import DataManager
from xquant.factordata import FactorData


class InputManager:
    def __init__(self, code, st_date, ed_date, executor_str, dir_path, overwrite_params, bt_type,
                 cv_triggers_list=None, mock_lib=None, freq='3s', trigger_lib=None):
        self.code = code
        self.st_date = st_date
        self.ed_date = ed_date
        self.valid_dates = []
        self.executor_str = executor_str
        self.trigger_lib = trigger_lib
        self.tick_data = None
        self.transaction_data = None
        self.tick_dict = None
        self.tick_dict_freq = None
        self.pre_close_dict = None
        self.signal_data = None
        self.signal_data_first = None  # 前一半的signal data（cv_cross用到）
        self.signal_data_second = None  # 后一半的signal data（cv_cross用到）
        self.params_dict = dict()
        self.overwrite_params = overwrite_params
        self.type = bt_type  # sp, bt, cv, cv_cross
        self.cv_triggers_list = cv_triggers_list  # 阈值list（cv和cv_cross用到）
        self.mock_lib = mock_lib
        self.freq = freq
        self.__is_combine_data = False
        self.__is_combine_params = False
        if bt_type == 'sp':
            self.__is_combine_data = True
            self.__is_combine_params = True

        self.__signal_lib = dir_path['signal_lib']
        self.origin_data_list = dir_path['origin_data_list']
        self.param_dir = dir_path['param_dir']
        self.output_dir = dir_path['output_dir']
        self.output_path = '{}/{}'.format(self.output_dir, self.code)

        self.__target_timestamp_dict = {}

    def load_origin_data(self, dfs):
        if self.freq == '3s':
            self.load_origin_data_3s(dfs=dfs)
        elif self.freq == '3s_l2p':
            if self.code.startswith('1'):
                self.load_origin_data_3s(dfs=dfs)
            else:
                self.load_origin_data_3s_l2p(dfs=dfs)
        elif self.freq == '1s':
            if self.code.startswith('1'):
                self.load_origin_data_cb_1s()  # 转债
            else:
                self.load_origin_data_1s(dfs=dfs)  # 股票

    def load_origin_data_3s(self, dfs):
        if self.__is_combine_data or self.code.startswith('1'):  # 转债
            valid_dates, tick_data, transaction_data = [], [], []
            for origin_data_dir in self.origin_data_list:
                if file_exist(f'{origin_data_dir}/{self.code}/Dates.pickle', dfs=dfs):
                    valid_dates_sub = load_pickle_file(f'{origin_data_dir}/{self.code}/Dates.pickle', dfs=dfs)
                    tick_data_sub, transaction_data_sub = load_pickle_file(f'{origin_data_dir}/{self.code}/Data.pickle', dfs=dfs)
                    valid_dates.extend(valid_dates_sub)
                    tick_data.extend(tick_data_sub)
                    transaction_data.extend(transaction_data_sub)
                else:
                    print(f'No Data File: {origin_data_dir}/{self.code}/Dates.pickle')
        else:
            start_time = dt.datetime.strptime(self.st_date, "%Y%m%d")
            end_time = dt.datetime.strptime(self.ed_date, "%Y%m%d")
            tick_data, valid_dates = getXQuantTickData2(self.code, start_time, end_time, timeMode=3, tradingPhaseCode=[], dfs=dfs)
            transaction_data, _ = getXQuantTransactionData2(self.code, start_time, end_time, True, True, timeMode=3, dfs=dfs)
        self.valid_dates = sorted(list(map(str, valid_dates)))
        self.tick_data = tick_data
        self.transaction_data = transaction_data
        self.tick_dict = SimpleDataConverter(tick_data).get_data_dict()

    def load_origin_data_3s_l2p(self, dfs):
        from DataAPI.GetXQuantDataL2P import getL2PTickData2, getXQuantTransactionData2

        start_time = dt.datetime.strptime(self.st_date, "%Y%m%d")
        end_time = dt.datetime.strptime(self.ed_date, "%Y%m%d")
        tick_data, valid_dates = getL2PTickData2(self.code, start_time, end_time, hbaseLibrary='Channel036STickDataLib')
        transaction_data, _ = getXQuantTransactionData2(self.code, start_time, end_time, True, True, timeMode=3, dfs=dfs)
        self.valid_dates = sorted(list(map(str, valid_dates)))
        self.tick_data = tick_data
        self.transaction_data = transaction_data
        self.tick_dict = SimpleDataConverter(tick_data).get_data_dict()

    def load_origin_data_1s(self, dfs):
        data_manager = DataManager(self.code, self.st_date, self.ed_date)
        data_manager.prepare_data_with_freq()
        self.tick_data = data_manager.get_tick()
        self.transaction_data = data_manager.get_transaction()
        self.tick_dict = data_manager.get_tick_dict()
        self.tick_dict_freq = data_manager.get_freq_tick_dict()
        self.pre_close_dict = data_manager.get_pre_close_dict()
        self.valid_dates = list(sorted(self.pre_close_dict.keys()))
        self.__target_timestamp_dict = data_manager.get_target_timestamp_dict()

    def load_origin_data_cb_1s(self):
        valid_dates, tick_data, transaction_data = [], [], []
        for date in trading_day(int(self.st_date), int(self.ed_date)):
            tick = self.load_tick(date)
            trans = self.load_trans(date)

            if tick is not None and trans is not None:
                tick_data.append(tick)
                transaction_data.append(trans)
                valid_dates.append(date)
        self.valid_dates = sorted(list(map(str, valid_dates)))
        self.tick_data = tick_data
        self.transaction_data = transaction_data
        self.tick_dict = SimpleDataConverter(tick_data).get_data_dict()

    def load_tick(self, date):
        hbase_columns1 = ["Code", "Timestamp", "Date", "Time", "PreviousClose", "OpenPrice", "HighPrice", "LowPrice",
                          "MaxPrice", "MinPrice", "LastPrice", "Volume", "Amount", "TotalVolume", "TotalAmount",
                          "BidPrice", "AskPrice", "BidVolume", "AskVolume", "IsMock"]
        hbase_columns2 = list(map(lambda x: f"T_{x}", hbase_columns1))
        map_ = {
            "Timestamp": "TimeStamp",
            "PreviousClose": "PreClose",
            "OpenPrice": "Open",
            "HighPrice": "High",
            "LowPrice": "Low",
            "MaxPrice": "MaxP",
            "MinPrice": "MinP",
            "LastPrice": "Price",
            "Amount": "Turover",
            "TotalVolume": "AccVolume",
            "TotalAmount": "AccTurover",
        }

        fd = FactorData()
        try:
            data = fd.get_factor_value("Channel1STickDataLib", self.code, str(date), hbase_columns2)
        except:
            return

        data.columns = [x[2:] for x in data.columns]
        data = data.rename(columns=map_)
        data = data.astype({"Date": int, "Time": int})
        data = data[data["IsMock"].astype(int) == 0]
        bid_price = data["BidPrice"]
        ask_price = data["AskPrice"]
        bid_vol = data["BidVolume"]
        ask_vol = data["AskVolume"]
        for i in range(10):
            data[f"BidP{i + 1}"] = [x[i] for x in bid_price]
            data[f"AskP{i + 1}"] = [x[i] for x in ask_price]
            data[f"BidV{i + 1}"] = [x[i] for x in bid_vol]
            data[f"AskV{i + 1}"] = [x[i] for x in ask_vol]
        data = data.drop(columns=["BidPrice", "AskPrice", "BidVolume", "AskVolume"])
        if data.empty:
            return
        data = data[data['TimeStamp'] % 3 == 0]  # TODO
        data = data.to_dict("list")
        for c in ['BidP1', 'AskP1', 'BidV1', 'AskV1', 'BidP2', 'AskP2', 'BidV2', 'AskV2', 'BidP3', 'AskP3', 'BidV3', 'AskV3',
                  'BidP4', 'AskP4', 'BidV4', 'AskV4', 'BidP5', 'AskP5', 'BidV5', 'AskV5', 'BidP6', 'AskP6', 'BidV6', 'AskV6',
                  'BidP7', 'AskP7', 'BidV7', 'AskV7', 'BidP8', 'AskP8', 'BidV8', 'AskV8', 'BidP9', 'AskP9', 'BidV9', 'AskV9',
                  'BidP10', 'AskP10', 'BidV10', 'AskV10']:
            data[c] = [round(x, 3) for x in data[c]]

        return data

    def load_trans(self, date):
        hbase_columns1 = [
            "Date", "Time", "BidOrder", "AskOrder", "TradeType", "BSFlag", "Price", "Volume", "Timestamp"
        ]
        hbase_columns2 = list(map(lambda x: f"TR_{x}", hbase_columns1))
        map_ = {
            "Timestamp": "TimeStamp",
        }

        fd = FactorData()
        try:
            data = fd.get_factor_value("ZeusDataLib", self.code, str(date), hbase_columns2)
        except:
            return

        data.columns = [x[3:] for x in data.columns]
        data = data.rename(columns=map_)
        data["Code"] = self.code
        data = data.astype({"Date": int, "Time": int})

        data = data.loc[data["TradeType"] == 0, :]
        data.loc[data["BSFlag"] == 2, "BSFlag"] = -1

        if data.empty:
            return
        data = data.to_dict("list")

        return data

    def load_signal_data(self, signal_col_names=None):
        vt_name = self.params_dict['vt_name']
        if self.type == 'bt_voting' or 'Voting' in self.executor_str:
            signal_col_names = ['Timestamp', '1minLong', '1minShort', '2minLong', '2minShort', '5minLong', '5minShort']
            if float(vt_name[:-3]) % 1 in [0.25, 0.5, 0.75]:
                signal_col_names = ['Timestamp', '1minLong', '1minShort', '2minLong', '2minShort', '5minLong', '5minShort',
                                    '15secLong', '15secShort', '30secLong', '30secShort']
                vt_name = '8.75min'
        if self.mock_lib is None:
            signal_manager = SignalManager(self.code, self.valid_dates, self.__signal_lib, vt_name=vt_name, signal_col_names=signal_col_names)
        else:
            signal_manager = SignalManager(self.code, self.valid_dates, self.__signal_lib, vt_name=vt_name, signal_col_names=signal_col_names,
                                           mock_lib=self.mock_lib, is_add_mock=False)
        self.signal_data = signal_manager.get_signals()
        if self.signal_data is None:
            return
        if self.type == 'cv_cross':
            self.signal_data_first, self.signal_data_second = signal_manager.get_signals_split()
        if self.freq == '1s':
            self.signal_data["TargetTimestamp"] = [self.__target_timestamp_dict.get(i) for i in self.signal_data["Timestamp"].tolist()]

    def load_param_dict(self, dfs=None):
        param_manager = ParamManager(self.executor_str, self.freq)
        param_manager.params_dict.update({'signal_lib': self.__signal_lib})
        if self.trigger_lib is not None and self.trigger_lib != '':
            trigger_dict = {}
            for trade_date in trading_day(self.st_date, self.ed_date):
                if self.trigger_lib == 'DynamicTriggers1000':
                    try:
                        triggers = FactorData().get_factor_value(self.trigger_lib, self.code, str(trade_date),
                                                                 [self.__signal_lib])[self.__signal_lib].to_dict()
                    except:
                        print(f'No Trigger: {self.code} {trade_date}')
                        continue
                else:
                    raise ValueError
                trigger_dict.update(triggers)
            param_manager.update_params({'triggers_by_date': trigger_dict})
        if self.__is_combine_params:
            param_file = f'{self.param_dir}/{self.code}.json'
            if file_exist(param_file, dfs=dfs):
                param_manager.update_code_default_param(self.code, self.st_date, self.ed_date, self.freq)
                param_update = load_json_file(param_file, dfs=dfs)
                param_manager.update_params(param_update)
                param_manager.update_params(self.overwrite_params)
                self.params_dict = param_manager.params_dict
        else:
            param_manager.update_code_default_param(self.code, self.st_date, self.ed_date, self.freq)
            param_manager.update_params(self.overwrite_params)
            self.params_dict = param_manager.params_dict
