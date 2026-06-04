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
import BT_HDFS.ConfigMultiPortfolio as bt_config 
from Logger.Logger import Logger
import time
config = bt_config.BacktestConfig()

# valid model
model_vers = os.listdir(config.model_path)
model_list = []
for model_v in model_vers: 
    code_the_model = os.listdir(config.model_path+str(model_v)+"/ModelSaved")
    model_list.extend(code_the_model)

config.codes = model_list
config.codes.sort()


is_gen_signal = True
py = Pyfile()
passed_str = os.environ['PARAMETERS']
start_idx, end_idx, pid = passed_str.split('-')
start_idx = int(start_idx)
end_idx = int(end_idx)

if is_gen_signal:

    log_file_path = "/data/user/Logging/inferSignal/{}_pid_{}".format(str(config.EndDateTime), pid)
    if not os.path.exists(log_file_path):
        os.makedirs(log_file_path)
    
    file_name = str(pid)+"_"+"debug.txt"
    log_debug_file = log_file_path + "/" + file_name
    log_fd = Logger(log_debug_file, level='debug')
    log_fd.logger.debug("start to infer signal")

    model_vers = os.listdir(config.model_path)
    log_fd.logger.debug("all model in the path {} is {}".format(model_vers, config.model_path))

    # 用历史行情计算的因子产生当日预测值
    if is_gen_signal:

        tagNames = config.tag_name
        factorName = config.factor_name

        test_start_date = config.StartDateTime
        test_end_date = config.EndDateTime
      
        pickle_factor_address = config.factor_pickle_output_dir
        # codes = py.listdir(pickle_factor_address)
        codes = config.codes
        codes.sort()
        log_fd.logger.debug("All code is {}".format(codes))
        log_fd.logger.debug("Total code number is {}, start index {}, end index {} ".format(len(codes), start_idx, end_idx))

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
                        code_list.append(stock_name)
            cnt_stock = cnt_stock + len(code_list)
            print("Pid {} is doing Inference of model {},  total number of stocks in this model is {}, total stock num is {}, all model is {} ".format(pid, model_v, len(code_list), end_idx-start_idx, model_vers)) 
          #  log_fd.logger.debug("Pid {} is doing Inference of model {},  total number of stocks in this model is {}, all model is {}".format(pid, model_v, len(code_list), model_vers)) 

            if len(code_list) > 0:
                infer_signal(config.signal_path, config.model_path+str(model_v)+"/", pickle_factor_address, tagNames, factorName, test_start_date, test_end_date, code_list, pid)
            end = time.time()
            print("pid {} Have dong {} tasks of totally {} , current model {} which cost {} seconds".format(pid, cnt_stock, end_idx-start_idx, model_v, end-start))
           # log_fd.logger.debug("pid {} Have dong {} tasks of totally {} in model {} which cost {} seconds".format(pid, cnt_stock, end_idx-start_idx, model_v, end-start))

