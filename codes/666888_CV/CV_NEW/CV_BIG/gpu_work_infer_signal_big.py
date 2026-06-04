import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
import time
import CV_NEW.CV_BIG.CONFIG_BIG as cv_config_big
from CV_NEW.CV_BIG.infer_signal_big import infer_signal
from Logger.Logger import Logger
from xquant.compute.aimr import AIMR

model_ver = "20190101_48"

config = cv_config_big.CVConfig()

passed_str = AIMR.getParam()
start_idx, end_idx, pid = passed_str.split('-')
start_idx = int(start_idx)
end_idx = int(end_idx)

log_file_path = "/data/user/666888/Logging1/inferSignal_big_cv/{}_pid_{}/".format(config.test_end_date_str, pid)
if not os.path.exists(log_file_path):
    os.makedirs(log_file_path)

file_name = str(pid) + "_" + "debug.txt"
log_debug_file = log_file_path + file_name
log_fd = Logger(log_debug_file, level='debug')
log_fd.logger.debug("Start to infer signal...")
log_fd.logger.debug("Current model {} is in the path {}.".format(model_ver, config.absolutePath))

tagNames = config.tagNames
factorNames = config.factorNames
test_start_date = config.test_start_date_str
test_end_date = config.test_end_date_str
pickle_factor_address = config.factorAddress
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
        signalPath=config.signalPath,
        absolutePath=config.absolutePath + str(model_ver) + "/",
        factorAddress=pickle_factor_address,
        tagNames=tagNames,
        factorName=factorNames,
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
