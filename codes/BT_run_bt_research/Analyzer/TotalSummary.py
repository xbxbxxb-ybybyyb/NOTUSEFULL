import xlrd
import xlwt
import os
import shutil


def summary(source_path_dir, result_path_dir, excel_name, config):
    if os.path.exists(source_path_dir + 'TEMP'):
        shutil.rmtree(source_path_dir + 'TEMP')
    file_list = os.listdir(source_path_dir)
    try:
        file_list.remove('TEMP')
    except:
        pass
    code = config['quantity'].keys()

    if not os.path.exists(result_path_dir):
        os.makedirs(result_path_dir)
    # 1. Scan the result.xls in all the directories, and record all the titles
    titleDict = {}  # key = title, value = default 0
    titleList = []  # record the title strings
    errorDict = {}  # record the exception. make sure to print once
    for i in range(len(file_list)):
        inner_dir = file_list[i]
        stock_code = inner_dir
        if not stock_code in code:
            continue
        file = source_path_dir + inner_dir + '/' + excel_name
        if os.path.exists(file):
            shutil.copy(file, result_path_dir + '/' + stock_code + '.xls')
            wb = None
            try:
                wb = xlrd.open_workbook(file)
            except Exception as e:
                if inner_dir not in errorDict:
                    errorDict.update({inner_dir: e})
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
    for i in range(len(file_list)):
        inner_dir = file_list[i]
        stock_code = inner_dir
        if not stock_code in code:
            continue
        file = source_path_dir + inner_dir + '/' + excel_name
        if os.path.exists(file):
            wb = None
            try:
                wb = xlrd.open_workbook(file)
            except Exception as e:
                if inner_dir not in errorDict:
                    errorDict.update({inner_dir: e})
            else:
                ws = wb.sheet_by_name('summary')
                row_title = ws.row_values(0)
                row_data = ws.row_values(1)
                for j in range(len(row_title)):
                    title = row_title[j]
                    titleIndex = titleDict.get(title) + 1  # +1 because the first column is 'ModelFileName'
                    wsSum.write(row_wt, titleIndex, row_data[j])
                wsSum.write(row_wt, 0, inner_dir)
                row_wt += 1

    # finally output the error messages
    for e in errorDict.values():
        print(e)
    # write the excel file
    wbSum.save(result_path_dir + '/TotalSummary.xls')
