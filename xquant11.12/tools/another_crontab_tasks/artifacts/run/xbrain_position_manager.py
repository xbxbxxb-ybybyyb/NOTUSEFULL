from collections import defaultdict
from xbrain import Order


class PositionManager:
    def __init__(self, HOLD_POSITION_LIMIT, SELL_POSITION_LIMIT):
        self.hold_position_limit = HOLD_POSITION_LIMIT
        self.sellable_position = SELL_POSITION_LIMIT
        self.net_position = 0  # 相对于底仓的持仓变化值,负值表示空头
        self.last_net_position = 0 # 上次的净持仓
        self.buy_position_order_dict ={} #多头持仓订单表
        self.sell_position_order_dict = {} #空头持仓订单表
        self.buysize_onway = 0
        self.sellsize_onway = 0
        self.net_position_his_high = defaultdict(float) #当前持仓的最大价格
        self.net_position_his_low= defaultdict(float)  # 当前持仓的最小价格
        self.signal_pending_order = {} # 未完成的订单
        self.stop_pending_order = {} #未完成的撤单
        self.wining_pending_order = {} # 止盈订单


    def get_net_postion(self):
        return self.net_position

    def add_signal_pending_order(self, order):
        order_data = self.pending_order_to_dict(order)
        self.signal_pending_order[order.ref] = order_data
        self.signal_pending_order[order.ref]["order"] = order

    def add_stop_pending_order(self, order):
        order_data = self.pending_order_to_dict(order)
        self.stop_pending_order[order.ref] = order_data
        self.stop_pending_order[order.ref]["order"] = order

    def add_wining_pending_order(self, order, create_dt = None):
        order_data = self.pending_order_to_dict(order)
        self.wining_pending_order[order.ref] = order_data
        self.wining_pending_order[order.ref]["order"] = order
        if create_dt:
            self.wining_pending_order[order.ref]["create_dt"] = create_dt


    def order_to_dict(self, order):
        return {
            "ref": order.ref,
            "dataname": order.dataname,
            "bs_str": order.bs_str,
            "status_str": order.status_str,
            "size": order.size,
            "price": order.price,
            "exec_size": order.exec_size,
            "exec_remsize": order.exec_remsize
        }

    def pending_order_to_dict(self, order):
        return {
            "ref": order.ref,
            "bs_str": order.bs_str,
            "size": order.size,
            "price": order.price,
            "exec_size": order.exec_size,
            "exec_remsize": order.exec_remsize,
            "create_dt": order.created.dt
        }


    def hedge_position_order(self, hedge_order):
        # 消解持仓
        hedge_order_data = self.order_to_dict(hedge_order)
        if hedge_order.isbuy():
            buy_hedge_size = abs(hedge_order.executed.incresize)
            for hedge_order_ref in self.sell_position_order_dict:
                sell_hedge_order_data = self.sell_position_order_dict[hedge_order_ref]
                if sell_hedge_order_data["open_size"] == 0:
                    # print("info 可平仓数量为0", sell_hedge_order_data)
                    continue
                hedge_size = min(buy_hedge_size, abs(sell_hedge_order_data["open_size"]))
                sell_hedge_order_data["open_size"] = sell_hedge_order_data["open_size"] - hedge_size  # 更新开仓量
                sell_hedge_order_data["hedge_size"] = sell_hedge_order_data["hedge_size"] + hedge_size
                sell_hedge_order_data["hedge_ref_size"].append((hedge_order.ref, hedge_size))
                buy_hedge_size -= hedge_size
                if buy_hedge_size <= 0:
                    break

            # 剩余buy_open_size新加入到buy_position_order
            if buy_hedge_size:
                # 当前卖单未全部对冲，先加入买方持仓订单，等待后续卖单对冲
                self.buy_position_order_dict[hedge_order.ref] = hedge_order_data
                self.buy_position_order_dict[hedge_order.ref]["open_size"] = buy_hedge_size
                self.buy_position_order_dict[hedge_order.ref]["hedge_size"] = 0
                self.buy_position_order_dict[hedge_order.ref]["hedge_ref_size"] = []
                self.buy_position_order_dict[hedge_order.ref]["order"] = hedge_order

        elif hedge_order.issell():
            # sell_open_size 先消耗buy_position_order中的open_size
            sell_hedge_size = abs(hedge_order.executed.incresize)
            for buy_order_ref in self.buy_position_order_dict:
                buy_hedge_order_data = self.buy_position_order_dict[buy_order_ref]
                if buy_hedge_order_data["open_size"] <= 0:
                    # print("info：可平仓数量为0 ", buy_hedge_order_data)
                    continue
                hedge_size = min(sell_hedge_size, abs(buy_hedge_order_data["open_size"]))
                buy_hedge_order_data["open_size"] = buy_hedge_order_data["open_size"] - hedge_size
                buy_hedge_order_data["hedge_size"] = buy_hedge_order_data["hedge_size"]+hedge_size
                buy_hedge_order_data["hedge_ref_size"].append((hedge_order.ref, hedge_size))
                sell_hedge_size = sell_hedge_size - hedge_size
                if sell_hedge_size <= 0:
                    break
            if sell_hedge_size:
                self.sell_position_order_dict[hedge_order.ref] = hedge_order_data
                self.sell_position_order_dict[hedge_order.ref]["open_size"] = sell_hedge_size
                self.sell_position_order_dict[hedge_order.ref]["hedge_size"] = 0
                self.sell_position_order_dict[hedge_order.ref]["hedge_ref_size"] = []
                self.sell_position_order_dict[hedge_order.ref]["order"] = hedge_order
        else:
            raise Exception("订单方向不明！")


    def incre_postion_order(self, new_order):
        "增加持仓"
        new_order_data = self.order_to_dict(new_order)
        if new_order.isbuy():
            # buy_open_size增加buy_position_order
            buy_open_size = abs(new_order.executed.incresize)
            if not self.buy_position_order_dict.get(new_order.ref, None):
                self.buy_position_order_dict[new_order.ref] = new_order_data
                self.buy_position_order_dict[new_order.ref]["open_size"] = buy_open_size
                self.buy_position_order_dict[new_order.ref]["hedge_size"] = 0
                self.buy_position_order_dict[new_order.ref]["hedge_ref_size"] = []
                self.buy_position_order_dict[new_order.ref]["order"] = new_order
            else:
                order_data = self.buy_position_order_dict.get(new_order.ref)
                order_data["open_size"] = order_data["open_size"] + buy_open_size
                order_data["exec_size"] = new_order.executed.size
                order_data["exec_remsize"] = new_order.executed.remsize
        elif new_order.issell():
            sell_open_size = abs(new_order.executed.incresize)
            if not self.sell_position_order_dict.get(new_order.ref, None):
                self.sell_position_order_dict[new_order.ref] = new_order_data
                self.sell_position_order_dict[new_order.ref]["open_size"] = sell_open_size
                self.sell_position_order_dict[new_order.ref]["hedge_size"] = 0
                self.sell_position_order_dict[new_order.ref]["hedge_ref_size"] = []
                self.sell_position_order_dict[new_order.ref]["order"] = new_order
            else:
                order_data = self.sell_position_order_dict.get(new_order.ref)
                order_data["open_size"] = order_data["open_size"] + sell_open_size
                order_data["exec_size"] = new_order.executed.size
                order_data["exec_remsize"] = new_order.executed.remsize
        else:
            raise Exception("订单方向不明！")


    def update_position_exec(self, order):
        self.last_net_position = self.net_position
        # 更新持仓
        if order.isbuy():
            if self.net_position>=0:
                self.incre_postion_order(order)
            else:
                self.hedge_position_order(order)
            # 更新在途
            self.buysize_onway = self.buysize_onway - abs(order.executed.incresize)
            self.net_position = self.net_position + abs(order.executed.incresize)

        elif order.issell():
            if self.net_position <= 0:
                self.incre_postion_order(order)
            else:
                self.hedge_position_order(order)
            # 更新在途
            self.sellsize_onway = self.sellsize_onway - abs(order.executed.incresize)
            self.net_position = self.net_position - abs(order.executed.incresize)

        # 移出已完成的订单
        if order.ref in self.signal_pending_order:
            if order.executed.size == order.created.size:
                self.signal_pending_order.pop(order.ref)
            else:
                self.signal_pending_order[order.ref]["exec_size"] += abs(order.executed.incresize)
                self.signal_pending_order[order.ref]["exec_remsize"] -= abs(order.executed.incresize)
        if order.ref in self.wining_pending_order:
            if order.executed.size == order.created.size:
                self.wining_pending_order.pop(order.ref)
            else:
                self.wining_pending_order[order.ref]["exec_size"] += abs(order.executed.incresize)
                self.wining_pending_order[order.ref]["exec_remsize"] -= abs(order.executed.incresize)
        if order.ref in self.stop_pending_order:
            if order.executed.size == order.created.size:
                self.stop_pending_order.pop(order.ref)
            else:
                self.stop_pending_order[order.ref]["exec_size"] += abs(order.executed.incresize)
                self.stop_pending_order[order.ref]["exec_remsize"] -= abs(order.executed.incresize)


    def update_position_cancel(self, order):
        self.last_net_position = self.net_position
        if order.issell():
            # 如果一笔卖订单分多次成交时，成交量变动需要扣除相对变化值
            self.sellable_position = self.sellable_position + abs(order.created.size) - abs(order.executed.size)

        if order.isbuy():
            self.buysize_onway = self.buysize_onway - (abs(order.created.size) - abs(order.executed.size))
        if order.issell():
            self.sellsize_onway = self.sellsize_onway - (abs(order.created.size) - abs(order.executed.size))
        # 移出pending_order队列
        if order.ref in self.signal_pending_order:
            self.signal_pending_order.pop(order.ref)
        if order.ref in self.stop_pending_order:
            self.stop_pending_order.pop(order.ref)
        if order.ref in self.wining_pending_order:
            self.wining_pending_order.pop(order.ref)

