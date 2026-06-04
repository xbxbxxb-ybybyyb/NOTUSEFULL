class Order:
    """
    订单类
    """

    def __init__(self, code, order_price, order_volume, direction, order_time, signal_type, market_vwap, strategy_vwap,
                 ema_volume, quote_volume):
        """
        :param code: str 股票代码
        :param order_price: float 下单价格
        :param order_volume: int 下单量
        :param direction: str 下单方向 "B" or "S"
        :param order_time: float 下单的timestamp
        :param signal_type: SignalType 触发这个订单的信号的类型，分为aggressive, passive, supplement, other
        """

        # 原始订单的属性
        self.code = code
        self.price = order_price
        self.volume = order_volume
        self.direction = direction
        self.order_time = order_time
        self.signal_type = signal_type

        # 交易所订单新增属性
        self.order_number = None  # 交易所订单编号
        self.order_status = None  # 交易所订单状态
        self.last_update_time = None  # 上次更新交易所订单的时间
        self.is_opposite = None  # 挂单价格是否在对方盘口
        self.is_opposite_previous = None  # 挂单价格在上一个tick是否在对方盘口
        self.queue = None  # 在下单价格所处队列中的位置
        self.is_first_drive = True  # 订单是否是第一次驱动
        self.is_back = False  # 订单是否被撤
        self.volume_executed = 0  # 已成交的量
        self.amount_executed = 0  # 已成交的金额
        self.duration = 0  # 订单在交易所持续的时间

        # 测试属性
        self.market_vwap = market_vwap
        self.strategy_vwap = strategy_vwap
        self.ema_volume = ema_volume
        self.quote_volume = quote_volume

    def update_order_status(self):
        """
        更新订单状态
        """
        if self.volume_executed == 0:
            if self.is_back:
                self.order_status = "cancelled"
            else:
                self.order_status = "new"
        elif self.volume_executed < self.volume:
            if self.is_back:
                self.order_status = "partially cancelled"
            else:
                self.order_status = "partially filled"
        else:
            self.order_status = "filled"
