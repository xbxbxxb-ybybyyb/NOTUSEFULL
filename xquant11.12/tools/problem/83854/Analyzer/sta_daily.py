import xlrd
import xlwt
import numpy as np
import pandas as pd
import os
import re
import json
import pandas as pd


def summary(today_str, files_dir):
    absolutePath = "/data/user/666888/BT_Results/results/" + today_str + '/' + files_dir + '/'
    sta_by_code = {}
    results = os.listdir(absolutePath) 
    for rst in results:
        if re.match(r"^\d{6}.\D{2}.*", rst):
            file = absolutePath + "/" + rst  
            wb = xlrd.open_workbook(file)
            ws = wb.sheet_by_name('dailyInfo')
            col0 = ws.col_values(0)
            col2 = ws.col_values(2)
            code = rst.split(".xls")[0] 
            sta_by_code[code] = {}
            for j in range(1, len(col0)):
                sta_by_code[code].update({col0[j]: col2[j]})
    title_list = ['Date']  
    code_list = list(sta_by_code.keys())
    code_list.sort() 
    title_list = title_list + code_list 
    
    date_list = {}
    for code in code_list:
        dates = list(sta_by_code[code].keys())  
        for d in dates:
            if not d in date_list:
                date_list[d] = True
    dates = list(date_list.keys())
    dates.sort()
    rst = {}
    for key in title_list:
        if not key in rst:
            rst[key] = []
    rst['Date'] = dates
    for code in code_list:
        for d in dates:
            if not d in sta_by_code[code]:
                rst[code].append(0.0)
            else:
                rst[code].append(sta_by_code[code][d])
    rst['Total'] = []
    for index in range(len(dates)):
        total = 0.0
        for code in code_list:
            total = total + float(rst[code][index])
        rst['Total'].append(total)   
         
    writer = pd.ExcelWriter(absolutePath + "/" + 'daily_split.xlsx')
    df1 = pd.DataFrame(data=rst)
    df1.to_excel(writer, "daily_split")
    writer.save()

