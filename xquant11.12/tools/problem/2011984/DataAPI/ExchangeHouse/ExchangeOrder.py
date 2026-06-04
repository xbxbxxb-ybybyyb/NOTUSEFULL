class ExchangeOrder:
    def __init__(self, order, isback=False):
        """
        订单的状态，适用于查询和返回
        """
        self.orderType = order.orderType
        self.bfbList = order.bfbList
        self.mcjList = order.mcjList
        self.orderNumber = order.orderNumber
        self.code = order.code
        # 成交总金额
        self.accMount = 0
        # 成交的量
        self.volume = 0
        # 最近一次的更新时间（下单，查找，撤单）
        self.lastUpdateTime = order.orderTime
        # 下单时设定价格
        self.setPrice = order.price
        # 下单时设定的量
        self.setVolume = order.volume
        self.BSFlag = order.BSFlag
        # 挂在我们前面的单子有多少
        self.queue = 0
        self.orderTime = order.orderTime
        # 是否发送了订单指令
        self.isback = isback
        # 是否在交易所挂出来等待成交撮合.这个主要是解决更新时间不同步的问题
        # 例如
        self.ishold = False

    def price(self):
        if self.volume == 0:
            return 0
        else:
            return self.accMount / self.volume

    def order_state(self):
        # 判断订单的状态。
        orderstate = ''
        if self.volume == 0 and self.setVolume != 0:
            if self.isback:
                orderstate = 'cancelled'
            else:
                orderstate = 'new'
        if self.volume != 0 and self.volume < self.setVolume:
            if self.isback:
                orderstate = 'partially_cancelled'
            else:
                orderstate = 'partially_filled'
        if self.volume != 0 and self.setVolume == self.volume:
            orderstate = 'filled'
        return orderstate
