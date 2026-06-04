import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
import gc
import datetime as dt
import pandas as pd
import numpy as np
from BT_SIG.ModelInferHDFS import ModelCNNLSTMLongShort
from System import DumpLoad
from Logger.Logger import Logger
from xquant.pyfile import Pyfile


def infer_signal(signalPath, absolutePath, factorAddress, tagNames, factorName, test_start_date, test_end_date,
                 code, pid):
    # 模型参数
    sliceLags = [160, 200, 240]
    open_tick_num = 21
    factorIndex = list(range(20))   # 设置需要训练的因子

    outSigPath = signalPath + "/ModelSignalDataSet/"
    outFactorPath = signalPath + "/ModelFactor/"

    log_file_path = absolutePath + "/Logging/"
    log_err_file = log_file_path + "/" + "error.txt"
    if not os.path.exists(log_file_path):
        os.makedirs(log_file_path)
    log_error_fd = Logger(log_err_file, level='debug')

    py = Pyfile()
    for i in range(0, len(code)):
        backTestUnderlying = "AlgoShaolin-" + code[i] + "-" + test_start_date + "-" + test_end_date
        stock_code = code[i]
        if i % 10 == 0:
            print("{} th stock of totally {} in pid {}".format(i, len(code), pid))
        try:
            time1 = dt.datetime.now()

            log_file = log_file_path + "/" + backTestUnderlying + ".txt"
            if not os.path.exists(log_file_path):
                os.makedirs(log_file_path)

            log_fd = Logger(log_file, level='debug')
            log_fd.logger.debug("start to train model")
            log_fd.logger.debug("factors: %s", factorName)
            log_fd.logger.debug(code[i])
            if not py.exists(factorAddress + backTestUnderlying + '.pickle'):
                log_fd.logger.debug('Not FactorData')
                continue

            outputFactor, outputSubTag, tradingUnderlyingCode, factorNames = \
                DumpLoad.loadOutput(factorAddress, backTestUnderlying + '.pickle')

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
                    if tag_name not in outputSubTag[0][0]:
                        log_fd.logger.debug("unmatched num of tags: %s", tag_name)
                        check_valid_tags = True
                        break

            if check_valid_tags:
                continue

            test_timestamp = {"timestamp": {}}
            for index in range(len(outputSubTag[0])):
                timestamp = outputSubTag[0][index][tagNames[0][0]].startTimeStamp
                date_key = dt.datetime.fromtimestamp(timestamp).date().strftime('%Y%m%d')
                if date_key not in test_timestamp["timestamp"]:
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
                    test_factor_data[factor_name][date_key].append(
                        outputFactor[0][index][factorNameIndexs[factor_name]])

                for tag_name in test_tag_data:
                    test_tag_data[tag_name][date_key].append(outputSubTag[0][index][tag_name].returnRate)

            for d in test_dates:
                test_concat_factor_data[d] = None
                for factor_name in factorName:
                    if test_concat_factor_data[d] is None:
                        test_concat_factor_data[d] = np.array(test_factor_data[factor_name][d]).reshape(-1, 1)
                    else:
                        test_concat_factor_data[d] = np.concatenate(
                            (test_concat_factor_data[d], np.array(test_factor_data[factor_name][d]).reshape(-1, 1)),
                            axis=1
                        )

            # 设置模型参数
            model_path = absolutePath + 'ModelSaved/' + stock_code + "/"
            if not os.path.exists(model_path):
                log_fd.logger.debug("mode not found %s", model_path)
                continue
            model_init = {}
            paraModel = {
                "triggerRatio": 1,
                "model_init": model_init,
                "tagNames": tagNames,
                "sliceLags": sliceLags,
                "test_factor_data": test_concat_factor_data,
                "test_tag_data": test_tag_data,
                "test_timestamp": test_timestamp,
                "open_tick_num": open_tick_num,
                "log_fd": log_fd,
                "model_path": model_path,
                "stock_code": stock_code,
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
        except Exception as e:
            print(code[i] + ": " + repr(e))
            log_fd.logger.debug("train code: %s Failed", code[i])
            log_fd.logger.debug(repr(e))
            log_error_fd.logger.debug("train code: %s Failed", code[i])

    log_error_fd.logger.debug("all finished")
