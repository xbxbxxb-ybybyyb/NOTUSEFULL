import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
import time
import BT_NEW.BT_SMALL.CONFIG_SMALL as bt_config_small
from BT_NEW.BT_SMALL.infer_signal_small import infer_signal
from Logger.Logger import Logger
from xquant.compute.aimr import AIMR


config = bt_config_small.BacktestConfig()

# 计算所有有小模型的股票的信号
model_vers = os.listdir(config.model_path)
model_list = []
for model_v in model_vers:
    code_the_model = os.listdir(config.model_path + str(model_v) + "/ModelSaved")
    model_list.extend(code_the_model)

config.codes = model_list
config.codes.sort()

passed_str = AIMR.getParam()
start_idx, end_idx, pid = passed_str.split('-')
start_idx = int(start_idx)
end_idx = int(end_idx)

log_file_path = "/data/user/666888/Logging/inferSignal/{}_pid_{}/".format(str(config.EndDateTime), pid)
if not os.path.exists(log_file_path):
    os.makedirs(log_file_path)

file_name = str(pid) + "_" + "debug.txt"
log_debug_file = log_file_path + file_name
log_fd = Logger(log_debug_file, level='debug')
log_fd.logger.debug("Start to infer signal...")
log_fd.logger.debug("All models {} are in the path {}.".format(model_vers, config.model_path))

tagNames = config.tag_name
factorName = config.factor_name
test_start_date = config.StartDateTime
test_end_date = config.EndDateTime
pickle_factor_address = config.factor_pickle_output_dir
codes = config.codes
codes.sort()

log_fd.logger.debug("All codes are {}".format(codes))
log_fd.logger.debug("Total code number is {}, start index {}, end index {} ".format(len(codes), start_idx, end_idx))

current_stock = 0
model_vers.sort()

for model_v in model_vers:
    start = time.time()
    code_the_model = os.listdir(config.model_path + str(model_v) + "/ModelSaved")
    code_list = []
    for stock_name in code_the_model:
        for pickle_name in codes[start_idx:end_idx]:
            if stock_name in pickle_name:
                code_list.append(stock_name)
    current_stock = current_stock + len(code_list)
    print("Pid {} is conducting inference of model {}...\n"
          "total number of stocks in this model: {}; "
          "total number of stocks in this pid: {}; "
          "all models are {}."
          .format(pid, model_v, len(code_list), end_idx - start_idx, model_vers))

    if len(code_list) > 0:
        infer_signal(
            signalPath=config.signal_path,
            absolutePath=config.model_path + str(model_v) + "/",
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
          .format(pid, current_stock, end_idx - start_idx, model_v, end - start))

# print("Start to sleep...")
# time.sleep(1800)
