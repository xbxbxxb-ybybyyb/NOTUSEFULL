import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
import gc
import datetime as dt
import pandas as pd
from xquant.pyfile import Pyfile
from xquant.factordata import FactorData
from System.GetTradingDay import getTradingDay
from Logger.Logger import Logger
from InferSignalSingle.ModelInferHDFS import ModelCNNLSTMLongShort


def infer_signal(signalPath, absolutePath, libraryName, factorNames, tagNames, tagDict, test_start_date, test_end_date,
                 code, pid):
    # 模型参数
    sliceLags = [160, 200, 240]
    open_tick_num = 21
    factorIndex = list(range(20))   # 设置需要训练的因子

    log_file_path = absolutePath + "/Logging/"
    log_err_file = log_file_path + "/" + "error_big_universe.txt"
    if not os.path.exists(log_file_path):
        os.makedirs(log_file_path)
    log_error_fd = Logger(log_err_file, level='debug')

    tag_names_flattened = [tag_name for tag_pair in tagNames for tag_name in tag_pair]
    test_date_list = list(map(str, getTradingDay(int(test_start_date), int(test_end_date))))
    column_names = factorNames + [tagDict[tag_name] for tag_name in tag_names_flattened] + ["timestamp"]

    factor_data = FactorData()
    # py = Pyfile()

    for i in range(len(code)):
        if i % 10 == 0:
            print("{} th stock of totally {} in pid {}".format(i, len(code), pid))

        stock_code = code[i]

        if not os.path.exists(log_file_path):
            os.makedirs(log_file_path)

        log_file = log_file_path + "/" + stock_code + test_start_date + "-" + test_end_date + ".txt"
        log_fd = Logger(log_file, level='debug')
        log_fd.logger.debug("Start to infer {} in pid {}".format(stock_code, pid))

        try:
            time1 = dt.datetime.now()

            test_timestamp = {"timestamp": {}}
            test_factor_data = {}
            test_tag_data = {}
            for tag_name in tag_names_flattened:
                test_tag_data[tag_name] = {}

            for test_date in test_date_list:
                try:
                    factor_tag_timestamp_df = factor_data.get_factor_value(
                        libraryName,
                        stock_code,
                        test_date,
                        column_names
                    ).rename(columns={v: k for k, v in tagDict.items()})
                    test_factor_data[test_date] = factor_tag_timestamp_df[factorNames].values
                    test_timestamp["timestamp"][test_date] = factor_tag_timestamp_df["timestamp"].tolist()
                    for tag_name in tag_names_flattened:
                        test_tag_data[tag_name][test_date] = factor_tag_timestamp_df[tag_name].tolist()
                except:
                    log_fd.logger.debug('No factor data on {}, {}, {}'.format(test_date, stock_code, pid))
                    continue

            if not test_factor_data or not test_tag_data or not test_timestamp:
                log_fd.logger.debug('No data between {} and {}, {}, {}'
                                    .format(test_start_date, test_end_date, stock_code, pid))
                continue

            # 设置模型参数
            model_path = absolutePath + "ModelSaved/universe/"
            if not os.path.exists(model_path):
                log_fd.logger.debug("Model not found {}, {}, {}".format(model_path, stock_code, pid))
                raise Exception("Model not found")
            model_init = {}
            paraModel = {
                "triggerRatio": 1,
                "model_init": model_init,
                "tagNames": tagNames,
                "sliceLags": sliceLags,
                "test_factor_data": test_factor_data,
                "test_tag_data": test_tag_data,
                "test_timestamp": test_timestamp,
                "open_tick_num": open_tick_num,
                "log_fd": log_fd,
                "model_path": model_path,
                "stock_code": "universe",
                "num_factors": len(factorNames),
                "factor_indexs": factorIndex,
                "factorNames": factorNames
            }

            model = ModelCNNLSTMLongShort(paraModel=paraModel)

            # 训练模型
            daily_prediction = model.infer()

            # sig_path = signalPath + '/' + stock_code + "/"
            # if not py.exists(sig_path):
                # py.mkdir(sig_path)

            signal_dates = []
            for date in daily_prediction:
                if daily_prediction[date]["signals"]:
                    dt_frame = pd.DataFrame(data=daily_prediction[date]["signals"])
                    dt_frame = dt_frame.rename(
                        columns={
                            "Timestamp": "timestamp",
                            "Ticktime": "ticktime",
                            "1minLong": "prediction1minLong",
                            "1minShort": "prediction1minShort",
                            "2minLong": "prediction2minLong",
                            "2minShort": "prediction2minShort",
                            "5minLong": "prediction5minLong",
                            "5minShort": "prediction5minShort",
                            "1minLongTag": "tag1minLong",
                            "1minShortTag": "tag1minShort",
                            "2minLongTag": "tag2minLong",
                            "2minShortTag": "tag2minShort",
                            "5minLongTag": "tag5minLong",
                            "5minShortTag": "tag5minShort",
                        }
                    )
                    # if not py.exists(sig_path + "/" + date):
                        # py.mkdir(sig_path + "/" + date)
                    # target_csv = sig_path + "/" + date + "/" + stock_code + "_" + date + ".csv"
                    # py.create(target_csv)
                    # py.write_csvfile(target_csv, dt_frame)
                    factor_data.update_factor_value("ApolloBTSignals", dt_frame, stock_code, date)
                    signal_dates.append(date)

            time2 = dt.datetime.now()
            log_fd.logger.debug("total train time: %s", time2 - time1)

            gc.collect()
        except Exception as e:
            print(stock_code + ": " + repr(e))
            log_fd.logger.debug("Inferring {} in pid {} failed".format(stock_code, pid))
            log_fd.logger.debug(repr(e))
            log_error_fd.logger.debug("Inferring {} in pid {} failed".format(stock_code, pid))

    log_error_fd.logger.debug("{} all finished".format(pid))
