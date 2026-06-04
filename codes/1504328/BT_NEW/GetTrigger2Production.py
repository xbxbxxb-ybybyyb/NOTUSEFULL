#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/6/16 13:52
import os
import pandas as pd
import json
from xquant.xqutils.xqfile import HDFSFile


def get_one_freq_trigger_ratio(input_dir, file):
    hf = HDFSFile()
    try:
        if file == 'TEMP' or file == '.tmp':
            return dict()
        trigger_ratio_dir = input_dir + file + '/triggerRatio.json'
        with hf.open(trigger_ratio_dir, 'rb') as f:
            data = f.read()
            data = json.loads(data)
    except:
        return dict()
    return data


def get_trigger2production(cv_start_date, cv_end_date, cv_next_date, csv_param_date, portfolio, signal_csv_dir, executor_str,
                           initialAmount, overwrite_params, is_use_csv=False):
    hf = HDFSFile()
    replace_all = True
    output_dir = 'production_triggers/EverestSep/'
    if replace_all:
        if hf.exists(output_dir):
            hf.delete(output_dir, recursive=True)
        hf.mkdir(output_dir)

    hdfs_root = "cv/Stock/Results"
    stock_list = sorted(pd.read_csv("/data/user/015629/StockPool/stock_1s_stock_list.csv")["stock"].tolist())
    for file in stock_list:
        code_trigger_ratios = dict()

        for freq in ["036", "147", "258"]:
            portfolio = "Stock1S-{}".format(freq)
            signal_csv_dir = "BigEasy{}Signals".format(freq)
            result_dir_name = 'cv-{}-{}_{}-{}-{}-{}-{}-{}-{}/'.format(cv_start_date, cv_end_date, cv_next_date, portfolio,
                                                                  signal_csv_dir, executor_str,
                                                                  initialAmount,
                                                                  str(overwrite_params["maxTurnoverPerOrder"] // 10000),
                                                                  str(overwrite_params["maxExposure"] // 10000))
            input_dir = os.path.join(hdfs_root, result_dir_name)
            trigger_dict = get_one_freq_trigger_ratio(input_dir, file)
            if not trigger_dict:
                print(" Empty Trigger Ratio: {}-{} ".format(file, freq))
                trigger_dict = dict()
                trigger_dict["shortTriggerRatio"] = -9999
                trigger_dict["shortCloseRatio"] = 0
                trigger_dict["shortRiskRatio"] = 0
                trigger_dict["longTriggerRatio"] = 9999
                trigger_dict["longCloseRatio"] = 0
                trigger_dict["longRiskRatio"] = 0
            code_trigger_ratios.update({freq: trigger_dict})

        with hf.open(output_dir + file + '.json', 'wb') as f:
            json.dump(code_trigger_ratios, f)


if __name__ == "__main__":
    cv_start_date = "20210301"
    cv_end_date = "20210331"
    cv_next_date = "20210401"
    csv_param_date = "20210401"
    portfolio = "Stock1S"
    signal_csv_dir = "BigEasy036Signals"
    executor_str = "SignalExecutorEasy"
    initialAmount = 10 * 100000000
    overwrite_params = {'maxTurnoverPerOrder': 1800000, 'maxExposure': 8000000}
    is_use_csv = False
    get_trigger2production(cv_start_date, cv_end_date, cv_next_date, csv_param_date, portfolio, signal_csv_dir, executor_str,
                           initialAmount, overwrite_params, is_use_csv)