from collections import defaultdict
import xbrain as xb

class PositionManager:
    def __init__(self, max_hold_size, max_sell_size, strategy_class):
        self.max_hold_size = max_hold_size # 单边敞口上限
        self.max_sell_size = max_sell_size # 单日卖出底仓限制
        self.buy_size_on_way = 0  # 买在途
        self.sell_size_on_way = 0  # 卖在途
        self.position_high_price = 0.0  # 持仓期间最大回撤的最高价
        self.position_low_price = 0.0  # 持仓期间最大回撤的最低价
        self.strategy_class = strategy_class
        self.position = strategy_class.get_position_by_name(strategy_class.datas[0]._name)
        self.last_position_size = 0

    def log(self, *args, level = None):
        if not level:
            self.strategy_class.log(*args, level = self.strategy_class.log_level)
        else:
            self.strategy_class.log(*args, level = level)

    def get_restrict_order_size(self, size, side):
        """
        获取不超过单边敞口、最大可卖数量的可买/卖的合法数量，根据仓位和在途计算，避免超卖超买（仅支持单标的）
        :param size: 申请委托的数量，买卖都为正
        :param side: 买卖方向
        :return:
        """
        net_position = self.position.size
        size = abs(int(size))
        available_size = 0
        if side == xb.Order.Sell:
            if self.max_sell_size - size <= 0:
                # 单日最大卖出数量
                if not net_position:
                    self.strategy_class.global_stop_flag = True
                self.log("可卖数量为0：今日底仓已用完！")
                return available_size
            else:
                # 单边敞口
                if net_position - abs(self.sell_size_on_way) - abs(size) < -self.max_hold_size:
                    self.log("可卖数量为0：超过单边敞口！")
                else:
                    available_size = size
        elif side == xb.Order.Buy:
            if self.max_sell_size - net_position - size - self.buy_size_on_way <= 0:
                # 单日最大卖出数量
                if not net_position:
                    self.strategy_class.global_stop_flag = True
                self.log("可买数量为0：今日底仓已用完！")
                return available_size
            else:
                # 单边敞口
                if net_position + self.buy_size_on_way + size > self.max_hold_size:
                    self.log("可买数量为0：超过单边敞口！")
                else:
                    available_size = size
        else:
            raise Exception()
        return available_size


    def get_position_mdd_ret(self, curr_price, mode="midprice"):
        # 计算当前持仓最大回撤的收益率(单位千分数)，为负表示相对最优价回撤多少
        mdd_return = 0
        if mode == "midprice":
            # 中间价计算收益率
            if self.position.size < 0:
                base_price = self.position_low_price
                if base_price is not None and base_price != 0:
                    mdd_return = (base_price - curr_price) / base_price * 1000
            elif self.position.size > 0:
                base_price = self.position_high_price
                if base_price is not None and base_price != 0:
                    mdd_return = (curr_price - base_price) / base_price * 1000
            return mdd_return


    def get_position_avg_ret(self,curr_price, mode="midprice"):
        # 计算当前平均开仓成本的收益率(单位千分数)，为负表示相对开仓成本回撤多少
        avg_return = 0
        if mode == "midprice":
            # 开仓价计算收益率
            base_price = self.position.price
            if self.position.size < 0:
                if base_price is not None and base_price != 0:
                    avg_return = (base_price - curr_price) / base_price * 1000
            elif self.position.size > 0:
                if base_price is not None and base_price != 0:
                    avg_return = (curr_price - base_price) / base_price * 1000
            return avg_return

    def update_position_optimal_price(self, curr_price):
        """
        更新持仓的最优价，多头持仓取最高价，空头持仓取最低价
        :param curr_price:
        :return:
        """
        if not self.position.size or self.position.size*self.last_position_size<0:
            self.position_high_price = 0
            self.position_low_price = curr_price # 中间价止损/close价止损  self.datas[0].close[0]
        else:
            self.position_high_price = max(self.position_high_price,curr_price)
            self.position_low_price = min(self.position_low_price, curr_price)
        self.last_position_size = self.position.size


    def update_position_created(self, order):
        if order.isbuy():
            # 更新在途
            self.buy_size_on_way = self.buy_size_on_way + order.created.size
        elif order.issell():
            # 更新在途
            self.max_sell_size = self.max_sell_size - abs(order.created.size)
            self.sell_size_on_way = self.sell_size_on_way + abs(order.created.size)

    def update_position_executed(self, order):
        if order.isbuy():
            # 更新在途
            self.buy_size_on_way = self.buy_size_on_way - abs(order.executed.incresize)
        elif order.issell():
            # 更新在途
            self.sell_size_on_way = self.sell_size_on_way - abs(order.executed.incresize)

    def update_position_cancel(self, order):
        if order.issell():
            # 如果一笔卖订单分多次成交时，成交量变动需要扣除相对变化值
            self.max_sell_size = self.max_sell_size + abs(order.created.size) - abs(order.executed.size)

        if order.isbuy():
            self.buy_size_on_way = self.buy_size_on_way - (abs(order.created.size) - abs(order.executed.size))
        if order.issell():
            self.sell_size_on_way = self.sell_size_on_way - (abs(order.created.size) - abs(order.executed.size))

