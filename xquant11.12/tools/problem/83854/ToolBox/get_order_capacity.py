# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 16:37:11 2017

@author: 006547
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
from Logger.Logger import Logger
import math
import datetime as dt
import gc
import pickle
import pandas as pd
import numpy as np
import json
from ModelSystem.getAveTickVol import getVolMeanRaw
from multiprocessing import Pool
from tqdm import tqdm

import System.GetValidTradingDay as GTD

def getMaxVolumePerOrder(symbol, back_test_dates, dayNum):
    maxVolumePerOrder = {}
    for cur_date in back_test_dates:
        pre_date = dt.datetime.fromtimestamp(dt.datetime.strptime(str(cur_date), "%Y%m%d").timestamp()  - 24 * 3600).date().strftime('%Y%m%d')  
        if not cur_date in maxVolumePerOrder:
            volumePerOrder = getVolMeanRaw(symbol, int(pre_date), dayNum)
            maxVolumePerOrder[cur_date] = volumePerOrder
    
    return maxVolumePerOrder    
                
def get_order_capacity(signal_dates, stock_list=None):
    sys.path.append("Factor")
    sys.path.append("NonFactor")
    sys.path.append("Tag")
    sys.path.append("System")

    outOrderCapacityPath = "/data/user/666888/OrderCapacity/"
    maxVolumePerOrderDayNum = 20
    if stock_list is None:
        code = os.listdir(outOrderCapacityPath)
        code.sort()
    else:
        code = stock_list

    log_file_path = "/data/user/666888/Logging/OrderCapacity"
    log_err_file = log_file_path + "/" + "error.txt"
    if not os.path.exists(log_file_path):
        os.makedirs(log_file_path)
    log_error_fd = Logger(log_err_file, level='debug')
    # code = code[1200:]
    stock_num = len(code)
    for i in tqdm(range(stock_num)):
        backTestUnderlying = code[i]
        print("stage get capacity {} {}/{}".format(backTestUnderlying, i+1, stock_num))
        stock_code = backTestUnderlying
        try:     
        # if True: 
            time1 = dt.datetime.now()  
            order_capacity_path = outOrderCapacityPath + '/' + stock_code + "/"    
            if not os.path.exists(order_capacity_path):
                os.makedirs(order_capacity_path)
                             
            signal_dates.sort()
            log_error_fd.logger.debug("stock_code: %s, signal_dates: %s", stock_code, signal_dates)
            valid_dates = signal_dates
            if False:
                valid_dates = GTD.getValidTradingDayList(stock_code, int(signal_dates[0]), int(signal_dates[-1]))
                print(valid_dates, stock_code, maxVolumePerOrderDayNum)
            maxVolumePerOrders = getMaxVolumePerOrder(stock_code, valid_dates, maxVolumePerOrderDayNum)
            
            
            order_capacity = {"code": stock_code, "OrderCapacity": maxVolumePerOrders}
            if os.path.exists(order_capacity_path + '/OrderCapacity.json'):
                with open(order_capacity_path + '/OrderCapacity.json', "r") as f:
                    capacity = json.load(f)
                    order_capacity["OrderCapacity"].update(capacity["OrderCapacity"])  
                  
            with open(order_capacity_path + '/OrderCapacity.json', "w") as f:
                 json.dump(order_capacity, f)
                           
            time2 = dt.datetime.now()
            log_error_fd.logger.debug("total train time: %s", time2 - time1)

            # del signalEvaluate
            
            gc.collect()
        except Exception as e:
            print("error")
            print(e)
            
            log_error_fd.logger.debug("train code: %s Failed", code[i])

def get_order_capacity2(signal_dates, start_idx, end_idx):
    sys.path.append("Factor")
    sys.path.append("NonFactor")
    sys.path.append("Tag")
    sys.path.append("System")

    outOrderCapacityPath = "/app/data/666888/OrderCapacity/" 
    maxVolumePerOrderDayNum = 20
    code = os.listdir(outOrderCapacityPath)
    code.sort()
    log_file_path = "/app/data/666888/Logging/OrderCapacity"
    log_err_file = log_file_path + "/" + "error.txt"
    if not os.path.exists(log_file_path):
        os.makedirs(log_file_path)
    log_error_fd = Logger(log_err_file, level='debug')
    code = code[start_idx:end_idx]
    stock_num = len(code)
    for i in range(stock_num):
        backTestUnderlying = code[i]
        print("stage get capacity {} {}/{} ({} -{})".format(backTestUnderlying, i+1, stock_num, start_idx, end_idx))
        stock_code = backTestUnderlying
        try:     
        # if True: 
            time1 = dt.datetime.now()  
            order_capacity_path = outOrderCapacityPath + '/' + stock_code + "/"    
            if not os.path.exists(order_capacity_path):
                os.makedirs(order_capacity_path)
                             
            signal_dates.sort()
            log_error_fd.logger.debug("stock_code: %s, signal_dates: %s", stock_code, signal_dates)  
            valid_dates = GTD.getValidTradingDayList(stock_code, int(signal_dates[0]), int(signal_dates[-1]))
            
                                      
            maxVolumePerOrders = getMaxVolumePerOrder(stock_code, valid_dates, maxVolumePerOrderDayNum)
            order_capacity = {"code": stock_code, "OrderCapacity": maxVolumePerOrders}
            if os.path.exists(order_capacity_path + '/OrderCapacity.json'):
                with open(order_capacity_path + '/OrderCapacity.json', "r") as f:
                    capacity = json.load(f)
                    order_capacity["OrderCapacity"].update(capacity["OrderCapacity"])  
                  
            with open(order_capacity_path + '/OrderCapacity.json', "w") as f:
                 json.dump(order_capacity, f)
                           
            time2 = dt.datetime.now()
            log_error_fd.logger.debug("total train time: %s", time2 - time1)

            # del signalEvaluate
            
            gc.collect()
        except:
            log_error_fd.logger.debug("train code: %s Failed", code[i])

def get_order_capacity_paral(signal_dates):
    outOrderCapacityPath = "/app/data/666888/OrderCapacity/" 
    code = os.listdir(outOrderCapacityPath)
    processNum = 8
    baseNum = len(code) // processNum
    remains = len(code) % processNum
    pool = Pool(processes=processNum)
    idx = 0
    
    for index in range(processNum):
        if index < remains:
            edx = idx + baseNum + 1
        else:
            edx = idx + baseNum
        pool.apply_async(get_order_capacity, (signal_dates, ))
        idx = edx
    pool.close()
    pool.join()

def main():
    signal_dates = []
    # start = dt.datetime(2019, 1,18)
    # end = dt.datetime(2019, 1,18)
    # while end > start:
        # if start.weekday() < 5:
            # signal_dates.append(start.strftime('%Y%m%d'))
        # start = start + dt.timedelta(days=1)
    # print(signal_dates)  
    get_order_capacity_paral(["20190118"])
    
    
if __name__ == "__main__":
    main()
