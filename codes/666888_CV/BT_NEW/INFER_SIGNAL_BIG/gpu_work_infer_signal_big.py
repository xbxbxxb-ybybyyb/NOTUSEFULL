import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
import time
import BT_NEW.BT_BIG.CONFIG_BIG as bt_config_big
from multiprocessing import Pool
from BT_NEW.INFER_SIGNAL_BIG.infer_signal_big import infer_signal
from Logger.Logger import Logger
from xquant.compute.aimr import AIMR

passed_str = AIMR.getParam()
start_index, end_index, pid = passed_str.split('-')
start_index = int(start_index)
end_index = int(end_index)

config = bt_config_big.BacktestConfig()

model_ver = config.model_ver

log_file_path = "/data/user/666888/Logging/inferSignal_big/{}_pid_{}/".format(
    config.test_start_date + "-" + config.test_end_date,
    pid
)
if not os.path.exists(log_file_path):
    os.makedirs(log_file_path)

file_name = str(pid) + "_" + "debug.txt"
log_debug_file = log_file_path + file_name
log_fd = Logger(log_debug_file, level='debug')
log_fd.logger.debug("Start to infer signal...")
log_fd.logger.debug("Current model {} is in the path {}.".format(model_ver, config.model_path))

signalPath = config.signal_path
modelPath = config.model_path
libraryName = config.library_name
factorNames = config.factor_names
tagNames = config.tag_names
tagDict = config.tag_dict
test_start_date = config.test_start_date
test_end_date = config.test_end_date

codes = config.codes
codes.sort()
code_list = codes[start_index:end_index]

start = time.time()
print("Pid {} is conducting inference of model {}; total number of stocks in this pid: {}."
      .format(pid, model_ver, end_index - start_index))

if len(code_list) > 0:
    infer_signal(
        signalPath=signalPath,
        absolutePath=modelPath + str(model_ver) + "/",
        libraryName=libraryName,
        factorNames=factorNames,
        tagNames=tagNames,
        tagDict=tagDict,
        test_start_date=test_start_date,
        test_end_date=test_end_date,
        code=code_list,
        pid=pid,
        model_ver=model_ver
    )
end = time.time()

print("Pid {} has finished {} tasks; time cost: {} seconds".format(pid, end_index - start_index, end - start))
