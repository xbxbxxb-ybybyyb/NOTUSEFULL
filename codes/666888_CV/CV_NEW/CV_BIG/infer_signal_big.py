# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 16:37:11 2017

@author: 006547
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
import gc
import datetime as dt
import pandas as pd
import numpy as np
from BT_SIG.ModelInfer import ModelCNNLSTMLongShort
from Logger.Logger import Logger
from xquant.pyfile import Pyfile


def infer_signal(signalPath, absolutePath, factorAddress, tagNames, factorName, test_start_date, test_end_date,
                 code, pid):
    sys.path.append("Factor")
    sys.path.append("NonFactor")
    sys.path.append("Tag")
    sys.path.append("System")

    sliceLags = [160, 200, 240]
    open_tick_num = 21

    # 设置需要训练的因子
    factorIndex = list(range(20))

    outSigPath = signalPath + "/ModelSignalDataSet/"
    outFactorPath = signalPath + "/ModelFactor/"

    log_file_path = absolutePath + "/Logging2/"
    log_err_file = log_file_path + "error.txt"
    if not os.path.exists(log_file_path):
        os.makedirs(log_file_path)
    log_error_fd = Logger(log_err_file, level='debug')

    py = Pyfile()
    for i in range(len(code)):
        if i % 10 == 0:
            print("{} th stock of totally {} in pid {}".format(i, len(code), pid))

        if os.path.exists(outSigPath + "/" + code[i]):
            continue

        backTestUnderlying = code[i]
        print(backTestUnderlying, pid)
        stock_code = backTestUnderlying

        try:
            time1 = dt.datetime.now()

            log_file = log_file_path + "/" + backTestUnderlying + ".txt"
            if not os.path.exists(log_file_path):
                os.makedirs(log_file_path)

            log_fd = Logger(log_file, level='debug')
            log_fd.logger.debug("start to train model")
            log_fd.logger.debug("factors: %s", factorName)
            log_fd.logger.debug(code[i])

            train_concat_factor_data = {}
            train_tag_data = {}
            train_timestamp = {"timestamp": {}}

            test_factor_data = {}
            test_concat_factor_data = {}
            test_tag_data = {}
            test_timestamp = {"timestamp": {}}

            data_path = factorAddress + "/" + stock_code
            model_init = {}
            if not os.path.exists(data_path):
                log_fd.logger.debug("no h5 data: %s", stock_code)
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
                continue
            for factor_name in factorName:
                test_factor_data[factor_name] = {}

                with pd.HDFStore(data_path + "/" + factor_name, 'r') as h5_data:
                    for d in test_dates:
                        test_factor_data[factor_name][d] = np.array(h5_data[d][:])

            for d in test_dates:
                test_concat_factor_data[d] = None
                for factor_name in factorName:
                    if test_concat_factor_data[d] is None:
                        test_concat_factor_data[d] = test_factor_data[factor_name][d]
                    else:
                        test_concat_factor_data[d] = np.concatenate(
                            (test_concat_factor_data[d], test_factor_data[factor_name][d]), axis=1)

            for tag_name_list in tagNames:
                for tag_name in tag_name_list:
                    test_tag_data[tag_name] = {}
                    with pd.HDFStore(data_path + "/" + tag_name, 'r') as h5_data:
                        for d in test_dates:
                            test_tag_data[tag_name][d] = np.array(h5_data[d][:]).reshape(-1).tolist()

            # 设置模型参数
            model_path = absolutePath + 'ModelSaved/universe/'
            if not os.path.exists(model_path):
                log_fd.logger.debug("mode not found %s", model_path)
                continue

            paraModel = {
                "triggerRatio": 1,
                "model_init": model_init,
                "tagNames": tagNames,
                "sliceLags": sliceLags,
                "train_factor_data": train_concat_factor_data,
                "train_tag_data": train_tag_data,
                "train_timestamp": train_timestamp,
                "test_factor_data": test_concat_factor_data,
                "test_tag_data": test_tag_data,
                "test_timestamp": test_timestamp,
                "open_tick_num": open_tick_num,
                "log_fd": log_fd,
                "model_path": model_path,
                "stock_code": 'universe',
                "num_factors": len(factorName),
                "factor_indexs": factorIndex,
                "factorNames": factorName
            }

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

            gc.collect()
        except:
            log_fd.logger.debug("train code: %s Failed", code[i])
            log_error_fd.logger.debug("train code: %s Failed", code[i])

    log_error_fd.logger.debug("all finished")
