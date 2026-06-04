import pandas as pd
import os
import re
import pandas.io.formats.excel


if not os.path.exists("/data/user/666888/AlgoGenzong/summary/"):
    os.makedirs("/data/user/666888/AlgoGenzong/summary/")

portfo = "hs300"
# portfo = "zz500"

preDate = 20200320
sDate = 20200323
eDate = 20200327

ias = [300000000, 500000000, 1000000000, 1500000000]

btd = "/data/user/666888/AlgoGenzong/results/{}-{}/".format(sDate, eDate)
btres = os.listdir(btd)

pres = 1
if not os.path.exists("/data/user/666888/AlgoGenzong/summary/{}_{}.xlsx".format(preDate, portfo)):
    pres = -1

writer = pd.ExcelWriter("/data/user/666888/AlgoGenzong/summary/{}_{}.xlsx".format(eDate, portfo))
pandas.io.formats.excel.header_style=None

for ia in ias:
    if pres > 0:
        prerd = pd.read_excel("/data/user/666888/AlgoGenzong/summary/{}_{}.xlsx".format(preDate, portfo), sheet_name="ResultDaily_{}".format(int(ia / 100000000)))
    else:
        prerd = None
    
    for btr in btres:
        if re.search(str(eDate) + "-" + portfo + "-cv-" + "\d{8}-\d{8}-" + portfo + "-" + str(ia), btr):
            nowrd = pd.read_excel("{}/{}/result_daily_modified.xlsx".format(btd, btr), index_col=0)
            rdcn = nowrd.columns.tolist()

    if prerd is not None:
        nowrd = pd.concat((prerd, nowrd))

    nowrd.to_excel(writer, sheet_name="ResultDaily_{}".format(int(ia / 100000000)), index=False)

for ia in ias:
    for btr in btres:
        if re.search(str(eDate) + "-" + portfo + "-cv-" + "\d{8}-\d{8}-" + portfo + "-" + str(ia), btr):
            
            nowts = pd.read_excel("{}/{}/TotalSummary.xls".format(btd, btr))
            tscn = nowts.columns.tolist()

    nowts.to_excel(writer, sheet_name="TotalSummary_{}".format(int(ia / 100000000)), index=False)

wb = writer.book
fmtj = wb.add_format({"font_name": "Arial", "font_size":10, 'align': 'left', 'valign': 'vcenter'})
fmti = wb.add_format({"font_name": "仿宋", "font_size":10, 'align': 'left', 'valign': 'vcenter', 'bold':True})
fmtk = wb.add_format({"font_name": "Arial", "font_size":10, 'align': 'left', 'valign': 'vcenter'})
for wsn, ws in writer.sheets.items():
    ws.set_column("A:AE", 8, fmtj)
    if wsn.startswith("R"):
        for i, cn in enumerate(rdcn):
            ws.write(0, i, cn, fmti)
    else:
        for i, cn in enumerate(tscn):
            ws.write(0, i, cn, fmtk)

writer.save()
