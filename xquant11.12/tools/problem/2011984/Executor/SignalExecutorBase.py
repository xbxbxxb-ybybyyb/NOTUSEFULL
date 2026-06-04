"""Executor下单的基类（剔除创业板移3s的逻辑）——update @2021.12.3"""

import time


class SignalExecutorBase:
    def __init__(self, position_manager, param_manager):
        self._positionMgr = position_manager
        self._param = param_manager
        self.__data_dict = None
        self.__tickData = None
        self.__slice_data_last = None
        self._ask0_price_today = []
        self._bid0_price_today = []
        self._volume_today = []
        self._amt_today = []
        self._ask_predictions = []
        self._bid_predictions = []

    def reset_new_day(self, trade_date):
        self.__slice_data_last = None
        self._ask0_price_today = []
        self._bid0_price_today = []
        self._volume_today = []
        self._amt_today = []
        self._ask_predictions = []
        self._bid_predictions = []
        self.on_new_day(trade_date)

    def on_new_day(self, trade_date):
        pass

    def update_predict_info(self, predictions, slice_data):
        pass

    def is_open_long(self, predictions, slice_data):
        pass

    def is_open_short(self, predictions, slice_data):
        pass

    def is_close_long(self, predictions, slice_data):
        pass

    def is_close_short(self, predictions, slice_data):
        pass

    def set_data_dict(self, data_dict, tick_data):
        self.__data_dict = data_dict
        self.__tickData = tick_data

    def _process_tick_data(self, predictions, slice_data):
        tick_time = slice_data.time
        if self.__slice_data_last is not None and self.__slice_data_last.time <= 113000000 and slice_data.time >= 130000000:
            # 午盘重置
            self.__slice_data_last = None
            self._ask0_price_today = []
            self._bid0_price_today = []
            self._volume_today = []
            self._amt_today = []
            self._ask_predictions = []
            self._bid_predictions = []

        if not self._volume_today:
            date_index = 0
            for i in range(len(self.__tickData)):
                if self.__tickData[i] is not None and self.__tickData[i]['Date'][0] == slice_data.date:
                    date_index = i
                    break
            tick_data = self.__tickData[date_index]
            tick_time_list = tick_data['Time']
            tick_index = 0
            for i in range(len(tick_time_list)):
                if tick_time_list[i] >= tick_time:
                    tick_index = i
                    break
            start_index = 0
            for i in range(len(tick_time_list)):
                if (tick_time < 120000000 and tick_time_list[i] >= 93015000) or (tick_time > 120000000 and tick_time_list[i] >= 130015000):
                    start_index = i
                    break

            for i in range(start_index, tick_index + 1):
                pre_acc_volume = tick_data['AccVolume'][max(0, i - 1)]
                cur_acc_volume = tick_data['AccVolume'][i]
                pre_acc_amt = tick_data['AccTurover'][max(0, i - 1)]
                cur_acc_amt = tick_data['AccTurover'][i]
                self._volume_today.append(cur_acc_volume - pre_acc_volume)
                self._amt_today.append(cur_acc_amt - pre_acc_amt)
                self._bid0_price_today.append(tick_data['BidP1'][i])
                self._ask0_price_today.append(tick_data['AskP1'][i])
        elif 93015000 <= tick_time < 113000000 or 130015000 <= tick_time < 145700000:
            self._volume_today.append(slice_data.totalVolume - self.__slice_data_last.totalVolume)
            self._amt_today.append(slice_data.totalAmount - self.__slice_data_last.totalAmount)
            self._bid0_price_today.append(slice_data.bidPrice[0])
            self._ask0_price_today.append(slice_data.askPrice[0])
        self.__slice_data_last = slice_data
        self._ask_predictions.append(predictions[1])
        self._bid_predictions.append(predictions[0])

        # is_valid
        tick_time = time.strftime("%H:%M:%S", time.localtime(slice_data.timeStamp))
        if self._param['trading_start_morning'] <= tick_time < '11:30:00' or self._param['trading_start_afternoon'] <= tick_time < '14:57:00':
            return True
        else:
            return False

    def _process_tick_data_1s(self, predictions, slice_data):
        tick_time = slice_data.time
        if self.__slice_data_last is not None and self.__slice_data_last.time <= 113000000 and slice_data.time >= 130000000:
            # 午盘重置
            self.__slice_data_last = None
            self._ask0_price_today = []
            self._bid0_price_today = []
            self._volume_today = []
            self._amt_today = []
            self._ask_predictions = []
            self._bid_predictions = []

        if not self._volume_today:
            volume, amount = self.__tickData.get(slice_data.timeStamp)
            self._volume_today.append(volume)
            self._amt_today.append(amount)

        elif 93015000 <= tick_time < 113000000 or 130015000 <= tick_time < 145700000:
            volume, amount = self.__tickData.get(slice_data.timeStamp)
            self._volume_today.append(volume)
            self._amt_today.append(amount)
            self._bid0_price_today.append(slice_data.bidPrice[0])
            self._ask0_price_today.append(slice_data.askPrice[0])
        self.__slice_data_last = slice_data
        self._ask_predictions.append(predictions[1])
        self._bid_predictions.append(predictions[0])

        # is_valid
        tick_time = time.strftime("%H:%M:%S", time.localtime(slice_data.timeStamp))
        if self._param['trading_start_morning'] <= tick_time < '11:30:00' or self._param['trading_start_afternoon'] <= tick_time < '14:57:00':
            return True
        else:
            return False

    def get_next_slice_data(self, slice_data):
        """如果是创业板股票，slice_data使用下一个tick的数据"""
        return slice_data

    def check_holo_price(self, price, side, slice_data):
        """如果应用盘口还原，则该方法会去检查挂单价格"""
        return price
