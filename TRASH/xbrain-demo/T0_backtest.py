# -*- coding: utf-8 -*-
from xbrain import XBrain
import xbrain as xb
from xbrain.strategy_base import StrategyBase
import pandas as pd
import numpy as np
import time
from collections import defaultdict


class StrategySignalT0(StrategyBase):  # 策略类需继承 StrategyBase 基类
    # 策略涉及的参数在 params 中定义，通过 self.params.p1 访问
    params = (
        ('stoploss', 0.1),  # 止损比例
        ('takeprofit', 0.1),  # 止盈比例
        ('tradesize', 300),  # 每笔交易股数
        ('period', 120),  # SMA参数
        ('ema_period', 20),  # ema参数
        ('init_open_long_th', 0.7),
        ('init_open_short_th', 0.7),
        ('init_close_long_th', 0.7),
        ('init_close_short_th', 0.7),
        ('STOP_LOSS_TH', 0.02),  # 止损的阈值
        ('UNIT_QTY_PER_ORDER', 10000)  # 标准每笔委托的成交笔数, 根据股票成交是否活跃设置
    )

    def __init__(self):
        self.close = self.datas[0].close
        self.sma = xb.talib.SMA(  # 调用 xbrain 集成的 talib 因子计算功能，计算短期 SMA 值
            self.data.close, timeperiod=self.params.period  # 指定 SMA 参数为 self.params.period
        )
        # sjl 实时数据播放时，ema怎么计算？跨天计算
        self.ema_vol = xb.talib.EMA(self.data.volume, timeperiod=self.params.ema_period)

    def start(self):
        # 新的一天重置策略
        self.reset_on_new_day()

    def _calc_ema(self, arr, alpha=0.75, window=5):
        if len(arr) == 0:
            return 0
        else:
            start_idx = max(0, len(arr) - window)
            ema = arr[start_idx]
            for a in arr[start_idx:]:
                ema = (1 - alpha) * ema + alpha * a
            return ema

    def reset_on_new_day(self):
        self.signal_long = np.array([])
        self.signal_short = np.array([])
        self.signal_long_delta = np.array([0.0])
        self.signal_short_delta = np.array([0.0])

        self.open_long_th = 0.0
        self.open_short_th = 0.0
        self.close_long_th = 0.0
        self.close_short_th = 0.0
        self.open_long_time = 0  # 以多头开仓的次数
        self.i = 0

        self.set_init_position()
        self._set_init_open_close_th()

        self.net_position = defaultdict(int)  # 相对于底仓的持仓变化值,负值表示空头

    def set_init_position(self):
        # 记录初始底仓，即初始的多头持仓
        self.init_position = {}
        positions = self.get_open_position()
        for security in positions:
            self.init_position[security] = positions[security].size

    def _set_init_open_close_th(self):
        # 设置初始信号阈值
        self.init_open_long_th = self.p.init_open_long_th
        self.init_open_short_th = self.p.init_open_short_th
        self.init_close_long_th = self.p.init_close_long_th
        self.init_close_short_th = self.p.init_close_short_th

    def get_up_down_limit(self, stock):
        # 获取涨跌停
        return 0.195 if stock.startswith('3') or stock.startswith('68') else 0.095

    def notify_order(self, order):
        super().notify_order(order)

        if order.status in [order.Partial, order.Completed]:
            if order.order_records:
                pass
            stock = order.data.getdataname()
            position = self.get_position_by_name(stock)
            # 订单成交时，更新净持仓
            if not position:
                pass
            else:
                self.net_position[stock] = position.size - self.init_position[stock] if self.init_position.get(stock,
                                                                                                               0) else position.size
        if order.status in [order.Canceled]:
            if isinstance(self.broker.p.filler, xb.broker.fillers.TradeMocker):
                #模拟撮合内部维护了一套订单，需和xbrain同步撤单
                self.broker.p.filler.cancel_inner()

    def process_openning_signal(self, stock, price_df):
        # 根据信号和行情下单逻辑
        last_price_df = price_df[stock].iloc[-1]
        signal_long = self.signal_long[-1]
        signal_short = self.signal_short[-1]

        if self.net_position[stock] == 0:  # price_df.iloc[-1].loc['ClosePx']
            # 空仓时
            if signal_long > self.init_open_long_th:
                # 开多
                self.open_long_th = signal_long  # 上一次开仓的阈值
                # sjl delta, buyside为signal_long_delta[-1]
                delta = self.signal_long_delta[-1]
                vol_ratio = signal_long / (self.init_open_long_th + 0.1) * delta / (self.open_long_time + 1)
                price = 1.0002 * last_price_df.ask1price
                size = int(min(self.ema_vol[0] * 1.5,
                               max(self.ema_vol[0] * 0.5, last_price_df.bid1qty),
                               self.p.UNIT_QTY_PER_ORDER * (1 + 10 * vol_ratio)
                               ))
                self.buy(price=price, size=int(size), exectype=xb.Order.Limit)
                self.log("init_open_long_th: signal long {}, price {}, volume {}!".format(signal_long, price, size))
                self.open_long_time = self.open_long_time + 1
            elif signal_short < self.init_open_short_th:
                # 开空
                pass
            else:
                # 不动
                pass
        else:
            # 已有持仓时
            if self.net_position[stock] > 0:
                # 已有多头持仓
                # sjl 持仓的平均成交价格,6.2 Position - 持仓类, price_orig累计开仓成本
                if signal_long > self.open_long_th + 0.1 * self._calc_ema(
                        self.signal_long_delta) and signal_long > self.init_open_long_th:
                    # 若singnal_long连续增强，连续开仓阈值增大
                    # 连续开多
                    self.open_long_th = self.open_long_th + self._calc_ema(self.signal_long_delta)
                    price = 1.0002 * last_price_df.ask1price
                    size = -self.net_position[stock] + min(20 * self.p.UNIT_QTY_PER_ORDER,
                                                           max(4 * self.ema_vol, 5 * self.p.UNIT_QTY_PER_ORDER)
                                                           )
                    self.buy(price=price, size=int(size), exectype=xb.Order.Limit)
                    self.log("continuous open_long_th: signal_long {}: price {}, volume {}!".format(signal_long, price,
                                                                                                    size))

                elif signal_short < self.init_close_long_th:
                    # 部分平仓
                    if not self.close_long_th or signal_short < self.close_long_th - 0.1 * self.signal_long_delta(
                            self.signal_short_delta):
                        # 若signal_short连续增强（不一定是连续增强，取的是相邻两次信号差值的绝对值），连续平仓阈值增大
                        # sjl，为避免无法平仓，设置门槛阈值，达到就可平仓，门槛阈值比初始阈值稍高
                        # sjl? close_long?而不是close_short
                        price = 1.0002 * last_price_df.bid1price
                        size = min(self.net_position[stock],
                                   2.5 * self.ema_vol,
                                   10 * self.p.UNIT_QTY_PER_ORDER
                                   )
                        self.sell(price=price, size=int(size), exectype=xb.Order.Limit)
                        self.log(
                            "continuous close_long_th: signal_short {}: price {}, volume {}!".format(signal_short,
                                                                                                     price,
                                                                                                     size))
                else:
                    # 保持现有仓位
                    pass
            else:
                # 已有空头持仓
                pass

    def process_morning_close(self, stock, price_df):
        last_price_df = price_df[stock].iloc[-1]
        size = min(max(self.ema_vol[0], abs(self.net_position[stock] / 5)),
                   abs(self.net_position[stock]))
        if self.net_position[stock] > 0:
            price = last_price_df.bid1price  # 买一价挂单，若要挂激进价格，可设置为max(ask1price,-0.02, bid1price)
            self.sell(price=price, size=int(size), exectype=xb.Order.Limit)
            self.log("process_morning_close: signal short {}, price {}, volume {}!".format(self.signal_short[-1], price,
                                                                                           size))
        elif self.net_position[stock] < 0:
            price = last_price_df.ask1price
            self.buy(price=price, size=int(size), exectype=xb.Order.Limit)
            self.log(
                "process_morning_close: signal long {}, price {}, volume {}!".format(self.signal_long[-1], price, size))

    def process_up_down_limit_close(self, stock, price_df):
        # ajl临近涨跌停处理，卖不掉怎么撤单？
        last_price_df = price_df[stock].iloc[-1]
        if not self.net_position[stock]:
            return
        if last_price_df.close > last_price_df.preclose:
            price = last_price_df.maxpx
        else:
            price = last_price_df.minpx
        size = abs(self.net_position[stock])

        if self.net_position[stock] > 0:
            self.sell(price=price, size=int(size), exectype=xb.Order.Limit)
            self.log(
                "process_up_down_limit_close: signal sell {}, price {}, volume {}!".format(self.signal_long[-1], price,
                                                                                           size))
        else:
            self.buy(price=price, size=int(size), exectype=xb.Order.Limit)
            self.log(
                "process_up_down_limit_close: signal long {}, price {}, volume {}!".format(self.signal_long[-1], price,
                                                                                           size))

    def check_stop_loss(self, stock, price_df):
        #当订单到达止损线时，撤单
        last_price_df = price_df[stock].iloc[-1]
        pending_orders = self.get_pending_orders().setdefault(stock, {})
        stop_loss_flag = False
        if pending_orders:
            # 止损撤单，不用stoplimit订单代替，stoplimit会按开高收低成交
            # 每个标的最多有一笔在途订单
            for order in pending_orders:
                if order.isbuy():
                    curr_price = last_price_df.ask1price if last_price_df.ask1price else last_price_df.bid1price
                    if order.created.price < last_price_df.bid1price and last_price_df.bid1price != 0 or \
                            order.executed.price * (1 - self.p.STOP_LOSS_TH) >= curr_price and order.executed.price!=0.0:
                        stop_loss_flag = True
                if order.issell():
                    curr_price = last_price_df.bid1price if last_price_df.bid1price else last_price_df.ask1price
                    if order.created.price > last_price_df.ask1price and last_price_df.ask1price != 0 or \
                            order.executed.price * (1 + self.p.STOP_LOSS_TH) <= curr_price and order.executed.price!=0.0:
                        stop_loss_flag = True
            self.log(
                "check_stop_loss: signal short {}, order.ref {}, order.created.price {}, order.created.size {} , order.executed.price {},  order.executed.size {}!".format(
                    self.signal_short[-1], order.ref, order.created.price, order.created.size, order.executed.price, order.executed.size))
            return stop_loss_flag
        else:
            return True


    def next(self):
        #TODO： 加上行情valid的校验
        if self.i == 1000:
            return
        self.i = self.i + 1

        stock = self.datas[0]._name
        nowtime = xb.num2time(self.datas[0].datetime[0]).strftime('%H:%M:%S')
        # 传入标的查询行情数据
        price_df = self.get_past_feed_price_df(datanames=stock, lagged_bar=1)
        last_price_df = price_df[stock].iloc[-1]
        price_df[stock].to_pickle("/home/appadmin/price_df.pkl")

        # 查询信号数据
        import random
        random.seed(0)
        signal_long = random.uniform(0.60, 0.80)
        signal_short = random.uniform(-1, -0.50)
        ###########################################
        self.signal_long = np.append(self.signal_long, signal_long)
        self.signal_short = np.append(self.signal_short, signal_short)
        self.signal_long_delta = np.append(self.signal_long_delta, np.abs(signal_long - self.signal_long_delta[-1]))
        self.signal_short_delta = np.append(self.signal_short_delta, np.abs(signal_short - self.signal_short_delta[-1]))

        ################################################################
        # sjl新一天开始后，重置持仓，信号。重置持仓后收益率怎么计算？xbrain 不支持，可以单天单天计算
        # if '11:29:00'> nowtime >= '09:30:00' or '14:55:00'> nowtime >= '13:00:00':
        #     self.process_openning_signal(stock, price_df)
        # elif '11:30:00'>= nowtime >= '11:29:00':
        #     #上午收盘平仓, 且不发开仓单
        #     self.process_morning_close(stock, price_df)
        # elif '14:57:00'> nowtime >= '14:55:00':
        #     pass
        # else:
        #     pass
        # PnlComm去除手续费后的收益
        trades = self.get_trades_by_name(stock)  # 获取标的持仓
        orders = self.get_orders_by_name(stock)

        if last_price_df.close/ last_price_df.preclose-1>= self.get_up_down_limit(stock) or \
                last_price_df.preclose/last_price_df.close -1 >= self.get_up_down_limit(stock):
            self.process_up_down_limit_close(stock, price_df)

        if '09:40:00' > nowtime >= '09:30:00' or '14:55:00' >= nowtime >= '13:00:00':
            stop_loss_flag = self.check_stop_loss(stock, price_df)
            if stop_loss_flag:
                for order in self.get_pending_orders().setdefault(stock, {}):
                    self.cancel(order)
            else:
                # 继续等待未完成的订单成交，不下新单
                return
            self.process_openning_signal(stock, price_df)
        elif '09:36:00' >= nowtime >= '09:35:00':
            # 上午收盘平仓, 且不发开仓单
            # self.process_morning_close(stock, price_df)
            pass
        elif '14:57:00' > nowtime >= '14:55:00':
            pass
        else:
            pass
        return

    def stop(self):
        self.log('End of backtest. Final value: {}'.format(self.get_value()))


if __name__ == '__main__':
    # 创建回测框架 XBrain 实例
    stock = '000002.SZ'
    start_date = "20180806 093000000"
    end_date = "20180806 105959000"

    brain = XBrain(start_date=start_date, end_date=end_date, live=False, init_amount=10000000, commission=0.0, slippage_multi=0.0)
    ####################################################################

    # 加载回测期内的标的数据到回测框架
    brain.add_feeds(
        datanames=stock,  # 标的名称，需符合数据科学量化研究平台标的命名规范
        time_frame="TICK",  # 回测频度
        instrument_type='STOCK',  # 标的品种，枚举变量，可选有 STOCK, FUTURE
    )
    # df = pd.read_pickle("/home/appadmin/price_df.pkl").reset_index()
    # df = df.rename(columns = {'open':'Open', 'high':'High','low': 'Low', 'close':'Close', 'volume':'Volume'})
    # brain.add_data(df=df, dataname=stock, time_frame='TICK', instrument_type='STOCK')

    ####################################################################

    # 设置底仓，支持多标的添加多次
    if True:
        from xquant.factordata import FactorData

        fa = FactorData()
        trading_days = fa.tradingday(start_date[:8], end_date[:8])
        price = fa.get_factor_value('Basic_factor', [stock], [trading_days[0]], ['close']).iloc[0, 0]
        brain.add_initial_position(symbol=stock, size=10000, price=price)
    else:
        from tquant import StockData, BasicData

        sd = StockData()
        bd = BasicData()
        trading_days = bd.get_trading_day(start_date[:8], end_date[:8])

        # SJL 合理设置底仓数量
        price = sd.get_factor_price_daily([stock], trading_days[0], ["close"]).iloc[0, 0]
        # print("stock {}, price: {}.".format(stock, price))
        brain.add_initial_position(symbol=stock, size=10000, price=price)

    # 设置撮合模式
    # 根据需要，自定义撮合时的目标价，普通模式有两种，NEXT_OPEN，与THIS_CLOSE
    # brain.set_fill_method(fill_method='TRADE_MOCKER', mocker_type="NORMAL")
    brain.set_fill_method(fill_method='PERCENT', fill_price="NEXT_OPEN")

    # 加载策略到回测框架，此处策略类是用户需要重点关注，并实现的
    brain.add_strategy(StrategySignalT0)
    ####################################################################

    # 运行回测
    brain.backtest_run()
    ####################################################################

    # 生成回测报告
    # param:
    # - plot: 是否绘图，True 绘制，False 不绘图
    # - plotname: 绘图名称
    brain.generate_report(plot=False, plotname="StrategySignalT0")

    # 获取Analyzers分析的结果
    trade_summary, trade_records, daily_pnl = brain.get_analyzer_result()
    print(trade_summary.head())
    print(trade_records)
    print(daily_pnl.head())

