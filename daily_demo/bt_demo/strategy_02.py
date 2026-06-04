# -*- coding: utf-8 -*-

import xbrain as xb
from xbrain.strategy_base import StrategyBase



# 策略类，是用户需要实现的主要内容。
# 此例是一个完整有意义的策略，主要展示如何在 XBrain 框架中下单并获取返回的订单对象，通过后续查询，继续操作订单。
# 策略介绍：收盘价站上 SMA 均线时开仓买入，+10%止盈，-10%止损。
# 常用下单函数：
# buy(data, size=X)
# sell(data, size=X)
# order_target_size(data, target=X)
# closeout(data)
# cancel(order)

class StrategyExample(StrategyBase): # 策略类需继承 StrategyBase 基类

    # 策略涉及的参数在 params 中定义，通过 self.params.p1 访问
    params = (
        ('p1', 60),                         # SMA 参数
        ('stoploss', 0.1),                  # 止损比例
        ('takeprofit', 0.1),                # 止盈比例
        ('tradesize', 10),                   # 每笔交易手数
    )

    def __init__(self):
        # XBrain 支持多数据源，多时间窗口回测，并自动进行时间对齐。
        # 用户通过 xbrain.add_data，添加任意多数据，并在策略类中通过 self.datas[n] 访问对应顺序的数据
        # self.datas[0] 即为第一个数据源，以此类推。
        self.close = self.datas[0].close
        self.sma = xb.talib.SMA(                   # 调用 xbrain 集成的 talib 因子计算功能，计算短期 SMA 值
            self.close, timeperiod=self.params.p1  # 指定 SMA 参数为 self.params.p1
        )
        self.order = None

    def next(self):
        # 通过 broker 对象的 get_position 方法，获得持仓信息，
        # 持仓信息即 Position 对象包含：
        # -- size: 头寸大小
        # -- price: 平均成本价
        pos = self.broker.get_position(self.datas[0])
        pos_size = pos.size
        pos_cost = pos.price

        self.log('Close: {}, SMA: {}, Pos: {}@{}'.format(
            self.close[0], self.sma[0], pos_size, pos_cost
        ))

        if self.order is not None and self.order.status_str not in ['Completed', 'Canceled'] \
           and self.count_bars_since_order_submit(self.order) > 3:
            self.cancel(self.order)

        # 如果无持仓，收盘价站上（即金叉）SMA 时开仓买入
        if pos_size == 0 and self.close[0] > self.sma[0] and self.close[-1] <= self.sma[-1]:
            print("**************************")
            self.order = self.buy(size=self.params.tradesize)
            print("==========================")
            return

        # 如果有持仓，则计算盈亏情况，决定是否止盈止损
        # 止损
        if pos_size > 0 and self.close[0] <= pos_cost * (1 - self.params.stoploss):
            self.sell(size=self.params.tradesize)
            return

        # 止盈
        if pos_size > 0 and self.close[0] >= pos_cost * (1 + self.params.takeprofit):
            self.sell(size=self.params.tradesize)
            return

        # 持仓超过 250 分钟，则清仓
        if pos_size > 0 and self.count_bars_since_trade_open() >= 250:
            self.order_target_size(data=self.datas[0], target=0)
            return
