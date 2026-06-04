import time
import json
import sys
import os
import xquant.tensorflow as xt
import datetime
from store_data_2_h5_multi import store_data
from BT_SIG.Infer_Signal import infer_signal
from xquant.pyfile import Pyfile
from multiprocessing import Pool





output_dir = 'output/temp/'
is_convert_factor = True
is_gen_signal = True
py = Pyfile()
#####################################################
# 计算开始结束的日期   
# today = datetime.datetime.now()
today = datetime.datetime.now() 
# - datetime.timedelta(days=3)
# weekday = today.weekday()
# predays = 1
# if weekday ==0:
    # predays = 3
# week_before = today - datetime.timedelta(days=predays)
# StartDateTime = "{}{}".format(week_before.strftime("%Y%m%d"), "093015") 
# EndDateTime = "{}{}".format(today.strftime("%Y%m%d"), "145659") 
# print("date from {} to {}".format(StartDateTime, EndDateTime))
passed_str = os.environ['PARAMETERS']
start_idx, end_idx, pid = passed_str.split('-')
start_idx = int(start_idx)
end_idx = int(end_idx)
# exit()
#########################################################################

factorAddress = "/data/user/AppleData"
# todo 删除log_save_path下的文件

if is_convert_factor:
    print(start_idx, end_idx)
    print("convert factors into h5 files")
    ##############################################################
    import random
    # random.shuffle(codes)   
    codes = py.listdir(output_dir)
    # codes = codes[1:15]
    # print(codes)

    if end_idx > len(codes):
        end_idx = len(codes)
    store_data(code=codes[start_idx:end_idx], absolutePath=factorAddress, factorAddress=output_dir, pid=pid)
    print("convert factors done!!!")


