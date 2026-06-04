# -*- coding: utf-8 -*-
"""
to output a spreadsheet for a better look

by 011478
"""

import xlwt
import copy


DetailedOrdersTitleList = ['tradeNo', 'code', 'orderTime', 'direction', 'price', 'quantity', 'avgPrice', 'cumQty',
                           'status', 'orderAmount', 'cumAmount']
ResultOrdersTitleList = ['code', 'startTime', 'direction', 'startPrice', 'endPrice', 'endTime', 'orderAmount',
                         'cumAmount', 'returnRate', 'afterCostProfit']
DateTitleList = ['date', 'preCostDailyProfit', 'afterCostDailyProfit', 'dailyOpenAmount', 'dailyCancelledRatio']


# if funStr is None, meaning runBackTest is used. otherwise the old methods are used
def OutputSpreadSheet(detailedOrders, result, dirPath, funStr):
    wb = xlwt.Workbook()
    OutputDetailedOrders(wb, detailedOrders, funStr)
    OutputResultOrders(wb, result)
    OutputDate(wb, result, funStr)
    OutputSummary(wb, result)
    wb.save(dirPath)


def OutputDetailedOrders(wb, detailedOrders, funStr):
    ws = wb.add_sheet('detailedOrders')
    # titleList = ['tradeNo', 'code', 'orderTime', 'direction', 'price', 'quantity', 'avgPrice',
    #              'cumQty', 'status', 'orderAmount', 'cumAmount']
    if funStr is None:
        for i in range(len(DetailedOrdersTitleList)):
            ws.write(0, i, DetailedOrdersTitleList[i])

        row = 1
        for i in range(len(detailedOrders)):
            for j in range(len(detailedOrders[i])):
                for k in range(len(DetailedOrdersTitleList)):
                    if k == 0:
                        ws.write(row, k, i + 1)
                    else:
                        ws.write(row, k, detailedOrders[i][j].get(DetailedOrdersTitleList[k]))
                row += 1


def OutputResultOrders(wb, result):
    orders = result.get('order')
    ws = wb.add_sheet('orders')
    # titleList = ['code', 'startTime', 'direction', 'startPrice', 'endPrice', 'endTime', 'orderAmount',
    #              'cumAmount', 'returnRate', 'afterCostProfit']
    for i in range(len(ResultOrdersTitleList)):
        ws.write(0, i, ResultOrdersTitleList[i])

    row = 1
    for i in range(len(orders)):
        for k in range(len(ResultOrdersTitleList)):
            ws.write(row, k, orders[i].get(ResultOrdersTitleList[k]))
        row += 1


def OutputDate(wb, result, funStr):
    # titleList = ['date', 'preCostDailyProfit', 'afterCostDailyProfit', 'dailyOpenAmount']
    ws = wb.add_sheet('dailyInfo')
    if funStr is None:
        for i in range(len(DateTitleList)):
            ws.write(0, i, DateTitleList[i])

        if len(DateTitleList) <= 1:
            return

        dateList = []
        tempDict = result.get(DateTitleList[1])
        for i in tempDict.keys():
            dateList.append(i)
        dateList = sorted(dateList)

        row = 1
        for i in range(len(dateList)):
            for k in range(len(DateTitleList)):
                if k == 0:
                    ws.write(row, 0, dateList[i])
                else:
                    dictInfo = result.get(DateTitleList[k])
                    ws.write(row, k, dictInfo.get(dateList[i]))
            row += 1


def OutputSummary(wb, result):
    ws = wb.add_sheet('summary')
    tempResult = copy.deepcopy(result)
    tempResult.pop('order', None)
    for i in range(len(DateTitleList)):
        tempResult.pop(DateTitleList[i], None)

    row = 0
    title = sorted(tempResult.keys())
    for i in range(len(title)):
        ws.write(row, i, title[i])

    row += 1
    for i in range(len(title)):
        ws.write(row, i, tempResult.get(title[i]))

