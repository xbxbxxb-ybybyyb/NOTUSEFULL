import pandas as pd
#import DataAPI2.DataToolkit as Dtk
#key_date = 20220929
#n_days_off = 3
#ans = Dtk.get_n_days_off(key_date, n_days_off)
#print(ans)
#from DataAPI2.AddressManagement import AddressManagement
import datetime as dt
import shutil
import time
import os
import pickle
import hashlib
import json
#1. get data root
#addressmanagement = AddressManagement()
#root=(addressmanagement.get_root('666889'))
#print(root + '/Apollo/DepartmentDailyFactor_expanded/DepartmentDailyStandardFactor2')


#2. 
#end_day = 20190103
#ts = pd.datetime.strptime(str(end_day),'%Y%m%d').timestamp()
#print(ts)



#1) datetime => string
#一个string对象 = datetime.datetime.strftime(一个datetime对象,'%Y-%m-%d %H:%M:%S')
print("datetime => string")
today = dt.datetime.today()
s = dt.datetime.strftime(today,'%Y-%m-%d %H:%M:%S')
print('from')
print(today)
print('to')
print(s)
print("--------------")
#
#2) string => datetime
#一个datetime对象 = datetime.datetime.strptime(一个string对象,'%Y-%m-%d %H:%M:%S')
print('string => datetime')
s = '2019-01-03 00:01:01'
res = dt.datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
print('from')
print(s)
print('to')
print(res)
print("--------------")
#
#3) datetime => timestamp
#
#一个timestamp对象= time.mktime(一个datetime对象)
print('datetime => timestamp')

today = dt.datetime.today()
ts = time.mktime((2019, 1, 3, 1, 2, 3, 0, 0, 0))
print('from')
print('(2019, 1, 3, 1, 2, 3, 0, 0, 0)')
print('to')
print(ts)
print("--------------")

#
#4) timestamp => datetime
#
#一个datetime对象= datetime.datetime.fromtimestamp(一个timestamp对象)
print('timestamp => datetime')
res = dt.datetime.fromtimestamp(1546448523)
print('from')
print('1546448523')
print('to')
print(res)
print("--------------")
#

#5) string => timestamp
#一个timestamp 对象= time.mktime(time.strptime(一个string对象, '%Y-%m-%d'))
print('timestamp => datetime')
res = time.mktime(time.strptime('2019-01-03', '%Y-%m-%d'))
print('from')
print('2019-01-03')
print('to')
print(res)
print("--------------")
#
#6) timestamp => string
#
## time.localtime()将时间戳转换为struct_time
#
#一个string对象= time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(一个time stamp对象))。
print('timestamp => string')

res = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(1546448523))
print('from')
print('1546448523')
print('to')
print(res)
print("--------------")













#============================================
#BTC example
import pandas as pd
import datetime as dt
import shutil
import time
import os
import pickle
import hashlib
import json
import sys
#1. get data root


fn = sys.argv[1]
print(fn)

a =pd.read_parquet('../BTCUSDT/' + fn)
a['second'] = a['timestamp'].apply(lambda x:time.strftime("%Y%m%d-%H:%M:%S", time.localtime(x / 1000000)))
#a['st'] = a['timestamp'].apply(lambda x:pd.to_datetime(x, unit='ms'))
a['st'] = pd.to_datetime(a['timestamp'], unit='us') #a['timestamp'].apply(lambda x:pd.to_datetime(x, unit='ms'))
#a['second'] = pd.to_datetime(a['timestamp'] / 1000000, unit='s') #a['timestamp'].apply(lambda x:pd.to_datetime(x, unit='ms'))

#print(a)
b = (a.groupby(by='second').last())
del b['timestamp']
del b['local_timestamp']
del b['st']
#print(b)

di = fn.replace('parquet', '')
b.to_csv('DATA/' + di + '.csv')

