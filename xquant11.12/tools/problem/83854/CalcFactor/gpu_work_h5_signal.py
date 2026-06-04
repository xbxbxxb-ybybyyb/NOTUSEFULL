import time
import json
import sys
import os
import xquant.tensorflow as xt
import datetime
sys.path.append("..")
# print(sys.path)
from root.CalcFactor.store_data_2_h5 import store_data
from BT_SIG.Infer_Signal import infer_signal
from xquant.pyfile import Pyfile
from multiprocessing import Pool
import time
import json
import sys
import os
import xquant.tensorflow as xt
import datetime
sys.path.append("..")
# print(sys.path)
from root.BT.store_data_2_h5 import store_data
from BT_SIG.Infer_Signal_HDFS import infer_signal
from xquant.pyfile import Pyfile
from multiprocessing import Pool
from Logger.Logger import Logger
import CalcFactor.Config as calc_config 

config = calc_config.CalcConfig()
output_dir = config.factor_pickle_output_dir
StartDateTime = config.StartDateTime
EndDateTime = config.EndDateTime
factor_config = config.factor_config


is_convert_factor = True
is_gen_signal = False
py = Pyfile()


passed_str = os.environ['PARAMETERS']
start_idx, end_idx, pid = passed_str.split('-')
start_idx = int(start_idx)
end_idx = int(end_idx)

factorAddress = config.factor_address


import time

py = Pyfile()
passed_str = os.environ['PARAMETERS']
start_idx, end_idx, pid = passed_str.split('-')
start_idx = int(start_idx)
end_idx = int(end_idx)


if is_convert_factor:
    print(start_idx, end_idx)
    import random
    codes = py.listdir(output_dir)
    # codes = config.codes
    if end_idx > len(codes):
        end_idx = len(codes)
    print("convert factors into h5 files {}".format(codes[start_idx:end_idx]) )
    print("fdsfdsdf")
    store_data(code=codes[start_idx:end_idx], absolutePath=factorAddress, factorAddress=output_dir, pid=pid)
    print("convert factors done!!!")



if is_gen_signal:
    
    log_file_path = "/data/user/Logging/inferSignal/{}".format(str(config.EndDateTime))
    if not os.path.exists(log_file_path):
        os.makedirs(log_file_path)
    
    file_name = str(pid)+"_"+"debug.txt"
    log_debug_file = log_file_path + "/" + file_name
    log_fd = Logger(log_debug_file, level='debug')
    log_fd.logger.debug("start to infer signal")



    model_vers = os.listdir(config.model_path)
    # 用历史行情计算的因子产生当日预测值
    
    tagNames = config.tag_name
    factorName = config.factor_name
                       
    test_start_date = str(config.StartDateTime)
    test_end_date = str(config.EndDateTime)
  
    pickle_factor_address = config.factor_pickle_output_dir
    codes = py.listdir(pickle_factor_address)
    # print(codes)
    # print(test_start_date, test_end_date)
    cnt_stock = 0       
    model_vers.sort()
    for model_v in model_vers: 
        start = time.time()                       
        code_the_model = os.listdir(config.model_path+str(model_v)+"/ModelSaved")
        code_list = []
       
        for stock_name in code_the_model:
            for pickle_name in codes[start_idx:end_idx]:
                if stock_name in pickle_name:
                    print(pickle_name)
                    code_list.append(stock_name)
        print(code_list)
        cnt_stock = cnt_stock + len(code_list)
        print("Pid {} is doing Inference of model {},  total number of stocks in this model is {}, all model is {}".format(pid, model_v, len(code_list), model_vers)) 
        log_fd.logger.debug("Pid {} is doing Inference of model {},  total number of stocks in this model is {}, all model is {}".format(pid, model_v, len(code_list), model_vers)) 

        if len(code_list) > 0:
            infer_signal(config.signal_path, config.model_path+str(model_v)+"/", pickle_factor_address, tagNames, factorName, test_start_date, test_end_date, code_list)
        end = time.time()
        print("pid {} Have dong {} tasks of totally {} in model {} which cost {} seconds".format(pid, cnt_stock, end_idx-start_idx, model_v, end-start))
        log_fd.logger.debug("pid {} Have dong {} tasks of totally {} in model {} which cost {} seconds".format(pid, cnt_stock, end_idx-start_idx, model_v, end-start))








# if is_gen_signal:

    # model_vers = os.listdir(config.model_path)
    # # 用历史行情计算的因子产生当日预测值
    # if is_gen_signal:
        
        # tagNames = config.tag_name
        # factorName = config.factor_name                   
        # # test_start_date = config.today.strftime("%Y-%m-%d")
        # # test_end_date = config.today.strftime("%Y-%m-%d")
        # test_start_date = "2019-02-24"
        # test_end_date = "2019-03-01"

        # print("generating signal from ", test_start_date, "to", test_end_date)
        
        # cnt_stock = 0       
        # for model_v in model_vers:
            # modelPath = config.model_path+str(model_v)+"/ModelSaved"
            # rstPath = config.model_path+str(model_v)
            # code_the_model = os.listdir(modelPath)
            # code_list = []
            

            # for stock_name in code_the_model:
                # for pickle_name in codes[start_idx:end_idx]:
                    # if stock_name in pickle_name and stock_name in config.codes:
                        # print(stock_name)
                        # code_list.append(stock_name)
            # cnt_stock = cnt_stock + len(code_list)
            # if len(code_list) > 0:
                # infer_signal(modelPath, rstPath, factorAddress, tagNames, factorName, test_start_date, test_end_date, code_list, pid)
            # print("signal generated ", cnt_stock, "of ", end_idx-start_idx,"pid:", pid)

