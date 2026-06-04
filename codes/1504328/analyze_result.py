import os
import json
import shutil
import Analyzer.TotalSummary as TotalSummary
import Analyzer.sta_daily as sta_daily
import Analyzer.summary_data as summary_data
import Analyzer.summary_data_longshort as summary_data_longshort
from xquant.xqutils.xqfile import HDFSFile
from CONFIG import USER_ID


def analyze_result(portfolio, today_str, hdfs_root, result_dir_name, bt_dir):
    # CHECK
    if not os.path.exists("/data/user/{}/BT_Results/Stock/sources/".format(USER_ID) + today_str):
        os.makedirs("/data/user/{}/BT_Results/Stock/sources/".format(USER_ID) + today_str)
    elif os.path.exists("/data/user/{}/BT_Results/Stock/sources/".format(USER_ID) + today_str + '/' + result_dir_name):
        shutil.rmtree("/data/user/{}/BT_Results/Stock/sources/".format(USER_ID) + today_str + '/' + result_dir_name)

    if not os.path.exists("/data/user/{}/BT_Results/Stock/results/".format(USER_ID) + today_str):
        os.makedirs("/data/user/{}/BT_Results/Stock/results/".format(USER_ID) + today_str)
    elif os.path.exists("/data/user/{}/BT_Results/Stock/results/".format(USER_ID) + today_str + '/' + result_dir_name):
        shutil.rmtree("/data/user/{}/BT_Results/Stock/results/".format(USER_ID) + today_str + '/' + result_dir_name)

    if result_dir_name.startswith('cv'):
        # excel_name = 'result_merged.xlsx'
        excel_name = 'result_all.xlsx'
    elif result_dir_name.startswith('bt'):
        excel_name = 'result_all.xlsx'
    else:
        raise Exception('Neither cv nor bt does the result_dir_name start with: ' + result_dir_name)

    # TRANSFER
    hf = HDFSFile()
    with hf.open(bt_dir + portfolio + '_quantity.json', 'rb') as f:
        config = f.read()
        config = json.loads(config)
    hdfs_path = os.path.join(hdfs_root, result_dir_name)
    hf.download("/data/user/{}/BT_Results/Stock/sources/".format(USER_ID) + today_str + '/' + result_dir_name, hdfs_path)

    # SUMMARIZE
    TotalSummary.summary(today_str, result_dir_name, portfolio, excel_name, config)
    sta_daily.summary(today_str, result_dir_name)
    summary_data.summary(today_str, result_dir_name)
    summary_data_longshort.summary(today_str, result_dir_name)