"""
头寸管理器
by 011478
"""
from ExchangeHouse.ExchangeOrder import ExchangeOrder
import copy
import math


class PositionManager:
    def __init__(self):
        self.__initQty = {}  # key = symbol, value = quantity
        self.__buyAvailQty = {}  # key = symbol, value = quantity
        self.__sellAvailQty = {}  # key = symbol, value = quantity
        self.__netPosition = {}  # key = symbol, value = quantity
        self.__nonFinishedOrder = {}  # key = symbol, value = ExchangeOrder
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
        self.__initQty[symbol] = quantity
        self.__buyAvailQty[symbol] = quantity
        self.__sellAvailQty[symbol] = quantity
        self.__netPosition[symbol] = 0
        self.__nonFinishedOrder[symbol] = None
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
        if isinstance(exchangeOrder, ExchangeOrder):
            status = exchangeOrder.order_state()  # new, filled, partially_filled, cancelled, partially_cancelled
            # 订单终结
            if status == 'cancelled' or status == 'filled' or status == 'partially_cancelled':
                self.__processFinishedOrder(exchangeOrder)
            else:
                self.__processNonFinishedOrder(exchangeOrder)
        else:
            raise Exception("The argument is not an instance of ExchangeOrder!")

    def isPositionClosed(self, symbol):
        if symbol not in self.__netPosition:
            return True
        #  考虑零股
        # if 0 <= self.__netPosition.get(symbol) < 100:
        #     return True
        # else:
        #     return False
        # 不考虑零股
        if int(self.__netPosition.get(symbol)) != 0:
            return False
        else:
            return True

    def isPositionPositive(self, symbol):
        if symbol not in self.__netPosition:
            return False
        if self.getNetPosition(symbol) > 0:
            return True
        else:
            return False

    def isPositionNegative(self, symbol):
        if symbol not in self.__netPosition:
            return False
        if self.getNetPosition(symbol) < 0:
            return True
        else:
            return False

    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    # helper functions
    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    def __processOrder(self, exchangeOrder):
        preVolume = 0
        preOrder = self.__nonFinishedOrder.get(exchangeOrder.code)
        if preOrder is not None:
            #  make sure they are the same order
            if preOrder.orderNumber == exchangeOrder.orderNumber:
                preVolume = preOrder.volume
            else:
                print('There is no such order number in the nonFinishedOrder!')
                return
        dVolume = exchangeOrder.volume - preVolume
        if exchangeOrder.BSFlag == 'B':
            self.__netPosition[exchangeOrder.code] += dVolume
            self.__buyAvailQty[exchangeOrder.code] -= dVolume
        elif exchangeOrder.BSFlag == 'S':
            self.__netPosition[exchangeOrder.code] -= dVolume
            self.__sellAvailQty[exchangeOrder.code] -= dVolume

    def __processNonFinishedOrder(self, exchangeOrder):
        self.__processOrder(exchangeOrder)
        self.__nonFinishedOrder[exchangeOrder.code] = copy.deepcopy(exchangeOrder)

    def __processFinishedOrder(self, exchangeOrder):
        self.__processOrder(exchangeOrder)
        self.__finishedOrders.get(exchangeOrder.code).append(exchangeOrder)
        self.__nonFinishedOrder.pop(exchangeOrder.code, None)


    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    # getters
    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    def getBuyAvailQty(self, symbol):
        """
        获取买入可用额度
        :param symbol: 股票代码
        :return: 该股票代码的买入可用额度
        """
        if symbol not in self.__buyAvailQty:
            return 0
        return self.__buyAvailQty.get(symbol)

    def getSellAvailQty(self, symbol):
        """
        获取卖出可用额度
        :param symbol: 股票代码
        :return: 该股票代码的卖出可用额度
        """
        if symbol not in self.__sellAvailQty:
            return 0
        return self.__sellAvailQty.get(symbol)

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

    def getNonFinishedOrder(self, symbol):
        """
        获取未终结订单，如果没有该symbol，则返回None
        :param symbol: 股票代码
        :return: 该股票代码的未终结订单
        """
        return self.__nonFinishedOrder.get(symbol)

    def getFinishedOrders(self, symbol):
        """
        获取终结订单，返回值为一个list
        :param symbol: 股票代码
        :return: 该股票代码的终结订单，以list形式存储
        """
        return self.__finishedOrders.get(symbol)

    def getInitialQty(self, symbol):
        if symbol not in self.__initQty:
            return 0
        return self.__initQty.get(symbol)

    def hasNonFinished(self, symbol):
        if symbol not in self.__nonFinishedOrder or self.__nonFinishedOrder.get(symbol) is None:
            return False
        else:
            return True

    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    # setter
    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    def setBuyAvailQty(self, quantity):
        self.__buyAvailQty = quantity

    def setSellAvailQty(self, quantity):
        self.__sellAvailQty = quantity


