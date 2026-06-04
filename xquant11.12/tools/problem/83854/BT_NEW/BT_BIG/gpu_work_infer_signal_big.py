import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
import time
import BT_NEW.BT_BIG.CONFIG_BIG as bt_config_big
from BT_NEW.BT_BIG.infer_signal_big import infer_signal
from Logger.Logger import Logger
from xquant.compute.aimr import AIMR


model_ver = "20190101_48"

config = bt_config_big.BacktestConfig()

passed_str = AIMR.getParam()
start_idx, end_idx, pid = passed_str.split('-')
start_idx = int(start_idx)
end_idx = int(end_idx)

log_file_path = "/data/user/666888/Logging/inferSignal_big/{}_pid_{}/".format(str(config.EndDateTime), pid)
if not os.path.exists(log_file_path):
    os.makedirs(log_file_path)

file_name = str(pid) + "_" + "debug.txt"
log_debug_file = log_file_path + file_name
log_fd = Logger(log_debug_file, level='debug')
log_fd.logger.debug("Start to infer signal...")
log_fd.logger.debug("Current model {} is in the path {}.".format(model_ver, config.model_path))

tagNames = config.tag_name
factorName = config.factor_name
test_start_date = config.StartDateTime
test_end_date = config.EndDateTime
pickle_factor_address = config.factor_pickle_output_dir
codes = config.codes
codes.sort()
code_list = codes[start_idx:end_idx]

log_fd.logger.debug("All codes are {}".format(codes))
log_fd.logger.debug("Total code number is {}, start index {}, end index {} ".format(len(codes), start_idx, end_idx))

current_stock = 0

start = time.time()
print("Pid {} is conducting inference of model {}...\n"
      "total number of stocks in this pid: {}."
      .format(pid, model_ver, end_idx - start_idx))

if len(code_list) > 0:
    infer_signal(
        signalPath=config.signal_path,
        absolutePath=config.model_path + str(model_ver) + "/",
        factorAddress=pickle_factor_address,
        tagNames=tagNames,
        factorName=factorName,
        test_start_date=test_start_date,
        test_end_date=test_end_date,
        code=code_list,
        pid=pid
    )
end = time.time()

print("Pid {} has finished {} tasks of totally {}; "
      "the current model is {} which costs {} seconds"
      .format(pid, end_idx - start_idx, end_idx - start_idx, model_ver, end - start))

# print("Start to sleep...")
# time.sleep(1800)
