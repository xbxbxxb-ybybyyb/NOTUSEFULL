"""
Handles the output in SignalEvaluate
Use "addOrder" when an order is finished
Use "registerOutput" when position is closed: to integrate one trading deal
Get the info you want, then output the results

by 011478

@revise: 011478
on 20180910: 将多空翻转的交易，从统计中拆开（策略中仍为一笔订单），e.g. 多空，在统计输出时拆为多平和开空两笔订单
on 20181022: 加入去掉最大最小盈利交易日的API
"""
import math
import datetime as dt
from typing import Dict, Tuple


class OutputManager:
    def __init__(self, cost, truncated: bool=False):
        self.__nonClosedOrderDict = {}  # 存入没有平仓的order; key = symbol, value = list
        self.__orderDict = {}  # key = symbol, value = list
        self.__detailedOrderDict = {}  # key = symbol, value = list
        self.__totalProfitDict: Dict[str, Dict[dt.date, float]] = {}  # key = symbol, value = dict{ key = date, value = float}
        self.__dailyInfoDict = {}  # key = symbol, value = dict: key = date, value = DailyInfo
        self.__cumOpenAmount: Dict[str, Dict[dt.date, float]] = {}  # key = symbol, value = dict{key = date, value = float}
        self.__dayCounts = {}  # key = symbol, value = int
        self.__trading_days_set = set()
        self.__splited_cum_qty = {}  # key = symbol, value = tuple: closed position and open position
        self.__COST = cost
        self.__truncated = truncated
        self.__maxProfit: Tuple[str, float] = None  # 获利最多日
        self.__minProfit: Tuple[str, float] = None  # 获利最少日
        self.__afterCostEarnings: Dict[str, Dict[dt.date, float]] = {}  # 净利润 key = symbol, value = dict{ key = date, value = float}

    def clearNonClosed(self, symbol):
        if symbol not in self.__detailedOrderDict:
            self.__detailedOrderDict.update({symbol: []})
        self.__updateDetailed(symbol)
        self.__nonClosedOrderDict.update({symbol: []})

    def addOrder(self, exchangeOrder, split_reversed_cum_qty):
        symbol = exchangeOrder.code
        if symbol not in self.__nonClosedOrderDict:
            self.__nonClosedOrderDict.update({symbol: []})
        self.__nonClosedOrderDict.get(symbol).append(exchangeOrder)
        if split_reversed_cum_qty is not None:
            self.__splited_cum_qty.update({exchangeOrder.orderNumber: split_reversed_cum_qty})
            self.__doOutput(symbol, exchangeOrder.orderTime.timestamp())
            self.__nonClosedOrderDict.get(symbol).append(exchangeOrder)

    def registerOutput(self, symbol, startTimeStamp):
        if symbol not in self.__nonClosedOrderDict or len(self.__nonClosedOrderDict.get(symbol)) == 0:
            return
        else:
            self.__doOutput(symbol, startTimeStamp)

    def __doOutput(self, symbol, startTimeStamp):
        if symbol not in self.__orderDict:
            self.__orderDict.update({symbol: []})
        if symbol not in self.__detailedOrderDict:
            self.__detailedOrderDict.update({symbol: []})
        size = len(self.__nonClosedOrderDict.get(symbol))
        # make sure there are two directions
        process = False
        direction = self.__nonClosedOrderDict.get(symbol)[0].BSFlag
        for i in range(size):
            if self.__nonClosedOrderDict.get(symbol)[i].BSFlag != direction:
                process = True
                break
        if not process:
            self.clearNonClosed(symbol)
            return

        # update the self.__orderDict
        sumOpenAmountCum = 0
        sumOpenAmountOrder = 0
        sumCloseAmount = 0
        sumOpenVolume = 0
        sumCloseVolume = 0
        tempOrder = {}
        for i in range(size):
            exchangeOrder = self.__nonClosedOrderDict.get(symbol)[i]
            if i == 0:
                tempOrder.update({'code': symbol})
                tempOrder.update({'startTime': exchangeOrder.orderTime.strftime('%m/%d/%y-%H:%M:%S')})
                if direction == 'B':
                    tempOrder.update({'direction': 'long '})
                else:
                    tempOrder.update({'direction': 'short'})
                tempOrder.update({'startPrice': exchangeOrder.setPrice})
                if exchangeOrder.orderNumber in self.__splited_cum_qty:
                    cum_qty_close = self.__splited_cum_qty.get(exchangeOrder.orderNumber)[0]
                    cum_qty_open = self.__splited_cum_qty.get(exchangeOrder.orderNumber)[1]
                    sumOpenAmountCum += cum_qty_open * exchangeOrder.price()
                    sumOpenAmountOrder += exchangeOrder.setPrice * (exchangeOrder.setVolume - cum_qty_close)
                    sumOpenVolume += cum_qty_open
                else:
                    sumOpenAmountCum += exchangeOrder.accMount
                    sumOpenAmountOrder += exchangeOrder.setPrice * exchangeOrder.setVolume
                    sumOpenVolume += exchangeOrder.volume
            elif i == size - 1:
                tempOrder.update({'endPrice': exchangeOrder.setPrice})
                tempOrder.update({'endTime': exchangeOrder.orderTime.strftime('%m/%d/%y-%H:%M:%S')})
                if exchangeOrder.BSFlag == direction:
                    if exchangeOrder.orderNumber in self.__splited_cum_qty:
                        cum_qty_close = self.__splited_cum_qty.get(exchangeOrder.orderNumber)[0]
                        sumOpenAmountCum += cum_qty_close * exchangeOrder.price()
                        sumOpenAmountOrder += exchangeOrder.setPrice * cum_qty_close
                        sumOpenVolume += cum_qty_close
                    else:
                        sumOpenAmountCum += exchangeOrder.accMount
                        sumOpenAmountOrder += exchangeOrder.setPrice * exchangeOrder.setVolume
                        sumOpenVolume += exchangeOrder.volume
                else:
                    if exchangeOrder.orderNumber in self.__splited_cum_qty:
                        cum_qty_close = self.__splited_cum_qty.get(exchangeOrder.orderNumber)[0]
                        sumCloseAmount += cum_qty_close * exchangeOrder.price()
                        sumCloseVolume += cum_qty_close
                    else:
                        sumCloseAmount += exchangeOrder.accMount
                        sumCloseVolume += exchangeOrder.volume
            else:
                if exchangeOrder.BSFlag == direction:
                    # open side
                    sumOpenAmountCum += exchangeOrder.accMount
                    sumOpenAmountOrder += exchangeOrder.setPrice * exchangeOrder.setVolume
                    sumOpenVolume += exchangeOrder.volume
                else:
                    # close side
                    sumCloseAmount += exchangeOrder.accMount
                    sumCloseVolume += exchangeOrder.volume
        returnInfo = self.__calReturn(symbol, sumOpenAmountCum, sumCloseAmount, direction, startTimeStamp)
        if returnInfo is None:
            self.clearNonClosed(symbol)
            return
        tempOrder.update({'orderAmount': sumOpenAmountOrder})
        tempOrder.update({'cumAmount': sumOpenAmountCum})
        tempOrder.update({'returnRate': returnInfo.returnRate})
        tempOrder.update({'afterCostProfit': returnInfo.afterCostProfit})
        self.__orderDict.get(symbol).append(tempOrder)
        self.clearNonClosed(symbol)

    def __updateDetailed(self, symbol):
        combinedOrder = []
        if symbol not in self.__nonClosedOrderDict or len(self.__nonClosedOrderDict.get(symbol)) == 0:
            return
        else:
            for i in range(len(self.__nonClosedOrderDict.get(symbol))):
                exchangeOrder = self.__nonClosedOrderDict.get(symbol)[i]
                tempOrder = {}
                tempOrder.update({'code': symbol})
                tempOrder.update({'orderTime': exchangeOrder.orderTime.strftime('%m/%d/%y-%H:%M:%S')})
                if exchangeOrder.BSFlag == 'B':
                    tempOrder.update({'direction': 'long '})
                else:
                    tempOrder.update({'direction': 'short'})
                tempOrder.update({'price': exchangeOrder.setPrice})
                tempOrder.update({'avgPrice': exchangeOrder.price()})
                tempOrder.update({'status': exchangeOrder.order_state()})
                if exchangeOrder.orderNumber in self.__splited_cum_qty:
                    if i == 0:
                        cum_qty_close = self.__splited_cum_qty.get(exchangeOrder.orderNumber)[0]
                        cum_qty_open = self.__splited_cum_qty.get(exchangeOrder.orderNumber)[1]
                        tempOrder.update({'quantity': exchangeOrder.setVolume - cum_qty_close})
                        tempOrder.update({'cumQty': cum_qty_open})
                        orderAmount = (exchangeOrder.setVolume - cum_qty_close) * exchangeOrder.setPrice
                        tempOrder.update({'orderAmount': round(orderAmount, 2)})
                        tempOrder.update({'cumAmount': exchangeOrder.price() * cum_qty_open})
                    else:
                        cum_qty_close = self.__splited_cum_qty.get(exchangeOrder.orderNumber)[0]
                        tempOrder.update({'quantity': cum_qty_close})
                        tempOrder.update({'cumQty': cum_qty_close})
                        orderAmount = cum_qty_close * exchangeOrder.setPrice
                        tempOrder.update({'orderAmount': round(orderAmount, 2)})
                        tempOrder.update({'cumAmount': exchangeOrder.price() * cum_qty_close})
                else:
                    tempOrder.update({'quantity': exchangeOrder.setVolume})
                    tempOrder.update({'cumQty': exchangeOrder.volume})
                    orderAmount = exchangeOrder.setVolume * exchangeOrder.setPrice
                    tempOrder.update({'orderAmount': round(orderAmount, 2)})
                    tempOrder.update({'cumAmount': exchangeOrder.accMount})
                combinedOrder.append(tempOrder)
            self.__detailedOrderDict.get(symbol).append(combinedOrder)

    def __calReturn(self, symbol, sumOpenAmountCum, sumCloseAmount, direction, startTimeStamp):
        if symbol not in self.__totalProfitDict:
            self.__totalProfitDict.update({symbol: {}})
        if symbol not in self.__cumOpenAmount:
            self.__cumOpenAmount.update({symbol: {}})
        if symbol not in self.__dailyInfoDict:
            self.__dailyInfoDict.update({symbol: {}})
        if symbol not in self.__afterCostEarnings:
            self.__afterCostEarnings.update({symbol: {}})
        # benchmark = 100
        # openVolumeFloor = self.__floorFun(sumOpenVolume)
        # closeVolumeFloor = self.__floorFun(sumCloseVolume)
        # if openVolumeFloor == 0 and closeVolumeFloor == 0:
        #     return None
        # if openVolumeFloor == 0:
        #     benchmark = closeVolumeFloor
        # elif closeVolumeFloor == 0:
        #     benchmark = openVolumeFloor
        # else:
        #     benchmark = min(openVolumeFloor, closeVolumeFloor)
        # if sumOpenVolume != benchmark:
        #     adjustedOpenAmount = sumOpenAmountCum / sumOpenVolume * benchmark
        # else:
        #     adjustedOpenAmount = sumOpenAmountCum
        # if sumCloseVolume != benchmark:
        #     adjustedCloseAmount = sumCloseAmount / sumCloseVolume * benchmark
        # else:
        #     adjustedCloseAmount = sumCloseAmount
        adjustedOpenAmount = sumOpenAmountCum
        adjustedCloseAmount = sumCloseAmount

        date = dt.datetime.fromtimestamp(startTimeStamp).date()
        self.__trading_days_set.add(date)
        if date not in self.__dailyInfoDict.get(symbol):
            self.__dailyInfoDict.get(symbol).update({date: DailyInfo(0, 0)})
            self.__totalProfitDict.get(symbol).update({date: 0})
            self.__afterCostEarnings.get(symbol).update({date: 0})
            self.__cumOpenAmount.get(symbol).update({date: 0})

        tempCumOpenAmount = self.__cumOpenAmount.get(symbol).get(date)
        tempCumOpenAmount += adjustedOpenAmount
        self.__cumOpenAmount.get(symbol).update({date: tempCumOpenAmount})

        dailyInfo = self.__dailyInfoDict.get(symbol).get(date)
        profit = self.__totalProfitDict.get(symbol).get(date)
        if direction == 'B':
            earning = adjustedCloseAmount - adjustedOpenAmount
            profit += earning
            dailyInfo.dailyProfit += earning
            dailyInfo.dailyOpenAmount += adjustedOpenAmount
            self.__dailyInfoDict.get(symbol).update({date: dailyInfo})
            self.__totalProfitDict.get(symbol).update({date: profit})
            afterCostEarning = earning - self.__COST * adjustedOpenAmount
            # afterCostReturnRate = afterCostEarning / adjustedOpenAmount
            returnRate = round(adjustedCloseAmount / adjustedOpenAmount - 1, 5)
        else:
            earning = adjustedOpenAmount - adjustedCloseAmount
            profit += earning
            dailyInfo.dailyProfit += earning
            dailyInfo.dailyOpenAmount += adjustedOpenAmount
            self.__dailyInfoDict.get(symbol).update({date: dailyInfo})
            self.__totalProfitDict.get(symbol).update({date: profit})
            afterCostEarning = earning - self.__COST * adjustedOpenAmount
            # afterCostReturnRate = afterCostEarning / adjustedOpenAmount
            returnRate = round(1 - adjustedCloseAmount / adjustedOpenAmount, 5)
        # Update the max and min profit, after cost
        if self.__maxProfit is None:
            self.__maxProfit = (date, afterCostEarning)
            self.__minProfit = (date, afterCostEarning)
        else:
            preEarning = self.__afterCostEarnings.get(symbol).get(date)
            tempEarning = preEarning + afterCostEarning
            if tempEarning > self.__maxProfit[1]:
                self.__maxProfit = (date, profit)
            self.__afterCostEarnings.get(symbol).update({date: tempEarning})
            min_key = min(self.__afterCostEarnings.get(symbol), key=self.__afterCostEarnings.get(symbol).get)
            self.__minProfit = (min_key, self.__afterCostEarnings.get(symbol).get(min_key))
        return ReturnInfo(round(afterCostEarning, 2), round(returnRate, 5))

    def __floorFun(self, x):
        return math.floor(x / 100) * 100

    # def getDateCounts(self, symbol):
    #     if symbol not in self.__dailyInfoDict:
    #         return 0
    #     else:
    #         return len(self.__dailyInfoDict.get(symbol).keys())

    def addOneDay(self, symbol):
        if symbol not in self.__dayCounts:
            self.__dayCounts.update({symbol: 1})
        else:
            self.__dayCounts[symbol] += 1

    def getDayCounts(self, symbol):
        if symbol not in self.__dayCounts:
            return 0
        else:
            counts = len(self.__trading_days_set)
            if self.__truncated:
                if counts >= 5:
                    return counts - 2
                else:
                    return counts
            else:
                return counts

    def getProfit(self, symbol):
        if symbol not in self.__totalProfitDict:
            return 0
        else:
            if self.__truncated and len(self.__trading_days_set) >= 5:
                total = 0
                for date in self.__totalProfitDict.get(symbol).keys():
                    if date == self.__maxProfit[0] or date == self.__minProfit[0]:
                        continue
                    else:
                        total += self.__totalProfitDict.get(symbol).get(date)
                return round(total, 2)
            else:
                total = 0
                for value in self.__totalProfitDict.get(symbol).values():
                    total += value
                return round(total, 2)

    def getCumOpenAmount(self, symbol):
        if symbol not in self.__cumOpenAmount:
            return 0
        else:
            if self.__truncated and len(self.__trading_days_set) >= 5:
                total = 0
                for date in self.__cumOpenAmount.get(symbol).keys():
                    if date == self.__maxProfit[0] or date == self.__minProfit[0]:
                        continue
                    else:
                        total += self.__cumOpenAmount.get(symbol).get(date)
                return round(total, 2)
            else:
                total = 0
                for value in self.__cumOpenAmount.get(symbol).values():
                    total += value
                return round(total, 2)

    def getOrder(self, symbol):
        if symbol not in self.__orderDict:
            return []
        else:
            if self.__truncated and len(self.__trading_days_set) >= 5:
                temp = []
                for order in self.__orderDict.get(symbol):
                    date = dt.datetime.strptime(order["startTime"], '%m/%d/%y-%H:%M:%S').date()
                    if date == self.__maxProfit[0] or date == self.__minProfit[0]:
                        continue
                    else:
                        temp.append(order)
                return temp
            else:
                return self.__orderDict.get(symbol)

    def getDetailedOrder(self, symbol):
        if symbol not in self.__detailedOrderDict:
            return []
        else:
            return self.__detailedOrderDict.get(symbol)

    def getDailyProfitDict(self, symbol):
        if symbol not in self.__dailyInfoDict:
            return {}
        else:
            if self.__truncated and len(self.__trading_days_set) >= 5:
                dict = {}
                for date in self.__dailyInfoDict.get(symbol).keys():
                    if date == self.__maxProfit[0] or date == self.__minProfit[0]:
                        continue
                    else:
                        dict.update({str(date): round(self.__dailyInfoDict.get(symbol).get(date).dailyProfit, 2)})
                return dict
            else:
                dict = {}
                for date in self.__dailyInfoDict.get(symbol).keys():
                    dict.update({str(date): round(self.__dailyInfoDict.get(symbol).get(date).dailyProfit, 2)})
                return dict

    def getAfterCostDailyProfitDict(self, symbol):
        if symbol not in self.__dailyInfoDict:
            return {}
        else:
            if self.__truncated and len(self.__trading_days_set) >= 5:
                dict = {}
                for date in self.__dailyInfoDict.get(symbol).keys():
                    if date == self.__maxProfit[0] or date == self.__minProfit[0]:
                        continue
                    else:
                        dailyProfit = self.__dailyInfoDict.get(symbol).get(date).dailyProfit
                        dailyOpenAmount = self.__dailyInfoDict.get(symbol).get(date).dailyOpenAmount
                        afterCostProfit = dailyProfit - self.__COST * dailyOpenAmount
                        dict.update({str(date): round(afterCostProfit, 2)})
                return dict
            else:
                dict = {}
                for date in self.__dailyInfoDict.get(symbol).keys():
                    dailyProfit = self.__dailyInfoDict.get(symbol).get(date).dailyProfit
                    dailyOpenAmount = self.__dailyInfoDict.get(symbol).get(date).dailyOpenAmount
                    afterCostProfit = dailyProfit - self.__COST * dailyOpenAmount
                    dict.update({str(date): round(afterCostProfit, 2)})
                return dict

    def getDailyOpenAmountDict(self, symbol):
        if symbol not in self.__dailyInfoDict:
            return {}
        else:
            if self.__truncated and len(self.__trading_days_set) >= 5:
                dict = {}
                for date in self.__dailyInfoDict.get(symbol).keys():
                    if date == self.__maxProfit[0] or date == self.__minProfit[0]:
                        continue
                    else:
                        dict.update({str(date): round(self.__dailyInfoDict.get(symbol).get(date).dailyOpenAmount, 2)})
                return dict
            else:
                dict = {}
                for date in self.__dailyInfoDict.get(symbol).keys():
                    dict.update({str(date): round(self.__dailyInfoDict.get(symbol).get(date).dailyOpenAmount, 2)})
                return dict

    def getDailyCancelledRatio(self, symbol):
        if symbol not in self.__detailedOrderDict:
            return {}
        else:
            if self.__truncated and len(self.__trading_days_set) >= 5:
                dict = {}
                for orders in self.__detailedOrderDict.get(symbol):
                    for order in orders:
                        date = dt.datetime.strptime(order["orderTime"], '%m/%d/%y-%H:%M:%S').date()
                        if date == self.__maxProfit[0] or date == self.__minProfit[0]:
                            continue
                        else:
                            if str(date) not in dict:
                                dict.update({str(date): (0, 0)})
                            status = order["status"]
                            if 'cancelled' in status:  # cancelled, partially_cancelled
                                temp = list(dict[str(date)])
                                temp[0] += 1
                                dict[str(date)] = tuple(temp)
                            temp = list(dict[str(date)])
                            temp[1] += 1
                            dict[str(date)] = tuple(temp)
                for date in dict.keys():
                    a, b = dict[date]
                    ratio = a / b
                    dict.update({date: ratio})
                return dict
            else:
                dict = {}
                for orders in self.__detailedOrderDict.get(symbol):
                    for order in orders:
                        date = dt.datetime.strptime(order["orderTime"], '%m/%d/%y-%H:%M:%S').date()
                        if str(date) not in dict:
                            dict.update({str(date): (0, 0)})
                        status = order["status"]
                        if 'cancelled' in status:  # cancelled, partially_cancelled
                            temp = list(dict[str(date)])
                            temp[0] += 1
                            dict[str(date)] = tuple(temp)
                        temp = list(dict[str(date)])
                        temp[1] += 1
                        dict[str(date)] = tuple(temp)
                for date in dict.keys():
                    a, b = dict[date]
                    ratio = a / b
                    dict.update({date: ratio})
                return dict

    def getSumCancelledRatio(self, symbol):
        if symbol not in self.__detailedOrderDict:
            return 0
        else:
            if self.__truncated and len(self.__trading_days_set) >= 5:
                order_num = 0
                cancelled_num = 0
                for orders in self.__detailedOrderDict.get(symbol):
                    for order in orders:
                        date = dt.datetime.strptime(order["orderTime"], '%m/%d/%y-%H:%M:%S').date()
                        if date == self.__maxProfit[0] or date == self.__minProfit[0]:
                            continue
                        status = order['status']
                        if 'cancelled' in status:
                            cancelled_num += 1
                        order_num += 1
                if order_num == 0:
                    ratio = 0.0
                else:
                    ratio = cancelled_num / order_num
                return ratio
            else:
                order_num = 0
                cancelled_num = 0
                for orders in self.__detailedOrderDict.get(symbol):
                    for order in orders:
                        status = order['status']
                        if 'cancelled' in status:
                            cancelled_num += 1
                        order_num += 1
                if order_num == 0:
                    ratio = 0.0
                else:
                    ratio = cancelled_num / order_num
                return ratio


class DailyInfo:
    def __init__(self, dailyProfit, dailyOpenAmount):
        self.dailyProfit = dailyProfit
        self.dailyOpenAmount = dailyOpenAmount


class ReturnInfo:
    # profit is after cost; return rate is pre-cost
    def __init__(self, afterCostProfit, returnRate):
        self.afterCostProfit = afterCostProfit
        self.returnRate = returnRate
