# -*- coding: utf-8 -*-
import xlrd
import xlwt
import os
import shutil
import json   
import re


def summary(today_str, files_dir, portfolio, excel_name, config):
    absolutePath = '/data/user/666888/BT_Results/sources/' + today_str + '/'
    files_dir = files_dir
    path = absolutePath + files_dir + '/'
    if os.path.exists(path + 'TEMP'):
        shutil.rmtree(path + 'TEMP')
    fileList = os.listdir(path)
    try:
        fileList.remove('TEMP')
    except:
        pass
    daypath = '/data/user/666888/BT_Results/results/' + today_str + '/'
    daypath = daypath + files_dir
    code = config['quantity'].keys()

    if not os.path.exists(daypath):
        os.makedirs(daypath)
    # 1. Scan the result.xls in all the directories, and record all the titles
    titleDict = {}  # key = title, value = default 0
    titleList = []  # record the title strings
    errorDict = {}  # record the exception. make sure to print once
    for i in range(len(fileList)):
        innerDir = fileList[i]
        path2 = absolutePath + files_dir + '/' + innerDir + '/'
        stock_code = innerDir
        if not stock_code in code:
            continue
        file = path + innerDir + '/' + excel_name
        if os.path.exists(file):
            shutil.copy(file, daypath + '/' + stock_code + '.xls')
            wb = None
            try:
                wb = xlrd.open_workbook(file)
            except Exception as e:
                if innerDir not in errorDict:
                    errorDict.update({innerDir: e})
            else:
                ws = wb.sheet_by_name('summary')
                row = ws.row_values(0)
                for j in range(len(row)):
                    if row[j] not in titleDict:
                        titleDict.update({row[j]: 0})
                        titleList.append(row[j])

    # 2. sort the titleList and set the index to the titleDict
    titleList = sorted(titleList)
    for i in range(len(titleList)):
        titleDict.update({titleList[i]: i})

    # 3. write the first title row in TotalSummary.xls
    wbSum = xlwt.Workbook()
    wsSum = wbSum.add_sheet('TotalSummary')
    wsSum.write(0, 0, 'ModelFileName')
    for i in range(len(titleList)):
        wsSum.write(0, i + 1, titleList[i])

    # 4. read each directory again and write the corresponding summary
    row_wt = 1
    for i in range(len(fileList)):
        innerDir = fileList[i]
        stock_code = innerDir
        if not stock_code in code:
            continue
        file = path + innerDir + '/' + excel_name
        if os.path.exists(file):
            wb = None
            try:
                wb = xlrd.open_workbook(file)
            except Exception as e:
                if innerDir not in errorDict:
                    errorDict.update({innerDir: e})
            else:
                ws = wb.sheet_by_name('summary')
                row_title = ws.row_values(0)
                row_data = ws.row_values(1)
                for j in range(len(row_title)):
                    title = row_title[j]
                    titleIndex = titleDict.get(title) + 1  # +1 because the first column is 'ModelFileName'
                    wsSum.write(row_wt, titleIndex, row_data[j])
                wsSum.write(row_wt, 0, innerDir)
                row_wt += 1

    # finally output the error messages
    for e in errorDict.values():
        print(e)
    # write the excel file
    wbSum.save(daypath + '/TotalSummary.xls')


