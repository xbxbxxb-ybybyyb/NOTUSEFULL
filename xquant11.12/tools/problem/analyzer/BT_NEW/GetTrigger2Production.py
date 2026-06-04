#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/6/16 13:52
import os
import pandas as pd
import json
from xquant.xqutils.xqfile import HDFSFile

def get_trigger2production(cv_start_date, cv_end_date, cv_next_date, csv_param_date, portfolio, signal_csv_dir, executor_str,
                           initialAmount, overwrite_params, is_use_csv=False):
    hf = HDFSFile()
    replace_all = True
    # replace_all = False
    output_dir = 'production_triggers/Easy/'
    if replace_all:
        if hf.exists(output_dir):
            hf.delete(output_dir, recursive=True)
        hf.mkdir(output_dir)

    result_dir_name = 'cv-{}-{}_{}-{}-{}-{}-{}-{}-{}/'.format(cv_start_date, cv_end_date, cv_next_date, portfolio,
                                                               signal_csv_dir, executor_str,
                                                               initialAmount,
                                                               str(overwrite_params["maxTurnoverPerOrder"] // 10000),
                                                               str(overwrite_params["maxExposure"] // 10000) )
    if portfolio == "EasyTrack":
        is_use_csv = True

    if not is_use_csv:

        hdfs_root = "cv/Stock/Results"
        input_dir = os.path.join(hdfs_root, result_dir_name)
        files = hf.listdir(input_dir)
        for file in files:
            if file == 'TEMP' or file == '.tmp':
                continue
            trigger_ratio_dir = input_dir + file + '/triggerRatio.json'
            with hf.open(trigger_ratio_dir, 'rb') as f:
                data = f.read()
                data = json.loads(data)
            with hf.open(output_dir + file + '.json', 'wb') as f:
                json.dump(data, f)

    else:
        trigger_csv_file = "/data/user/015629/EasyInferSignal/portfolioInfo/parameters/easy_live_params_{}.csv".format(
            csv_param_date)
        trigger_file = pd.read_csv(trigger_csv_file).dropna(how='any', axis=0)
        target_code = trigger_file["symbol"].tolist()

        for symbol in target_code:
            trigger_dict = {}
            trigger_info = trigger_file[trigger_file["symbol"] == symbol].iloc[0].to_dict()
            trigger_dict["shortTriggerRatio"] = trigger_info.get("shortTriggerRatio")
            trigger_dict["shortCloseRatio"] = trigger_info.get("shortCloseRatio")
            trigger_dict["shortRiskRatio"] = trigger_info.get("shortRiskRatio")
            trigger_dict["longTriggerRatio"] = trigger_info.get("longTriggerRatio")
            trigger_dict["longCloseRatio"] = trigger_info.get("longCloseRatio")
            trigger_dict["longRiskRatio"] = trigger_info.get("longRiskRatio")

            json_file = output_dir + "{}.json".format(symbol)
            with hf.open(json_file, "wb") as f:
                json.dump(trigger_dict, f)

    name = result_dir_name.split('/')[0]
    with hf.open(output_dir + 'come_from.json', 'wb') as f:
        json.dump(name, f)
        

if __name__ == "__main__":
    cv_start_date = "20200810"
    cv_end_date = "20201023"
    cv_next_date = "20201026"
    csv_param_date = "20201026"
    portfolio = "EasyTrack"
    signal_csv_dir = "Separate1019ModelSignals"
    executor_str = "SignalExecutorEasy"
    initialAmount = 5 * 100000000
    overwrite_params = {'maxTurnoverPerOrder': 1800000, 'maxExposure': 8000000}
    is_use_csv = True
    get_trigger2production(cv_start_date, cv_end_date, cv_next_date, csv_param_date, portfolio, signal_csv_dir, executor_str,
                           initialAmount, overwrite_params, is_use_csv)