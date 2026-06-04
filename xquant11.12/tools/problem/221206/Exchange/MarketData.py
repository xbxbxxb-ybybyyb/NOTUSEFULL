import datetime
import numpy as np


class MarketData:
    def __init__(self, tick_data, transaction_data):
        """
        :param tick_data: list
        :param transaction_data: list
        """
        self._code = transaction_data[0]["Code"][0]

        self._tick_columns = [
            "AskP10", "AskP9", "AskP8", "AskP7", "AskP6", "AskP5", "AskP4", "AskP3", "AskP2", "AskP1",
            "BidP1", "BidP2", "BidP3", "BidP4", "BidP5", "BidP6", "BidP7", "BidP8", "BidP9", "BidP10",
            "AskV10", "AskV9", "AskV8", "AskV7", "AskV6", "AskV5", "AskV4", "AskV3", "AskV2", "AskV1",
            "BidV1", "BidV2", "BidV3", "BidV4", "BidV5", "BidV6", "BidV7", "BidV8", "BidV9", "BidV10"
        ]
        self._transaction_columns = ["Price", "Volume"]

        self._tick_data, self._transaction_data = self._transform_tick_and_transaction_data(tick_data, transaction_data)

        self._tick_timestamp_array_today = None
        self._tick_data_today = None
        self._transaction_timestamp_array_today = None
        self._transaction_data_today = None

        self._current_date = None

    def update_current_date_for_tick_and_transaction_data(self, timestamp):
        """
        更新self._tick_data_today和self._transaction_data_today
        :param timestamp: float
        """
        date_from_timestamp = datetime.datetime.fromtimestamp(timestamp).strftime("%Y%m%d")

        if date_from_timestamp != self._current_date:
            self._current_date = date_from_timestamp

            tick_data_tuple = self._tick_data[self._current_date]
            transaction_data_tuple = self._transaction_data[self._current_date]

            self._tick_timestamp_array_today = tick_data_tuple[0]
            self._tick_data_today = tick_data_tuple[1]
            self._transaction_timestamp_array_today = transaction_data_tuple[0]
            self._transaction_data_today = transaction_data_tuple[1]

    def get_tick_timestamp(self, timestamp):
        """
        获取截至timestamp最新的tick的timestamp
        :param timestamp: float
        :return: float
        """
        tick_index = np.searchsorted(self._tick_timestamp_array_today, timestamp, side="right") - 1

        if tick_index == -1:
            raise ValueError("{} has no tick before or at {}"
                             .format(self._code, datetime.datetime.fromtimestamp(timestamp)))

        return self._tick_timestamp_array_today[tick_index]

    def get_tick_timestamp_list(self, start_timestamp, end_timestamp, right_closed):
        """
        获取(start_timestamp, end_timestamp]或(start_timestamp, end_timestamp)时间段内的tick_timestamp
        :param start_timestamp: float
        :param end_timestamp: float
        :param right_closed: bool
        :return: np.ndarray
        """
        start_index = np.searchsorted(self._tick_timestamp_array_today, start_timestamp, side="right")
        if right_closed:
            end_index = np.searchsorted(self._tick_timestamp_array_today, end_timestamp, side="right")
        else:
            end_index = np.searchsorted(self._tick_timestamp_array_today, end_timestamp)

        return self._tick_timestamp_array_today[start_index:end_index].copy()

    def get_quote(self, timestamp):
        """
        获取截至timestamp时刻的盘口
        :param timestamp: float
        :return: np.ndarray, float
        """
        quote_index = np.searchsorted(self._tick_timestamp_array_today, timestamp, side="right") - 1

        if quote_index == -1:
            raise ValueError("{} has no tick before or at {}"
                             .format(self._code, datetime.datetime.fromtimestamp(timestamp)))

        price_array = self._tick_data_today[quote_index, :20].copy()
        volume_array = self._tick_data_today[quote_index, 20:].copy()

        return np.stack([price_array, volume_array], axis=1), self._tick_timestamp_array_today[quote_index]

    def get_transaction_data(self, start_timestamp, end_timestamp):
        """
        获取[start_timestamp, end_timestamp)时间段内的逐笔成交信息
        :param start_timestamp: float
        :param end_timestamp: float
        :return: np.ndarray
        """
        start_index = np.searchsorted(self._transaction_timestamp_array_today, start_timestamp)
        end_index = np.searchsorted(self._transaction_timestamp_array_today, end_timestamp)

        return self._transaction_data_today[start_index:end_index].copy()

    def _transform_tick_and_transaction_data(self, tick_data, transaction_data):
        """
        把tick data和transaction data按天转换为pd.DataFrame
        :param tick_data: list
        :param transaction_data: list
        :return: (dict, dict)
        """
        tick_data_dict = {}
        for tick_data_each in tick_data:
            tick_data_list = []
            for key in self._tick_columns:
                tick_data_list.append(tick_data_each[key])
            tick_data_dict[str(tick_data_each["Date"][0])] = \
                (np.array(tick_data_each["TimeStamp"]), np.stack(tick_data_list, axis=1))

        transaction_data_dict = {}
        for transaction_data_each in transaction_data:
            transaction_data_list = []
            for key in self._transaction_columns:
                transaction_data_list.append(transaction_data_each[key])
            transaction_data_dict[str(transaction_data_each["Date"][0])] = \
                (np.array(transaction_data_each["TimeStamp"]), np.stack(transaction_data_list, axis=1))

        return tick_data_dict, transaction_data_dict