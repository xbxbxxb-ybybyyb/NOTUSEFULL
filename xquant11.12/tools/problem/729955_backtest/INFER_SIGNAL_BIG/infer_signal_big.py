import sys
import os

sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
import gc
import json
import datetime as dt
import pandas as pd
import numpy as np
from System.TradingDay import getTradingDay
from Logger.Logger import Logger
from INFER_SIGNAL_SINGLE.ModelInferHDFS import ModelCNNLSTMLongShort
from xquant.factordata import FactorData


def infer_signal(absolutePath, libraryName, libraryNameS, factorNames, factorNamesS, tagNames, tagDict,
                 test_start_date, test_end_date, code, pid, model_ver):
    with open("/data/user/666888/WuKong/CBMap/CBMap_{}.json".format(max(int(test_end_date), 20200403)), "r") as f:
        cbmap = json.load(f)

    factor_data = FactorData()

    # 模型参数
    sliceLags = [160, 200, 240]
    open_tick_num = 21
    factorIndex = list(range(20))  # 设置需要训练的因子

    log_file_path = absolutePath + "/Logging/"
    log_err_file = log_file_path + "/error_big_universe_" + pid + ".txt"
    if not os.path.exists(log_file_path):
        os.makedirs(log_file_path)
    log_error_fd = Logger(log_err_file, level='debug')

    tag_names_flattened = [tag_name for tag_pair in tagNames for tag_name in tag_pair]
    factor_names_flattened = [tag_name for tag_pair in factorNames for tag_name in tag_pair]
    factor_namesS_flattened = [tag_name for tag_pair in factorNamesS for tag_name in tag_pair]

    test_date_list = list(map(str, getTradingDay(int(test_start_date), int(test_end_date))))

    for k in range(len(code)):
        if k % 10 == 0:
            print("{} th stock of totally {} in pid {}".format(k, len(code), pid))

        stock_code = code[k]

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
                    try:
                        factor_tag_timestamp_df_l = []
                        for i in range(len(libraryName)):
                            if i == 0:
                                factor_tag_timestamp_df_l.append(
                                    factor_data.get_factor_value(
                                        libraryName[i],
                                        stock_code,
                                        test_date,
                                        factorNames[i] + ["timestamp"]
                                        + [tagDict[tag_name] for tag_name in tag_names_flattened]
                                    ).rename(columns={v: k for k, v in tagDict.items()})
                                )
                            else:
                                factor_tag_timestamp_df_l.append(
                                    factor_data.get_factor_value(
                                        libraryName[i],
                                        stock_code,
                                        test_date,
                                        factorNames[i]
                                    )
                                )

                        for i in range(len(factor_tag_timestamp_df_l)):
                            if i == 0:
                                length = factor_tag_timestamp_df_l[i].shape[0]
                            else:
                                if factor_tag_timestamp_df_l[i].shape[0] != length:
                                    raise Exception("Data length unmatched, {}, {}", stock_code, test_date)
                        factor_tag_timestamp_df = pd.concat(factor_tag_timestamp_df_l, axis=1)
                    except:
                        log_fd.logger.debug('No Factor Data {}, {}, {}'.format(test_date, stock_code, pid))
                        continue

                    for zg in cbmap[stock_code]:
                        try:
                            factor_tag_timestamp_df_stock_l = []
                            for i in range(len(libraryName)):
                                if i == 0:
                                    factor_tag_timestamp_df_stock_l.append(
                                        factor_data.get_factor_value(
                                            libraryNameS[i],
                                            zg,
                                            test_date,
                                            factorNamesS[i] + ["timestamp"]
                                        )
                                    )
                                else:
                                    factor_tag_timestamp_df_stock_l.append(
                                        factor_data.get_factor_value(
                                            libraryNameS[i],
                                            zg,
                                            test_date,
                                            factorNamesS[i]
                                        )
                                    )

                            for i in range(len(factor_tag_timestamp_df_stock_l)):
                                if i == 0:
                                    length = factor_tag_timestamp_df_stock_l[i].shape[0]
                                else:
                                    if factor_tag_timestamp_df_stock_l[i].shape[0] != length:
                                        raise Exception("Data length unmatched, {}, {}", stock_code, test_date)
                            factor_tag_timestamp_df_stock = pd.concat(factor_tag_timestamp_df_stock_l, axis=1)

                            mc = factor_data.get_factor_value(
                                "XHFDataLib",
                                "{}_T".format(zg),
                                test_date,
                                ["T_Timestamp", "T_IsMock"]
                            ).set_index("T_Timestamp")["T_IsMock"]
                            break
                        except:
                            pass
                    else:
                        log_fd.logger.debug('No Stock Data {}, {}, {}'.format(test_date, stock_code, pid))
                        factor_tag_timestamp_df_stock = None
                        mc = None

                    test_factor_data[test_date] = concatCBStockFactor(
                        factor_tag_timestamp_df,
                        factor_tag_timestamp_df_stock,
                        factor_names_flattened,
                        factor_namesS_flattened,
                        lag=0,
                        # lag=1,
                        # isUseMocked=True,
                        # stockMockSeries=None,
                        isUseMocked=False,
                        stockMockSeries=mc,
                    )
                    test_timestamp["timestamp"][test_date] = factor_tag_timestamp_df["timestamp"].tolist()
                    for tag_name in tag_names_flattened:
                        test_tag_data[tag_name][test_date] = factor_tag_timestamp_df[tag_name].tolist()
                except Exception as e:
                    log_fd.logger.debug('Unexpected Error {}, {}, {}: {}'.format(test_date, stock_code, pid, e))
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
                "num_factors": len(factor_names_flattened + factor_namesS_flattened),
                "factor_indexs": factorIndex,
                "factorNames": factor_names_flattened + factor_namesS_flattened
            }

            model = ModelCNNLSTMLongShort(paraModel=paraModel)

            # 训练模型
            daily_prediction = model.infer()

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

                    factor_data.update_factor_value(model_ver, dt_frame, stock_code, date)
                    signal_dates.append(date)

            time2 = dt.datetime.now()
            log_fd.logger.debug("total train time: %s", time2 - time1)

            del test_factor_data
            del model
            gc.collect()
        except Exception as e:
            print(stock_code + ": " + repr(e))
            log_fd.logger.debug("Inferring {} in pid {} failed".format(pid, stock_code))
            log_fd.logger.debug(repr(e))
            log_error_fd.logger.debug("Inferring {} in pid {} failed".format(pid, stock_code))

    log_error_fd.logger.debug("{} all finished".format(pid))


def concatCBStockFactor(cbFactorDF, stockFactorDF, cbFN, stockFN, lag=0, isUseMocked=True, stockMockSeries=None):
    if stockFactorDF is None:
        return np.concatenate([cbFactorDF.loc[:, cbFN].values, np.zeros([cbFactorDF.shape[0], len(stockFN)])], axis=1)

    cbTimestamp = cbFactorDF["timestamp"].values
    stockTimestamp = stockFactorDF["timestamp"].values

    cbFactor = cbFactorDF.loc[:, cbFN].values
    stockFactor = stockFactorDF.loc[:, stockFN].values

    if not isUseMocked:
        stockIsMocked = stockFactorDF["timestamp"].map(stockMockSeries).fillna(1).values
    else:
        stockIsMocked = np.zeros(stockFactorDF.shape[0])

    resStockFactor = []

    stockIdx = 0
    notMockedStockIdx = 0
    for cbIdx in range(cbFactor.shape[0]):
        while stockIdx + 1 < stockFactor.shape[0] and stockTimestamp[stockIdx + 1] + lag <= cbTimestamp[cbIdx]:
            stockIdx += 1
            if stockIsMocked[stockIdx] == 0:
                notMockedStockIdx = stockIdx

        if cbTimestamp[cbIdx] < stockTimestamp[notMockedStockIdx] + lag:
            resStockFactor.append(np.zeros(len(stockFN)))
            continue

        resStockFactor.append(stockFactor[notMockedStockIdx, :])

    resStockFactor = np.vstack(resStockFactor)

    return np.concatenate([cbFactor, resStockFactor], axis=1)
