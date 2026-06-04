import os
import pickle
import json
from multiprocessing import Pool
from datetime import datetime
from xquant.pyfile.ftp import pyfileFTP
import pandas as pd
import ToolBox.constant_params as constants
from xquant.pyfilelib import Pyfile
import time
#py = Pyfile()
# 常量：指定了相应的路径
ORDER_CAPACITY_PATH = constants.order_capacity_path
TRADE_PATH =          constants.trade_data_path
PORTFOLIO_PATH =           constants.portfolio_path   
PROCESS_NUM = 10



def get_bt_data(target_code, volume, start_date, end_date, combine_path, index_list, pid):
    py = Pyfile()

    from Logger.Logger import Logger
         
    py = Pyfile()

    last_date = "20181001"


    log_file = "/app/data/666888/Logging/delete_trade/log_info_20190308.txt"
    if not os.path.exists("/app/data/666888/Logging/delete_trade/"):
        os.makedirs("/app/data/666888/Logging/delete_trade/")
    log_fd = Logger(log_file, level='info')
    log_fd.logger.info(str(pid))

    quantity = {}
    start = time.time()
    for index in index_list:
        log_fd.logger.info("Pid {} have get {} stocks".format(pid, index))

        c = target_code[index]
        order_capacity = {"OrderCapacity": {}}
        __fpath = ORDER_CAPACITY_PATH + "/" + c + '/OrderCapacity.json'
        if not os.path.exists(__fpath):
            print("order capacity not found", c)
            print(__fpath)
            continue
        with open(ORDER_CAPACITY_PATH + "/" + c + '/OrderCapacity.json', "r") as f:
            capacity = json.load(f)
        code = capacity["code"]
        order_capacity["code"] = code
        if 300000 <= int(code[0: 6]) <= 399999:
            order_capacity["Holo"] = "true"
        else:
            order_capacity["Holo"] = "false"
        dates = []
        for d in capacity["OrderCapacity"]:
            if d >= start_date and d <= end_date:
                dates.append(d)
        if len(dates) == 0:
            log_fd.logger.info("stock {} have no trade data on {}".format(c, d))
            continue        
        # Trade data
        dates.sort()
        for d in dates:
            order_capacity["OrderCapacity"][d] = capacity["OrderCapacity"][d] 
        tickData = []
        transactionData = []
        for d in dates:
            # load from share
            if not py.exists(TRADE_PATH + "/" + c + "/" + d + "/Data.pickle"):
                log_fd.logger.info("stock {} on date {} have no trade data".format(c, d))
                log_fd.logger.info(TRADE_PATH + "/" + c + "/" + d + "/Data.pickle")

                #print(TRADE_PATH + "/" + c + "/" + d + "/Data.pickle")
                continue
            # print("pickle path is ", TRADE_PATH + "/" + c + "/" + d + "/Data.pickle")
            with py.open(TRADE_PATH + "/" + c + "/" + d + "/Data.pickle", Absolute=False, mode='rb') as f:
                data = pickle.load(f)
            tickData.append(data[0])
            transactionData.append(data[1])
        out_path = combine_path + '/' + c + "/"
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        try:
            with py.open(out_path + "/Data.pickle" ,Absolute=False, mode= 'wb') as f:
                pickle.dump((tickData, transactionData), f)
        except Exception as e:
            log_fd.logger.info("stock {} dumping trade data error: {}".format(c, e))           
        try:   
            with py.open(out_path + '/OrderCapacity.json', Absolute=False, mode= 'wb') as f:
                json.dump(order_capacity, f)   
        except Exception as e:
            log_fd.logger.info("stock {} dumping OrderCapacity error: {}".format(c, e))
        try:   
            with py.open(out_path + '/Dates.json', Absolute=False, mode='wb') as f:
                json.dump({"Dates": dates}, f) 
        except Exception as e:
            log_fd.logger.info("stock {} dumping Dates error: {}".format(c, e))
        quantity[c] = volume[index]
    return quantity
    
def combine(target_code, volume, start_date, end_date, combine_name): 
    bt_date_path = PORTFOLIO_PATH + "/" + start_date + "-" + end_date + "/" 
    combine_path = bt_date_path + "/" + combine_name   
       
    if not os.path.exists(combine_path):
        os.makedirs(combine_path)
        print("combine_path is {}".format(combine_path))
    if False:
        quantity = get_bt_data(target_code, volume, start_date, end_date, combine_path)
        
        with open(combine_path + '/' + combine_name + '_quantity.json', "w") as f:
            json.dump({"Combine": combine_name, "quantity": quantity}, f)    
       
    quantity = {}
    processNum = PROCESS_NUM
    para_split = []
    if len(target_code) < processNum:
        processNum = len(target_code)
               
    for index in range(processNum):
        para_split.append([])
        
    count = 0    
    for index in range(len(target_code)):
        para_split[count].append(index)
        count = count + 1
        if count >= processNum:
            count = 0
        
    pool = Pool(processes=processNum)
    multiProcessResult = []
    for ii in range(para_split.__len__()):
        result = pool.apply_async(get_bt_data, (target_code, volume, start_date, end_date, combine_path,  para_split[ii],ii,))
        multiProcessResult.append(result)
    pool.close()
    pool.join()
    for kk in multiProcessResult:
        quantity.update(kk.get())   
    try:
        with open(combine_path + '/' + combine_name + '_quantity.json', "w") as f:
            json.dump({"Combine": combine_name, "quantity": quantity}, f)                         
    except Exception as e:
        print(e)
                                        
                                                
                                                        
                                                                        
                   
      
def main():
    start_date = "20190110"
    end_date =   "20190110"
    stock = ["000002.SZ", "000001.SZ", "000006.SZ"]
    volume = [200, 300, 300]
     
    combine(stock, volume, start_date, end_date, "TEST_PORTFOLIO_1")


       