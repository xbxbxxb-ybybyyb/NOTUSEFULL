# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 16:37:11 2017

@author: 006547
"""
import sys
import os 
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
from Logger.Logger import Logger
import datetime as dt
import gc
import json
from ModelSystem.getAveTickVol import getVolMeanRaw, getVolMeanRawGroup
import System.GetValidTradingDay as GTD

def getMaxVolumePerOrder(symbol, back_test_dates, dayNum):
    maxVolumePerOrder = {}
    for cur_date in back_test_dates:
        pre_date = dt.datetime.fromtimestamp(dt.datetime.strptime(cur_date, "%Y%m%d").timestamp()  - 24 * 3600).date().strftime('%Y%m%d')  
        if not cur_date in maxVolumePerOrder:
            volumePerOrder = getVolMeanRaw(symbol, int(pre_date), dayNum)
            maxVolumePerOrder[cur_date] = volumePerOrder
    
    return maxVolumePerOrder
    
def getMaxVolumePerOrderGroup(symbol, back_test_dates, dayNum):
    maxVolumePerOrder = {}
    pre_date_list = []
    for cur_date in back_test_dates:
        pre_date = dt.datetime.fromtimestamp(dt.datetime.strptime(cur_date, "%Y%m%d").timestamp()  - 24 * 3600).date().strftime('%Y%m%d')  
        pre_date_list.append(int(pre_date))
    orderCapacitys = getVolMeanRawGroup(symbol, pre_date_list, dayNum)
    
    for i in range(len(back_test_dates)):       
        maxVolumePerOrder[back_test_dates[i]] = orderCapacitys[i]
    
    return maxVolumePerOrder    
                
def main():
    outOrderCapacityPath = "/data/user/666888/OrderCapacityCB/" 
    maxVolumePerOrderDayNum = 20

    start_end_dates = [20191101, 20200508]

    from xquant.bonddata import BondData
    fd = BondData()
    from System.TradingDay import getTradingDay
    stockSet = set()
    for d in getTradingDay(start_end_dates[0], start_end_dates[1]):
        stockSet = stockSet.union(fd.get_bond_set(str(d)))
    stock_list = list(stockSet)
    stock_list.sort()
    print(len(stock_list))

    log_file_path = "/data/user/666888/Logging/OrderCapacityCB"
    log_err_file = log_file_path + "/" + "error.txt"
    if not os.path.exists(log_file_path):
        os.makedirs(log_file_path)
    log_error_fd = Logger(log_err_file, level='debug')

    for i in range(250, 300):
        backTestUnderlying = stock_list[i]
        # print(backTestUnderlying)
        stock_code = backTestUnderlying
        print("{}, {}/{}".format(stock_code, i + 1, 300))
        try:     
        # if True: 
            time1 = dt.datetime.now()  
            signal_dates = GTD.getValidTradingDayList(stock_code, start_end_dates[0], start_end_dates[-1])
            for i in range(len(signal_dates)):
                signal_dates[i] = str(signal_dates[i])    
            order_capacity_path = outOrderCapacityPath + '/' + stock_code + "/"    
            if not os.path.exists(order_capacity_path):
                os.makedirs(order_capacity_path)
                             
            signal_dates.sort()
            # log_error_fd.logger.debug("stock_code: %s, signal_dates: %s", stock_code, signal_dates)                
            maxVolumePerOrders = getMaxVolumePerOrderGroup(stock_code, signal_dates, maxVolumePerOrderDayNum)
            # print (maxVolumePerOrders)
            
            if os.path.exists(order_capacity_path + '/OrderCapacity.json'):
                with open(order_capacity_path + '/OrderCapacity.json', "r") as f:
                    order_capacity = json.load(f)
                order_capacity["OrderCapacity"].update(maxVolumePerOrders)  
            else:
                order_capacity = {"code": stock_code, "OrderCapacity": maxVolumePerOrders}
            with open(order_capacity_path + '/OrderCapacity.json', "w") as f:
                 json.dump(order_capacity, f)
                           
            time2 = dt.datetime.now()
            log_error_fd.logger.debug("total train time: %s", time2 - time1)

            # del signalEvaluate
            
            gc.collect()
        except:
            log_error_fd.logger.debug("train code: %s Failed", stock_list[i])

    log_error_fd.logger.debug("all finished")
if __name__ == "__main__":
    main()
