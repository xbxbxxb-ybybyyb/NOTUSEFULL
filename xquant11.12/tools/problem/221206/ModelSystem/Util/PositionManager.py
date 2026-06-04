"""
头寸管理器
by 011478
"""
from Exchange.Order import Order


class PositionManager:
    def __init__(self):
        self.__targetQty = {}  # key = symbol, value = quantity
        self.__netPosition = {}  # key = symbol, value = quantity
        self.__nonFinishedOrder = {}  # key = symbol, value = orderNumber
        self.__pre_volume = {}  # key = orderNumber, value = volume
        self.__finishedOrders = {}  # key = symbol, value = LIST of ExchangeOrders, not used so far

    def __initPositionSingle(self, symbol, quantity):
        """
        初始化单个股票持仓
        :param symbol: 股票代码
        :param quantity: 期初持仓
        :return: void
        """
        # if symbol in self.__initQty:
        #     print("Overwriting the quantity in the position manager where symbol already is!")

        # 在相应字段的字典中，加入symbol
        self.__targetQty[symbol] = quantity
        self.__netPosition[symbol] = 0
        self.__finishedOrders[symbol] = []  # the value is a list

    def __initPositionList(self, symbolList, quantityList):
        """
        初始化股票持仓
        :param symbolList: 股票代码list
        :param quantityList:  股票代码对应的底仓数量list
        :return: void
        """
        if len(symbolList) == len(quantityList):
            for i in range(len(symbolList)):
                self.initPosition(symbolList[i], quantityList[i])
        else:
            raise Exception("The dimensions of the two arguments did not match!")

    def initPosition(self, symbol, quantity):
        if isinstance(symbol, list):
            self.__initPositionList(symbol, quantity)
        else:
            self.__initPositionSingle(symbol, quantity)

    def updatePosition(self, exchangeOrder):
        if isinstance(exchangeOrder, Order):
            status = exchangeOrder.order_status
            # 订单终结
            if status == 'cancelled' or status == 'filled' or status == 'partially cancelled':
                self.__processFinishedOrder(exchangeOrder)
            else:
                self.__processNonFinishedOrder(exchangeOrder)
        else:
            raise Exception("The argument is not an instance of ExchangeOrder!")

    def onNewOrder(self, symbol, orderNumber):
        self.__nonFinishedOrder.update({symbol: orderNumber})
        self.__pre_volume.update({orderNumber: 0})

    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    # helper functions
    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    def __processOrder(self, exchangeOrder):
        if exchangeOrder.order_number not in self.__pre_volume:
            print('There is no such order number in the nonFinishedOrder!')
            return
        else:
            preVolume = self.__pre_volume[exchangeOrder.order_number]
        dVolume = exchangeOrder.volume_executed - preVolume
        if exchangeOrder.direction == 'B':
            self.__netPosition[exchangeOrder.code] += dVolume
        elif exchangeOrder.direction == 'S':
            self.__netPosition[exchangeOrder.code] -= dVolume

    def __processNonFinishedOrder(self, exchangeOrder):
        self.__processOrder(exchangeOrder)
        self.__pre_volume.update({exchangeOrder.order_number: exchangeOrder.volume_executed})

    def __processFinishedOrder(self, exchangeOrder):
        self.__processOrder(exchangeOrder)
        self.__finishedOrders.get(exchangeOrder.code).append(exchangeOrder)
        self.__nonFinishedOrder.pop(exchangeOrder.code, None)
        self.__pre_volume.pop(exchangeOrder.order_number, None)


    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    # getters
    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    def getNetPosition(self, symbol):
        """
        获取净头寸
        :param symbol: 股票代码
        :return: 该股票代码的净头寸
        """
        if symbol not in self.__netPosition:
            return 0
        return int(self.__netPosition.get(symbol))

    # def getCalNetPosition(self, symbol):
    #     """
    #     获取向下取100的整数倍的净头寸
    #     即，不含零股的净头寸
    #     建议始终用该方法获取净头寸！
    #     :param symbol: 股票代码
    #     :return: 该股票代码的向下取100整数倍的净头寸
    #     """
    #     if symbol not in self.__netPosition:
    #         return 0
    #     return math.floor(self.__netPosition.get(symbol) / 100) * 100

    def getNonFinishedOrderNumber(self, symbol):
        """
        获取未终结订单ID，如果没有该symbol，则返回None
        :param symbol: 股票代码
        :return: 该股票代码的未终结订单ID
        """
        return self.__nonFinishedOrder.get(symbol)

    def getFinishedOrders(self, symbol):
        """
        获取终结订单，返回值为一个list
        :param symbol: 股票代码
        :return: 该股票代码的终结订单，以list形式存储
        """
        return self.__finishedOrders.get(symbol)

    def getTargetQty(self, symbol):
        if symbol not in self.__targetQty:
            return 0
        return self.__targetQty.get(symbol)

    def hasNonFinished(self, symbol):
        if symbol in self.__nonFinishedOrder:
            return True
        else:
            return False
