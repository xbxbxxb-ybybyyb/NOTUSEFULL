# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 16:37:11 2017

@author: 006547
"""
import sys
import os 
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
from BT_SIG.ModelInfer import ModelCNNLSTMLongShort
from Logger.Logger import Logger
import math
import datetime as dt
import gc
import pickle
import pandas as pd
import numpy as np
import json
from tqdm import tqdm

def infer_signal(modelPath, absolutePath, factorAddress, tagNames, factorName, test_start_date, test_end_date, code=None, pid=-1):



    # tagNames = [["5minLong", "5minShort"]]
    # sliceLags = [240]
    sliceLags = [160, 200, 240]
    open_tick_num = 21
    # 设置需要训练的因子
    factorIndex = list(range(20))
    outSigPath = absolutePath + "/ModelSignalDataSet/" 
    outFactorPath = absolutePath + "/ModelFactor/" 
    # print(outSigPath)
    maxVolumePerOrderDayNum = 20
    if code is None:
        code = os.listdir(modelPath)
        code.sort()
        
    log_file_path = absolutePath + "/Logging/"
    log_err_file = log_file_path + "/" + "error.txt"
    if not os.path.exists(log_file_path):
        os.makedirs(log_file_path)
    log_error_fd = Logger(log_err_file, level='error')
    # code = code[600:]
    stock_num = len(code)

    for i in range(stock_num): 
        backTestUnderlying = code[i]
       # print("pid:{} {}---{}/{}, {}-{}".format(pid, backTestUnderlying, i+1, stock_num, test_start_date, test_end_date))
        stock_code = backTestUnderlying
        # try:     
        try: 
            time1 = dt.datetime.now()    
            
            log_file = log_file_path + "/" + backTestUnderlying + ".txt"
            if not os.path.exists(log_file_path):
                os.makedirs(log_file_path)
                
            log_fd = Logger(log_file, level='debug')
            log_fd.logger.debug("start to train model")
            log_fd.logger.debug("factors: %s", factorName)
            log_fd.logger.debug(code[i])
                                    
            train_factor_data = {}
            train_concat_factor_data = {}
            train_tag_data = {}
            train_timestamp = {"timestamp": {}} 
            
            test_factor_data = {}
            test_concat_factor_data = {}
            test_tag_data = {}
            test_timestamp = {"timestamp": {}} 
            
            # if stock_code[0] == '6':
                # stock_code = stock_code + '.SH'
                
            # else:
                # stock_code = stock_code + '.SZ'
            data_path = factorAddress + "/" + stock_code   
            model_init = {}
            if not os.path.exists(data_path):
                log_fd.logger.info("no h5 data: %s", stock_code)
                continue
                
            with pd.HDFStore(data_path + "/timestamp", "r") as h5_data:
                total_dates = h5_data.keys()
               
                total_dates.sort()
                total_dates = np.array(total_dates)
                
                test_dates = total_dates[total_dates >= "/" + test_start_date]
                test_dates = test_dates[test_dates <= "/" + test_end_date].tolist()
                
                log_fd.logger.debug("total test find days of %s is: %d", stock_code, len(test_dates))
                                
                for d in test_dates:
                    test_timestamp["timestamp"][d] = np.array(h5_data[d][:]).reshape(-1).tolist()
            if len(test_dates) == 0:
                print("test dates is 0")
                continue
            for factor_name in factorName:                
                test_factor_data[factor_name] = {}
                with pd.HDFStore(data_path + "/" + factor_name,'r') as h5_data:                   
                    for d in test_dates:
                        test_factor_data[factor_name][d] = np.array(h5_data[d][:])
                                                                    
            for d in test_dates:
                test_concat_factor_data[d] = None
                for factor_name in factorName:               
                    if test_concat_factor_data[d] is None:
                        test_concat_factor_data[d] = test_factor_data[factor_name][d]
                    else:
                        test_concat_factor_data[d] = np.concatenate((test_concat_factor_data[d], test_factor_data[factor_name][d]), axis=1)  
                              
            for tag_name_list in tagNames:
                for tag_name in tag_name_list:                    
                    test_tag_data[tag_name] = {}
                    with pd.HDFStore(data_path + "/" + tag_name,'r') as h5_data:                        
                        for d in test_dates:
                            test_tag_data[tag_name][d] = np.array(h5_data[d][:]).reshape(-1).tolist()

            # 设置模型参数
            model_path = modelPath + "/" + backTestUnderlying + "/"
            if not os.path.exists(model_path):
                log_fd.logger.debug("mode not found %s", model_path)    
                continue
            paraModel = {"triggerRatio": 1,
                         "model_init": model_init, "tagNames": tagNames, "sliceLags": sliceLags,
                         "train_factor_data": train_concat_factor_data, "train_tag_data": train_tag_data, "train_timestamp": train_timestamp,
                         "test_factor_data": test_concat_factor_data, "test_tag_data": test_tag_data, "test_timestamp": test_timestamp,
                         "open_tick_num": open_tick_num, "log_fd": log_fd,
                         "model_path": model_path, "stock_code": stock_code, "num_factors": len(factorName),
                         "factor_indexs": factorIndex, "factorNames": factorName}
                
            model = ModelCNNLSTMLongShort(paraModel=paraModel)
            # 训练模型
            daily_prediction = model.infer()
            sig_path = outSigPath + '/' + stock_code + "/"
            factor_path = outFactorPath + '/' + stock_code + "/"
            
            if not os.path.exists(sig_path):
                os.makedirs(sig_path)
                
            if not os.path.exists(factor_path):
                os.makedirs(factor_path) 
                       
            signal_dates = []                  
            for date in daily_prediction:
                if daily_prediction[date]["factors"]:
                    dt_frame = pd.DataFrame(data=daily_prediction[date]["factors"])
                    if not os.path.exists(factor_path + "/" + date):
                        os.makedirs(factor_path + "/" + date)
                    dt_frame.to_csv(factor_path + "/" + date + "/" + stock_code + "_" + date + ".csv", index=False)
                if daily_prediction[date]["signals"]:
                    dt_frame = pd.DataFrame(data=daily_prediction[date]["signals"])
                    if not os.path.exists(sig_path + "/" + date):
                        os.makedirs(sig_path + "/" + date)
                    dt_frame.to_csv(sig_path + "/" + date + "/" + stock_code + "_" + date + ".csv", index=False)
                    signal_dates.append(date)
                                                                             
            time2 = dt.datetime.now()
            log_fd.logger.debug("total train time: %s", time2 - time1)

            # del signalEvaluate
            
            gc.collect()
        except Exception as ex:
            print(ex)
            log_fd.logger.debug("train code: %s Failed", code[i])
            log_error_fd.logger.debug("train code: %s Failed", code[i])

    log_error_fd.logger.debug("all finished")


         
def main():
    sys.path.append("Factor")
    sys.path.append("NonFactor")
    sys.path.append("Tag")
    sys.path.append("System")
    modelPath = "/app/data/666888/ModelProduction/2018-09-01/20181210/ModelSaved"
    absolutePath = "/app/data/666888/ModelProduction/2018-09-01/20181210"
    code =  [
                "603128.SH",
                "600901.SH",
                "603127.SH",
                "002411.SZ",
                "600550.SH",
                "603501.SH",
                "002309.SZ",
                "600658.SH",
                "600831.SH",
                "603283.SH",
                "603612.SH"
                ]
    tagNames = [["1minLong", "1minShort"], ["2minLong", "2minShort"], ["5minLong", "5minShort"]]
    factorName = ['factorMAVolumeDistance40', 'factorDistanceBetweenVWAPPrice200', 'factorEmaSlicePressure', 
                  'factorTransPressureVol', 'factorDistanceToAvePrice', 'factorDistanceBetweenVWAPPrice100',
                  'factorOrderPressure', 'factorDistanceBetweenVWAPPrice40', 'factorDistanceBetweenVWAPPrice20', 
                  'factorMAVolumeDistance200', 'factorCrossPriceChangeSpeed', 'factorCrossPriceChangeRatio', 
                  'factorTransPressure', 'factorVolumeMagnification', 'factorMAVolumeDistance100', 'factorAccumSellPower', 
                  'factorAccumBuyPower', 'factorSpeed', 'factorMAVolumeDistance3', 'factorMAVolumeDistance20']
    test_start_date = "2018-12-09"
    test_end_date = "2019-01-03"
    factorAddress = "/app/data/666888/AppleData"
    infer_signal(modelPath, absolutePath, factorAddress, tagNames, factorName, test_start_date, test_end_date, code)
    
    # code =  [
        # "603128.SH",
        # "600901.SH",
        # "603127.SH",
        # "002411.SZ",
                    # "600550.SH",
                    # "603501.SH",
                    # "002309.SZ",
                    # "600658.SH",
                    # "600831.SH",
                    # "603283.SH",
                    # "603612.SH"
                    # ]
    # # code = code_diff
    # # code.sort()
    # processNum = 3
    # baseNum = len(code) // processNum
    # remains = len(code) % processNum
    # pool = Pool(processes=processNum)
    # idx = 0
    
    # for index in range(processNum):
        # if index < remains:
            # edx = idx + baseNum + 1
        # else:
            # edx = idx + baseNum
        # pool.apply_async(infer_signal, (modelPath, rstPath, factorAddress, tagNames, factorName, test_start_date, test_end_date, code[idx: edx], index))
        # idx = edx
    # pool.close()
    # pool.join()
    
if __name__ == "__main__":
    main()
