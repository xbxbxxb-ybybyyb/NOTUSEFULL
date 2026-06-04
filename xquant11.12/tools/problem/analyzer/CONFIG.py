#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/3/5 14:32
import os

### 用户
USER_ID = "015629"

DATA_USER_ID = "666888"

ORDER_CAPACITY_PATH = "/data/user/{}/OrderCapacity2/".format(DATA_USER_ID)
TRADE_DATA_PATH = "/data/user/{}/TradeData2/".format(DATA_USER_ID)

TRADE_ORDER_CAPACITY_PATH = "/data/user/{}/BT_Trade_OrderCapacity/".format(USER_ID)
TRIGGER_PARAMETER_PATH = "/data/user/{}/Trigger_Parameter/".format(USER_ID)
TRIGGER_CSV_PATH = "/data/user/{}/MISC/params_tuning_results_20190801_20190905.csv".format(USER_ID)

FTP_UPLOAD_BT = "/data/user/{}/ftp_uploads_bt/".format(USER_ID)
FTP_UPLOAD_CV = "/data/user/{}/ftp_uploads_cv/".format(USER_ID)
FTP_PORTFOLIO_PATH = "{}/".format(DATA_USER_ID)

MODEL_NAME = "20191101_48_end"
MODEL_PATH = "ModelProduction/"+ MODEL_NAME + "/"
TRADE_ORDER_CAPACITY_HDFS_PATH = 'ModelProduction/' + MODEL_NAME + '/bt_info/'
TRIGGER_PARAMETER_HDFS_PATH = 'ModelProduction/' + MODEL_NAME + '/tg_para/'
HDFS_BT_ROOT = "bt"
HDFS_CV_ROOT = "cv"

LOG_PATH = "/data/user/{}/Logging/bt/".format(USER_ID)

BT_RESULT_SOURCE_PATH = "/data/user/{}/BT_Results/sources/".format(USER_ID)
BT_RESULT_RESULT_PATH = "/data/user/{}/BT_Results/results/".format(USER_ID)
BT_RESULT_ZIP_PATH = '/data/user/{}/BT_Results/zipped/'.format(USER_ID)

TICK_SUFFIX = "T"


def get_hdfs_root_path(mode, path):
    if mode == "Local":
        return os.path.join("", path)
    elif mode == "Spark":
        return os.path.join(USER_ID, path)
    else:
        raise Exception("ONLY SUPPORT LOCAL OR SPARK MODE")


