"""转债临停处理————update @2021.8.13"""


class LimitProcess:
    def __init__(self, limit_params):
        self._limit_params = limit_params
        self.__limit_recover_counter = limit_params['limit_recover_counter']

        self.__FIRST_UP_LIMIT = 200
        self.__SECOND_UP_LIMIT = 300
        self.__FIRST_DOWN_LIMIT = -200
        self.__SECOND_DOWN_LIMIT = -300
        self.__LIMIT_STATUS = None
        self.__is_first_up = False  # 是否触发第一次向上临停
        self.__is_first_down = False  # 是否触发第一次向下临停
        self.__is_second_up = False  # 是否触发第二次向上临停
        self.__is_second_down = False  # 是否触发第二次向下临停
        self.__is_first_position_cleared = False
        self.__is_second_position_cleared = False
        self.__first_limit_recover_flag = True  # 经过一次临停后，价格再次触及临停价，也不会发生临停
        self.__second_limit_recover_flag = True

    def on_new_tick(self, slice_data):
        self.__limit_recover_counter += 1
        price_ratio = 1000 * (slice_data.lastPrice / slice_data.previousClosingPrice - 1)
        if price_ratio >= self.__FIRST_UP_LIMIT:
            self.__is_first_up = True
        elif price_ratio <= self.__FIRST_DOWN_LIMIT:
            self.__is_first_down = True
        if price_ratio >= self.__SECOND_UP_LIMIT:
            self.__is_second_up = True
        elif price_ratio <= self.__SECOND_DOWN_LIMIT:
            self.__is_second_down = True

        if (self.__is_first_up or self.__is_first_down) and self.__first_limit_recover_flag:
            self.__limit_recover_counter = 0
            self.__first_limit_recover_flag = False

        if (self.__is_second_up or self.__is_second_down) and self.__second_limit_recover_flag:
            self.__limit_recover_counter = 0
            self.__second_limit_recover_flag = False

    def process_no_position(self, slice_data):
        if self.__is_first_up or self.__is_first_down:
            self.__is_first_position_cleared = True
        if self.__is_second_up or self.__is_second_down:
            self.__is_second_position_cleared = True
        condition1 = self.is_price_limit_deal(slice_data)  # 快达到临停状态
        condition2 = self.__limit_recover_counter < self.__limit_recover_counter  # 临停结束之后，未达到一定时间
        return condition1 or condition2

    def get_limit_price(self, slice_data):
        ask0 = slice_data.askPrice[0]
        bid0 = slice_data.bidPrice[0]
        first_close_long_limited_coef = 0.995
        second_close_long_limited_coef = 0.99

        price = ask0
        if self.__LIMIT_STATUS == "FIRST_UP_LIMIT":
            price = max(bid0, ask0 - 0.01)
        elif self.__LIMIT_STATUS == "SECOND_UP_LIMIT":
            price = max(bid0, ask0 - 0.02)
        elif self.__LIMIT_STATUS == "FIRST_DOWN_LIMIT":
            price = max(bid0 - 0.01, ask0 * first_close_long_limited_coef)
        elif self.__LIMIT_STATUS == "SECOND_DOWN_LIMIT":
            price = max(bid0 - 0.01, ask0 * second_close_long_limited_coef)
        elif self.__LIMIT_STATUS == "LIMIT_CLEAR":
            price = max(bid0 * self._limit_params['price_limit_clear_aggressive_coef'],
                        ask0 * self._limit_params['price_limit_clear_passive_coef'])
        return price

    def is_price_limit_deal(self, slice_data):
        """临停前（马上就临停了，但是还未临停）"""
        price_ratio = 1000 * (slice_data.lastPrice / slice_data.previousClosingPrice - 1)
        if not (self.__is_second_up or self.__is_second_down):
            if self.__SECOND_DOWN_LIMIT <= price_ratio < self.__SECOND_DOWN_LIMIT + self._limit_params['down_offset']:
                self.__LIMIT_STATUS = "SECOND_DOWN_LIMIT"
                return True
            elif self.__SECOND_UP_LIMIT - self._limit_params['up_offset'] < price_ratio <= self.__SECOND_UP_LIMIT:
                self.__LIMIT_STATUS = "SECOND_UP_LIMIT"
                return True
        if not (self.__is_first_up or self.__is_first_down):
            if self.__FIRST_UP_LIMIT - self._limit_params['up_offset'] < price_ratio <= self.__FIRST_UP_LIMIT:
                self.__LIMIT_STATUS = "FIRST_UP_LIMIT"
                return True
            elif self.__FIRST_DOWN_LIMIT <= price_ratio < self.__FIRST_DOWN_LIMIT + self._limit_params['down_offset']:
                self.__LIMIT_STATUS = "FIRST_DOWN_LIMIT"
                return True
        return False

    def is_price_limit_clear(self):
        """临停后（已经触发临停），且有持仓"""
        is_first = (self.__is_first_up or self.__is_first_down) and not self.__is_first_position_cleared
        is_second = (self.__is_second_up or self.__is_second_down) and not self.__is_second_position_cleared
        if is_first or is_second:
            self.__LIMIT_STATUS = "LIMIT_CLEAR"
            return True
        return False
