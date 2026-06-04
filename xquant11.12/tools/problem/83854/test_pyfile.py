import os
import sys
# from System import DumpLoad
# from xquant.pyfile import Pyfile
# from multiprocessing import Pool
import datetime as dt
import h5py

# with h5py.File("/app/data/666888/AppleData/600031.SH/timestamp", mode='r') as f:
    # print(list(f.keys()))
from xquant.pyfile import Pyfile
py = Pyfile()

if True:
    stocks = print(len(py.listdir("output/trade_review_factor_pickle")))
    a = 0
    b = 0
    for stock in py.listdir('$21/ModelProduction/20181001_end/signals/'):
        print(stock)
        print(py.exists('$21/ModelProduction/20181001_end/signals/'+stock+"/"+stock+"_"+"20190225.csv"))
        a = a+py.exists('$21/ModelProduction/20181001_end/signals/'+stock+"/"+stock+"_"+"20190225.csv")
        print(a)
        b = b+1
        print(b)
if False:     
    print(len(py.listdir('$21/ModelProduction/20181001_end/bt_info/20190225-20190225/5161101+800')))
    print(len(py.listdir('$21/ModelProduction/20181001_end/bt_info/20190225-20190225/5161101')))

    print(len(py.listdir('$21/ModelProduction/20181001_end/bt_info/20190225-20190225/h300')))
    print(len(py.listdir('$21/ModelProduction/20181001_end/bt_info/20190225-20190225/z500')))