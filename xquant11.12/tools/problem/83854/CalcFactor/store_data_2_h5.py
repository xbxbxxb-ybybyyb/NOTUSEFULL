# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 16:37:11 2017

@author: 006547
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
from xquant.pyfile import Pyfile
from System import DumpLoad
import math
import datetime as dt
import gc
# from multiprocessing import Pool
# import multiprocessing
import pickle
import numpy as np
import random
import json
import copy
import h5py
import pandas as pd
import os

def store_data(code, absolutePath, factorAddress, pid=0):
    sys.path.append("Factor")
    sys.path.append("NonFactor")
    sys.path.append("Tag")
    sys.path.append("System")


    # 读取数据：
    # GPUID = 0
    # 设置是否需要加载因子去计算预测值

    tagNames = [["1minLong", "1minShort"], ["2minLong", "2minShort"], ["5minLong", "5minShort"]]
    tag_names = ["1minLong", "1minShort", "2minLong", "2minShort", "5minLong", "5minShort"]
    tagName = tagNames[0][0]

    py = Pyfile()
    # code = code[50:]
    total = len(code)


    for i in range(total): 
        backTestUnderlying = code[i]
        print("pid {}: {} {}/{}".format(backTestUnderlying, pid, i+1, total))
        stock_code = backTestUnderlying.split('-')[1]
        file_name = factorAddress + backTestUnderlying
        if not py.exists(file_name):
            print('{} is not exists'.format(file_name))
        # if not os.path.exists(file_name):
            # print('{} is not exists'.format(file_name))
        else:
            # print('sssssssSSSSSSSSSSSSSSSSSSSSSSS')
            # return
            outputFactor = []
            outputSubTag = []
            tradingUnderlyingCode = []
            factorName = []

            try:
                import time

                outputFactor, outputSubTag, tradingUnderlyingCode, factorName = DumpLoad.loadOutput(factorAddress, backTestUnderlying)
                all_train_date_num = 0
                all_dates_dict = {}
                for index in range(len(outputSubTag[0])):
                    timestamp = outputSubTag[0][index][tagName].startTimeStamp
                    all_dates_dict.update({dt.datetime.fromtimestamp(timestamp).date().strftime('%Y-%m-%d'): timestamp})
                all_dates = list(all_dates_dict.keys())
                all_dates.sort()
                all_date_num = len(all_dates)
                                    
                factors = {}
                timestamps = {"timestamp": {}} 
                tags = {}
                
                for tag_name in outputSubTag[0][0].keys():
                    tags[tag_name] = {}
                    for date in all_dates:
                        tags[tag_name][date] = []
                        
                for name in factorName:
                    factors[name] = {}
                    for date in all_dates:
                        factors[name][date] = []
                                                
                for date in all_dates:
                    timestamps["timestamp"][date] = []           
                     
                for index in range(len(outputSubTag[0])):
                    timestamp = outputSubTag[0][index][tagName].startTimeStamp
                    date_key = dt.datetime.fromtimestamp(timestamp).date().strftime('%Y-%m-%d')
                    timestamps["timestamp"][date_key].append(timestamp)
                    
                    for factor_index in range(len(factorName)):
                        factors[factorName[factor_index]][date_key].append(outputFactor[0][index][factor_index]) 
                    
                    for tag_name in tags:
                        tags[tag_name][date_key].append(outputSubTag[0][index][tag_name].returnRate)
                        
                store_path = absolutePath + '/' + stock_code
                # print("start", time.time())
                
                if not os.path.exists(store_path):
                    os.makedirs(store_path)
                    
                for factor_name in factors: 
                    with pd.HDFStore(store_path + "/" + factor_name, 'a', complevel=4) as h5:
                        for d in factors[factor_name]:
                            h5[d] = pd.DataFrame(factors[factor_name][d])
                        
                for tag_name in tags: 
                    with pd.HDFStore(store_path + "/" + tag_name, 'a', complevel=4) as h5:
                        for d in tags[tag_name]:
                            h5[d] = pd.DataFrame(tags[tag_name][d])   
                            
                with pd.HDFStore(store_path + "/" + "timestamp", 'a', complevel=4) as h5:
                    for d in timestamps["timestamp"]:
                        h5[d] = pd.DataFrame(timestamps["timestamp"][d])  
                # print("end", time.time())
                                           
                outputFactor = []
                outputSubTag = []
                tradingUnderlyingCode = []
                factorName = []
            except Exception as e:
                print(e)
               
                print ("update " + stock_code + " failed!")
                
                
def main():
    codes = [ 
            # "AlgoShaolin-002309.SZ-20181209093015-20190103145659.pickle",
            # "AlgoShaolin-002411.SZ-20181209093015-20190103145659.pickle",
            # "AlgoShaolin-600550.SH-20181209093015-20190103145659.pickle",
            # "AlgoShaolin-600658.SH-20181209093015-20190103145659.pickle",
            "AlgoShaolin-600831.SH-20181209093015-20190103145659.pickle",
            # "AlgoShaolin-600901.SH-20181209093015-20190103145659.pickle",
            # "AlgoShaolin-603127.SH-20181209093015-20190103145659.pickle",
            # "AlgoShaolin-603128.SH-20181209093015-20190103145659.pickle",
            # "AlgoShaolin-603283.SH-20181209093015-20190103145659.pickle",
            # "AlgoShaolin-603501.SH-20181209093015-20190103145659.pickle",
            # "AlgoShaolin-603612.SH-20181209093015-20190103145659.pickle"
           
            ]
    absolutePath = "/app/data/666888/AppleData/"
    factorAddress = 'output/all_300_500_20170101_20180101_10_all_test/'
    store_data(code=codes, absolutePath=absolutePath, factorAddress=factorAddress)

if __name__ == "__main__":
    main()
