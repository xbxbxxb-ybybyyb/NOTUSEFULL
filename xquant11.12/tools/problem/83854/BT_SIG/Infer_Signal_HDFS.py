# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 16:37:11 2017

@author: 006547
"""
import sys
import os 
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
from BT_SIG.ModelInferHDFS import ModelCNNLSTMLongShort
from Logger.Logger import Logger
import math
from xquant.pyfile import Pyfile
from System import DumpLoad
import datetime as dt
import gc
import pickle
import pandas as pd
import numpy as np
import json

def infer_signal(signalPath, absolutePath, factorAddress, tagNames, factorName, test_start_date, test_end_date, code=None, pid=-1):
    sliceLags = [160, 200, 240]
    open_tick_num = 21
    # 设置需要训练的因子
    factorIndex = list(range(20))
    # print(signalPath + "/ModelSignalDataSet/" )
    outSigPath =    signalPath + "/ModelSignalDataSet/" 
    outFactorPath = signalPath + "/ModelFactor/" 
    modelPath =   absolutePath + "/ModelSaved"
    if code is None:
        code = os.listdir(modelPath)
        code.sort()
        
    log_file_path = absolutePath + "/Logging/"
    log_err_file = log_file_path + "/" + "error.txt"
    if not os.path.exists(log_file_path):
        os.makedirs(log_file_path)
    log_error_fd = Logger(log_err_file, level='debug')
 
    py = Pyfile()
    # print(code)
    for i in range(0, len(code)):
        backTestUnderlying = "AlgoShaolin-" + code[i] + "-" + test_start_date + "-" + test_end_date
        # print(backTestUnderlying)
        stock_code = code[i]
        if i % 10==0:
            print("{} th stock of totally {} in pid {}".format(i,len(code), pid))
        try:     
        # if True: 
            time1 = dt.datetime.now()    
            
            log_file = log_file_path + "/" + backTestUnderlying + ".txt"
            if not os.path.exists(log_file_path):
                os.makedirs(log_file_path)
                
            log_fd = Logger(log_file, level='debug')
            log_fd.logger.debug("start to train model")
            log_fd.logger.debug("factors: %s", factorName)
            log_fd.logger.debug(code[i])
            if (not py.exists(factorAddress + backTestUnderlying + '.pickle')):
                log_fd.logger.debug('Not FactorData') 
                continue
            
            outputFactor, outputSubTag, tradingUnderlyingCode, factorNames = DumpLoad.loadOutput(factorAddress, backTestUnderlying + '.pickle')
            
            factorNameIndexs = {}
            for factor_name in factorName:
                for index in range(len(factorNames)):
                    if factor_name == factorNames[index]:
                        factorNameIndexs[factor_name] = index
                        break
                        
            if len(list(factorNameIndexs.keys())) != len(factorName):
                log_fd.logger.debug("unmatched num of factors")
                continue 
            
            check_valid_tags = False    
            for tag_name_list in tagNames:
                for tag_name in tag_name_list:
                    if not tag_name in outputSubTag[0][0]:
                        log_fd.logger.debug("unmatched num of tags: %s", tag_name)
                        check_valid_tags = True
                        break
                        
            if check_valid_tags:
                continue   
                        
            test_timestamp = {"timestamp": {}} 
            for index in range(len(outputSubTag[0])):
                timestamp = outputSubTag[0][index][tagNames[0][0]].startTimeStamp
                date_key = dt.datetime.fromtimestamp(timestamp).date().strftime('%Y%m%d')
                if not date_key in test_timestamp["timestamp"]:
                    test_timestamp["timestamp"][date_key] = []
                test_timestamp["timestamp"][date_key].append(timestamp)
                
            test_factor_data = {}    
            test_concat_factor_data = {}
            test_tag_data = {}
            test_dates = list(test_timestamp["timestamp"].keys())
            test_dates.sort()
            
            for factor_name in factorName:
                test_factor_data[factor_name] = {}
                for d in test_dates:
                    test_factor_data[factor_name][d] = []
                    
            for tag_name_list in tagNames:
                for tag_name in tag_name_list:
                    test_tag_data[tag_name] = {}
                    for d in test_dates:
                        test_tag_data[tag_name][d] = []
                                                                     
            for index in range(len(outputSubTag[0])):
                timestamp = outputSubTag[0][index][tagNames[0][0]].startTimeStamp
                date_key = dt.datetime.fromtimestamp(timestamp).date().strftime('%Y%m%d')
                
                for factor_name in factorName:
                    test_factor_data[factor_name][date_key].append(outputFactor[0][index][factorNameIndexs[factor_name]]) 
                
                for tag_name in test_tag_data:                 
                    test_tag_data[tag_name][date_key].append(outputSubTag[0][index][tag_name].returnRate)
                                                                                                                                                          
            for d in test_dates:
                test_concat_factor_data[d] = None
                for factor_name in factorName:               
                    if test_concat_factor_data[d] is None:
                        test_concat_factor_data[d] = np.array(test_factor_data[factor_name][d]).reshape(-1, 1)
                    else:
                        test_concat_factor_data[d] = np.concatenate((test_concat_factor_data[d], np.array(test_factor_data[factor_name][d]).reshape(-1, 1)), axis=1)                                    

            # 设置模型参数
            model_path = absolutePath + 'ModelSaved/' + stock_code + "/"
            if not os.path.exists(model_path):
                log_fd.logger.debug("mode not found %s", model_path)    
                continue
            model_init = {}
            paraModel = {"triggerRatio": 1,
                         "model_init": model_init, "tagNames": tagNames, "sliceLags": sliceLags,
                         "test_factor_data": test_concat_factor_data, "test_tag_data": test_tag_data, "test_timestamp": test_timestamp,
                         "open_tick_num": open_tick_num, "log_fd": log_fd,
                         "model_path": model_path, "stock_code": stock_code, "num_factors": len(factorName),
                         "factor_indexs": factorIndex, "factorNames": factorName}
                
            model = ModelCNNLSTMLongShort(paraModel=paraModel)
            # 训练模型
            daily_prediction = model.infer()
            sig_path = outSigPath + '/' + stock_code + "/"
            factor_path = outFactorPath + '/' + stock_code + "/"
            
            if not py.exists(sig_path):
                py.mkdir(sig_path)
                
            if not py.exists(factor_path):
                py.mkdir(factor_path) 
                       
            signal_dates = []                  
            for date in daily_prediction:
                if daily_prediction[date]["factors"]:
                    dt_frame = pd.DataFrame(data=daily_prediction[date]["factors"])
                    if not py.exists(factor_path + "/" + date):
                        py.mkdir(factor_path + "/" + date)
                    target_csv = factor_path + "/" + date + "/" + stock_code + "_" + date + ".csv"
                    py.create(target_csv)
                    py.write_csvfile(target_csv, dt_frame)
                if daily_prediction[date]["signals"]:
                    dt_frame = pd.DataFrame(data=daily_prediction[date]["signals"])
                    if not py.exists(sig_path + "/" + date):
                        py.mkdir(sig_path + "/" + date)
                    target_csv = sig_path + "/" + date + "/" + stock_code + "_" + date + ".csv"
                    py.create(target_csv)
                    py.write_csvfile(target_csv, dt_frame)
                    signal_dates.append(date)
                                                                             
            time2 = dt.datetime.now()
            log_fd.logger.debug("total train time: %s", time2 - time1)

            # del signalEvaluate
            
            gc.collect()
        except:
            log_fd.logger.debug("train code: %s Failed", code[i])
            log_error_fd.logger.debug("train code: %s Failed", code[i])

    log_error_fd.logger.debug("all finished")
    
def main():
    sys.path.append("Factor")
    sys.path.append("NonFactor")
    sys.path.append("Tag")
    sys.path.append("System")
    # modelPath = "/app/data/666888/ModelProduction/2018-10-01/20190102/ModelSaved"
    absolutePath = "/app/data/666888/ModelProduction/2018-10-01/20190102/" # model_path
    signalPath =                    "ModelProduction/2018-10-01" # out put path

    code =  [
                "000009.SZ",
            ]
    tagNames = [["1minLong", "1minShort"], ["2minLong", "2minShort"], ["5minLong", "5minShort"]]
    factorName = ['factorMAVolumeDistance40', 'factorDistanceBetweenVWAPPrice200', 'factorEmaSlicePressure', 
                  'factorTransPressureVol', 'factorDistanceToAvePrice', 'factorDistanceBetweenVWAPPrice100',
                  'factorOrderPressure', 'factorDistanceBetweenVWAPPrice40', 'factorDistanceBetweenVWAPPrice20', 
                  'factorMAVolumeDistance200', 'factorCrossPriceChangeSpeed', 'factorCrossPriceChangeRatio', 
                  'factorTransPressure', 'factorVolumeMagnification', 'factorMAVolumeDistance100', 'factorAccumSellPower', 
                  'factorAccumBuyPower', 'factorSpeed', 'factorMAVolumeDistance3', 'factorMAVolumeDistance20']
    test_start_date = "20190225093015"
    test_end_date =   "20190301145659"
    factorAddress = "output/calc_factor_2017_100/"
    infer_signal(signalPath, absolutePath, factorAddress, tagNames, factorName, test_start_date, test_end_date, code)
      
if __name__ == "__main__":
    main()
