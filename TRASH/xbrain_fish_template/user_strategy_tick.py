# -*- coding: utf-8 -*-
import xbrain_pro as xb
from xbrain_pro import *
import pandas as pd

pd.set_option('display.max_columns', None)


class StrategyMMDemo(StrategyBase):  # 策略类需继承 StrategyBase 基类
    # 策略涉及的参数在 params 中定义，通过 self.params 访问
    params = (
        ('SYMBOL', ''),
        ('trade_size', 200),
        ('gap_pct', 0.003)
    )

    def __init__(self):
        self.trade_size = self.p.trade_size
        self.gap_pct = self.p.gap_pct

    def next(self):
        current_datetime = xb.num2date(self.data.datetime[0])
        if ((current_datetime.hour == 9 and current_datetime.minute < 40) or
                (current_datetime.hour == 13 and current_datetime.minute < 1)):
            return

        if current_datetime.second % 3 != 0:
            return

        pos = self.get_position(self.data)
        inventory = pos.size

        if (current_datetime.hour == 14 and current_datetime.minute >= 55) or current_datetime.hour == 15:
            for o in self.get_pending_orders().get(self.data._dataname, []):
                self.cancel(o)

        px = (self.data.bid1price[0] + self.data.ask1price[0]) / 2  # 股票现价（中间价）
        # s = self.data.ask1price[0] - self.data.bid1price[0]  # 价差（绝对值）
        buy_px = px - self.gap_pct * px / 2
        sell_px = px + self.gap_pct * px / 2

        order_choices = [[buy_px, self.trade_size], [sell_px, self.trade_size]]
        px_move = self.gap_pct * px / 4

        if inventory > 0:
            order_choices[0][0] -= px_move
            order_choices[1][0] -= px_move
            order_choices[1][1] = self.trade_size + abs(inventory)
        elif inventory < 0:
            order_choices[0][0] += px_move
            order_choices[1][0] += px_move
            order_choices[0][1] = self.trade_size + abs(inventory)
        
        # 超时未成交订单直接撤单
        for order in self.get_pending_orders().setdefault(self.data._dataname, {}):
            # 超过10s撤单
            if order.ref == 3343:
                aa = 1
            if (xb.num2date(order.data.datetime[0])-xb.num2date(order.created.dt)).total_seconds() >=10:
                self.cancel(order)

        nowtime = str(xb.num2time(self.datas[0].datetime[0]))

        # self.buy(self.data, price=float(round(order_choices[0][0], 2)), size=int(order_choices[0][1]),
        #          exectype=xb.Order.Limit)
        # self.sell(self.data, price=float(round(order_choices[1][0], 2)), size=int(order_choices[1][1]),
        #           exectype=xb.Order.Limit)
        
        order1 = self.buy(self.data, price=float(self.datas[0].bid1price[0]), size=int(order_choices[0][1]),
                 exectype=xb.Order.Limit)
        order2 = self.sell(self.data, price=float(self.datas[0].ask1price[0]), size=int(order_choices[1][1]),
                  exectype=xb.Order.Limit)
        
        # for symbol in self.get_pending_orders():
        #     orders = self.get_pending_orders()[symbol]
        #     for order in orders:
        #         if order.queue > 0:
        #             print(order.queue, order.queue_count)

        return

    def stop(self):
        self.log('End of backtest. Final value: {}'.format(self.get_value()), level="info")
