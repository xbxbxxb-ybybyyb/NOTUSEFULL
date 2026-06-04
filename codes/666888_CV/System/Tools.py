# -*- coding: utf-8 -*-
"""
Created on 2017/9/7 20:47

@author: 006547
"""
import xlwt
import datetime as dt
import os


def exportExecl(strategy):
    style0 = xlwt.easyxf('font: name Times New Roman, color-index red, bold on')
    style1 = xlwt.easyxf(num_format_str='YY-MM-DD: HH-MM-SS')
    if not os.path.exists(strategy.getOutputDir()):
        os.makedirs(strategy.getOutputDir())
    wb = xlwt.Workbook()
    for i in range(strategy.getOutputFactor().__len__()):
        sheetName = strategy.getTradingUnderlyingCode()[i][0]
        if strategy.getTradingUnderlyingCode()[i].__len__() - 1 > 0:
            for j in range(strategy.getTradingUnderlyingCode()[i].__len__()-1):
                sheetName = sheetName + "-" + strategy.getTradingUnderlyingCode()[i][j + 1]  # 为sheet命名
        ws = wb.add_sheet(sheetName)
        ws.write(0, 0, "TimeStamp", style0)  # 写入时间戳表头
        column = 0
        while column < strategy.getFactorName().__len__():  # 写入因子名表头
            ws.write(0, column + 1, strategy.getFactorName()[column], style0)
            column += 1
        # ws.write(0, column + 1, "BreakLongTag", style0)  # 写入标签表头
        # ws.write(0, column + 2, "BreakShortTag", style0)  # 写入标签表头
        # ws.write(0, column + 3, "BreakLongShortTag", style0)  # 写入标签表头
        # ws.write(0, column + 4, "reversalLongTag", style0)  # 写入标签表头
        # ws.write(0, column + 5, "reversalShortTag", style0)  # 写入标签表头
        # ws.write(0, column + 6, "reversalLongShortTag", style0)  # 写入标签表头
        ws.write(0, column + 1, "1minTag", style0)  # 写入标签表头
        ws.write(0, column + 2, "2minTag", style0)  # 写入标签表头
        ws.write(0, column + 3, "5minTag", style0)  # 写入标签表头
        # ws.write(0, column + 4, "BreakLongStartPrice", style0)  # 写入标签表头

        for row in range(strategy.getOutputFactor()[i].__len__()):
            ws.write(row + 1, 0, dt.datetime.fromtimestamp(strategy.getOutputTimeStamp()[i][row]), style1)  # 写入时间戳
            column = 0
            while column < strategy.getOutputFactor()[i][row].__len__():  # 写入因子数据
                ws.write(row + 1, column + 1, strategy.getOutputFactor()[i][row][column])
                column += 1
            # ws.write(row + 1, column + 1, strategy.getOutputTag()[i][row].subTag["breakLong"].returnRate)  # 写入标签数据
            # ws.write(row + 1, column + 2, strategy.getOutputTag()[i][row].subTag["breakShort"].returnRate)  # 写入标签数据
            # ws.write(row + 1, column + 3, strategy.getOutputTag()[i][row].subTag["breakLongShort"].returnRate)  # 写入标签数据
            # ws.write(row + 1, column + 4, strategy.getOutputTag()[i][row].subTag["reversalLong"].returnRate)  # 写入标签数据
            # ws.write(row + 1, column + 5, strategy.getOutputTag()[i][row].subTag["reversalShort"].returnRate)  # 写入标签数据
            # ws.write(row + 1, column + 6, strategy.getOutputTag()[i][row].subTag["reversalLongShort"].returnRate)  # 写入标签数据
            ws.write(row + 1, column + 1, strategy.getOutputTag()[i][row].subTag["1min"].returnRate)  # 写入标签数据
            ws.write(row + 1, column + 2, strategy.getOutputTag()[i][row].subTag["2min"].returnRate)  # 写入标签数据
            ws.write(row + 1, column + 3, strategy.getOutputTag()[i][row].subTag["5min"].returnRate)  # 写入标签数据
            # ws.write(row + 1, column + 4, strategy.getOutputTag()[i][row].subTag["breakLong"].startPrice)  # 写入标签数据
    wb.save(strategy.getOutputDir()+"/"+strategy.getStrategyName()+'.xls')
