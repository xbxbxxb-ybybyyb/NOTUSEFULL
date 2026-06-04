import datetime as dt
import json
import pandas as pd
from xquant.xqutils.xqfile import HDFSFile
from xquant.factordata import FactorData
from DataIO.StaticInfo import StaticInfo
from DataIO.Utils import MyPrint


class SignalManager:
    def __init__(self, symbol: str, start_date: str, end_date: str, signal_library: str, bt_dir: str):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.signal_library = signal_library
        self.bt_dir = bt_dir

        self.hf = HDFSFile()
        self.fa = FactorData()

        self.static_info = StaticInfo(self.symbol, self.start_date, self.end_date)
        self.dates, self.first_half_dates, self.second_half_dates = self.split_trade_dates()
        
        self.prediction_names = [
            "timestamp", "ticktime", "prediction1minLong", "prediction2minLong",
            "prediction5minLong", "prediction1minShort", "prediction2minShort",
            "prediction5minShort"
        ]
        self.rename_dict = {
            "timestamp": "Timestamp",
            "ticktime": "Ticktime",
            "prediction1minLong": "1minLong",
            "prediction1minShort": "1minShort",
            "prediction2minLong": "2minLong",
            "prediction2minShort": "2minShort",
            "prediction5minLong": "5minLong",
            "prediction5minShort": "5minShort"
        }

        self.__pre_process_first_half()
        self.__pre_process_second_half()

        self.__tick = None
        self.__transaction = None
        self.__tick_dict = None
        self.__load_order_capacity()

    def split_trade_dates(self):
        valid_trade_dates = self.static_info.load_valid_dates()
        dates = sorted(valid_trade_dates)
        half = int(len(dates) / 2)
        first_half_dates, second_half_dates = dates[:half], dates[half:]
        return dates, first_half_dates, second_half_dates

    def __pre_process_first_half(self) -> None:
        self.__first_half_data: pd.DataFrame = None
        for date in self.first_half_dates:
            data = self.__pre_process_single(date)
            if data is None:
                continue
            if self.__first_half_data is not None:
                self.__first_half_data = pd.concat([self.__first_half_data, data], axis=0)
            else:
                self.__first_half_data = data

    def __pre_process_second_half(self) -> None:
        self.__second_half_data: pd.DataFrame = None
        for date in self.second_half_dates:
            data = self.__pre_process_single(date)
            if data is None:
                continue
            if self.__second_half_data is not None:
                self.__second_half_data = pd.concat([self.__second_half_data, data], axis=0)
            else:
                self.__second_half_data = data

    def __pre_process_single(self, date: str) -> pd.DataFrame:
        try:
            data = self.fa.get_factor_value(self.signal_library, self.symbol, date, self.prediction_names)
            data = data.rename(columns=self.rename_dict)
        except:
            MyPrint(" {}-{} no signal data ".format(self.symbol, date))
            return None

        column_long = data['1minLong'] + data['2minLong'] + data['5minLong']
        column_long /= 3
        data = data.assign(ave_long=column_long)

        column_short = data['1minShort'] + data['2minShort'] + data['5minShort']
        column_short /= 3
        data = data.assign(ave_short=column_short)

        data['Ticktime'] = data['Ticktime'].apply(lambda x: dt.datetime.strptime(x, '%H:%M:%S').time())
        data = SignalManager.average_special_time(data, dt.time(11, 25, 0), dt.time(11, 28, 0), dt.time(11, 30, 0))
        data = SignalManager.average_special_time(data, dt.time(14, 52, 0), dt.time(14, 55, 0), dt.time(14, 57, 0))
        return data

    @staticmethod
    def average_special_time(data: pd.DataFrame, time1: dt.time, time2: dt.time, time3: dt.time) -> pd.DataFrame:
        filter1 = (data['Ticktime'] >= time1) & (data['Ticktime'] < time2)
        index1 = data.loc[filter1, 'Ticktime'].index
        ave_long1 = (data.loc[index1, '1minLong'] + data.loc[index1, '2minLong']) / 2
        ave_short1 = (data.loc[index1, '1minShort'] + data.loc[index1, '2minShort']) / 2
        data.loc[index1, 'ave_long'] = ave_long1
        data.loc[index1, 'ave_short'] = ave_short1

        filter2 = (data['Ticktime'] >= time2) & (data['Ticktime'] < time3)
        index2 = data.loc[filter2, 'Ticktime'].index
        ave_long2 = data.loc[index2, '1minLong']
        ave_short2 = data.loc[index2, '1minShort']
        data.loc[index2, 'ave_long'] = ave_long2
        data.loc[index2, 'ave_short'] = ave_short2
        return data

    def __load_order_capacity(self):
        with self.hf.open(self.bt_dir + self.symbol + '/OrderCapacity.json', 'rb') as f:
            data = f.read()
            self.__capacity = json.loads(data)

    def get_signals(self) -> pd.DataFrame:
        try:
            return pd.concat([self.__first_half_data, self.__second_half_data], axis=0)
        except Exception as e:
            return None

    def get_signals_from_first_half(self) -> pd.DataFrame:
        return self.__first_half_data

    def get_signals_from_second_half(self) -> pd.DataFrame:
        return self.__second_half_data

    def get_order_capacity(self):
        return self.__capacity


if __name__ == '__main__':
    data_manager = SignalManager('000333.SZ', "20211115", "20211115", "Everest20210201_20210515", bt_dir="")
    data_temp = data_manager.get_signals()
    data_temp.to_csv('test.csv')
