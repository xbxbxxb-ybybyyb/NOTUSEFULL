# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 16:37:11 2017

@author: 006547
@author: 012807
"""
import sys
import os 
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
from BT_SIG.ModelInfer import ModelCNNLSTMLongShort
from Logger.Logger import Logger
import System.GetXQuantData2 as GD
import math
import datetime as dt
import gc
import pickle
import pandas as pd
import numpy as np
import json
from multiprocessing import Pool
# from xquant.pyfile import Pyfile
from xquant.pyfilelib import Pyfile
   
def get_trade_to_hdfs(outTradeDataPath, signal_dates, log_file_path = "/app/data/666888/Logging/TradeData", stock_list = None):
    sys.path.append("Factor")
    sys.path.append("NonFactor")
    sys.path.append("Tag")
    sys.path.append("System")
    py = Pyfile()    
    if stock_list is None:
        code = py.listdir(outTradeDataPath)
        # code = code_diff
        code.sort()
    else:
        code = stock_list
        
    today = dt.datetime.now()
    today_str = today.strftime('%Y%m%d%H%M%S')
    log_err_file = log_file_path + "/" +today_str+ "_info.txt"
    if not os.path.exists(log_file_path):
        os.makedirs(log_file_path)
    log_error_fd = Logger(log_err_file, level='info')
    # code = code[1200:]

    stock_num = len(code)
    succeful_geted_stock_num = 0
    for i in range(stock_num):
        backTestUnderlying = code[i]
        log_error_fd.logger.info("Begin getting trade {} {}/{}".format(backTestUnderlying, i+1, stock_num))
        stock_code = backTestUnderlying
        #try:     
        time1 = dt.datetime.now()  
        trade_data_path = outTradeDataPath + '/' + stock_code + "/"    
            
        if not py.exists(trade_data_path):
            py.mkdir(trade_data_path)       
                                              
        signal_dates.sort()
        log_error_fd.logger.info("stock_code: %s, signal_dates: %s", stock_code, signal_dates)
        startTime = dt.datetime.strptime(signal_dates[0], "%Y%m%d")
        endTime = dt.datetime.strptime(signal_dates[-1], "%Y%m%d")
        
        tickData = GD.getXQuantTickData2(stock_code, startTime, endTime, timeMode=2)
        transactionData = GD.getXQuantTransactionData2(stock_code, startTime, endTime, True, True, timeMode=2)
        for index in range(len(tickData)):
            if tickData[index] is not None and tickData[index]:
                d = tickData[index]['Date'][0]
                trans_data_path = trade_data_path + str(d)
                trans_data_name = trans_data_path + '/Data.pickle'
                if not py.exists(trans_data_path):
                    py.mkdir(trans_data_path) 
                # print(trans_data_name)
                # trans_data_name = "$21/test_makedir_1/601318.SH/20190201/Data1.pickle"
                try:
                    with py.open(trans_data_name,Absolute=False, mode='wb') as f:
                        pickle.dump((tickData[index], transactionData[index]), f) 
                except Exception as e:
                    print(e) 
        del tickData
        del transactionData               
        time2 = dt.datetime.now()
        log_error_fd.logger.info("stock {} cost time: {}".format(stock_code, time2 - time1))
        succeful_geted_stock_num = succeful_geted_stock_num + 1
        log_error_fd.logger.info("succefully get {} stocks data".format(succeful_geted_stock_num))
        gc.collect()
        # except Exception as e:
            # print(e)
            # log_error_fd.logger.info("stock: %s Failed", code[i])  
                                    
def get_trade(outTradeDataPath, signal_dates, log_file_path = "/app/data/666888/Logging/TradeData", stock_list = None):
    sys.path.append("Factor")
    sys.path.append("NonFactor")
    sys.path.append("Tag")
    sys.path.append("System")
    if stock_list is None:
        code = os.listdir(outTradeDataPath)
        # code = code_diff
        code.sort()
    else:
        code = stock_list
    log_err_file = log_file_path + "/" + "error.txt"
    if not os.path.exists(log_file_path):
        os.makedirs(log_file_path)
    log_error_fd = Logger(log_err_file, level='debug')
    # code = code[1200:]

    stock_num = len(code)
    for i in range(stock_num):
        backTestUnderlying = code[i]
        print("stage get trade {} {}/{}".format(backTestUnderlying, i+1, stock_num))
        stock_code = backTestUnderlying
        try:     
        # if True: 
            time1 = dt.datetime.now()  
            trade_data_path = outTradeDataPath + '/' + stock_code + "/"    
            if not os.path.exists(trade_data_path):
                os.makedirs(trade_data_path)
                             
            signal_dates.sort()
            log_error_fd.logger.debug("stock_code: %s, signal_dates: %s", stock_code, signal_dates)
            startTime = dt.datetime.strptime(signal_dates[0], "%Y%m%d")
            endTime = dt.datetime.strptime(signal_dates[-1], "%Y%m%d")
            
            tickData = GD.getXQuantTickData2(stock_code, startTime, endTime, timeMode=2)
            transactionData = GD.getXQuantTransactionData2(stock_code, startTime, endTime, True, True, timeMode=2)
            
            for index in range(len(tickData)):
                if tickData[index] is not None and tickData[index]:
                    d = tickData[index]['Date'][0]
                    trans_data_path = trade_data_path + "/" + str(d)
                    trans_data_name = trans_data_path + '/Data.pickle'
                    if not os.path.exists(trans_data_path):
                        os.makedirs(trans_data_path) 
                    with open(trans_data_name, 'wb') as f:
                        pickle.dump((tickData[index], transactionData[index]), f)  
                             
            del tickData
            del transactionData               
            time2 = dt.datetime.now()
            log_error_fd.logger.debug("total train time: %s", time2 - time1)

            # del signalEvaluate
            
            gc.collect()
        except Exception  as e:
            log_error_fd.logger.debug("train code: %s Failed", code[i])
            print(e)
def get_trade_paral(outTradeDataPath, signal_dates, ):
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
        pool.apply_async(get_trade, (outTradeDataPath, signal_dates, idx, edx, '/app/data/666888/Logging/TradeData'))
        idx = edx
    pool.close()
    pool.join()

def main():
    outTradeDataPath = "$21/test_makedir_1" 
    signal_dates = []
    start = dt.datetime(2019, 2, 1)
    end = dt.datetime(2019, 3, 2)
    while end > start:
        if start.weekday() < 5:
            signal_dates.append(start.strftime('%Y%m%d'))
        start = start + dt.timedelta(days=1)
        
    get_trade_to_hdfs(outTradeDataPath, signal_dates, stock_list=["601318.SH", "600030.SH"])
    #get_trade_paral(get_trade_to_hdfs, )
if __name__ == "__main__":
    main()
