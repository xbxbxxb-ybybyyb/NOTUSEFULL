import time
import json
import sys
import os
import xquant.tensorflow as xt
import datetime
sys.path.append("..")
# print(sys.path)
from root.BT.store_data_2_h5 import store_data
from BT_SIG.Infer_Signal import infer_signal
from xquant.pyfile import Pyfile
from multiprocessing import Pool
import BT.ConfigMultiPortfolio as bt_config 

config = bt_config.BacktestConfig()
output_dir = config.factor_pickle_output_dir
trade_portfolio = config.trade_portfolio
today_str = config.today_str
StartDateTime = config.StartDateTime
EndDateTime = config.EndDateTime
factor_config = config.factor_config


is_convert_factor = True
is_gen_signal = True
py = Pyfile()


passed_str = os.environ['PARAMETERS']
start_idx, end_idx, pid = passed_str.split('-')
start_idx = int(start_idx)
end_idx = int(end_idx)

factorAddress = config.factor_address

if is_convert_factor:
    print(start_idx, end_idx)
    print("convert factors into h5 files")
    import random
    codes = py.listdir(output_dir)
    # codes = config.codes
    if end_idx > len(codes):
        end_idx = len(codes)
    
    store_data(code=codes[start_idx:end_idx], absolutePath=factorAddress, factorAddress=output_dir, pid=pid)
    print("convert factors done!!!")




if is_gen_signal:

    model_vers = os.listdir(config.model_path)
    # 用历史行情计算的因子产生当日预测值
    if is_gen_signal:
        
        tagNames = config.tag_name
        factorName = config.factor_name                   
        test_start_date = config.today.strftime("%Y-%m-%d")
        test_end_date = config.today.strftime("%Y-%m-%d")
      
        print("generating signal from ", test_start_date, "to", test_end_date)
        
        cnt_stock = 0       
        for model_v in model_vers:
            modelPath = config.model_path+str(model_v)+"/ModelSaved"
            rstPath = config.model_path+str(model_v)
            code_the_model = os.listdir(modelPath)
            code_list = []
            

            for stock_name in code_the_model:
                for pickle_name in codes[start_idx:end_idx]:
                    if stock_name in pickle_name:
                        code_list.append(stock_name)
            cnt_stock = cnt_stock + len(code_list)
            if len(code_list) > 0:
                infer_signal(modelPath, rstPath, factorAddress, tagNames, factorName, test_start_date, test_end_date, code_list, pid)
            print("signal generated ", cnt_stock, "of ", end_idx-start_idx,"pid:", pid)

