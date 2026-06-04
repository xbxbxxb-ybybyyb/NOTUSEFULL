import sys
import os

sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
import time
import BT_NEW.BT_SMALL.CONFIG_SMALL as bt_config_small
from BT_NEW.INFER_SIGNAL_SMALL.infer_signal_small import infer_signal
from Logger.Logger import Logger
from xquant.compute.aimr import AIMR

passed_str = AIMR.getParam()
start_index, end_index, pid = passed_str.split('-')
start_index = int(start_index)
end_index = int(end_index)

config = bt_config_small.BacktestConfig()

# 计算所有有小模型的股票的信号
model_vers = os.listdir(config.model_path)
model_vers.sort()

# model_list = []
# for model_v in model_vers:
    # code_the_model = os.listdir(config.model_path + str(model_v) + "/ModelSaved")
    # model_list.extend(code_the_model)
model_list = config.codes
model_list.sort()


log_file_path = "/data/user/666888/Logging/inferSignal/{}_pid_{}/".format(
    config.test_start_date + "-" + config.test_end_date,
    pid
)
if not os.path.exists(log_file_path):
    os.makedirs(log_file_path)

file_name = str(pid) + "_" + "debug.txt"
log_debug_file = log_file_path + file_name
log_fd = Logger(log_debug_file, level='debug')
log_fd.logger.debug("Start to infer signal...")
log_fd.logger.debug("All models {} are in the path {}.".format(model_vers, config.model_path))

signalPath = config.signal_path
modelPath = config.model_path
libraryName = config.library_name
factorNames = config.factor_names
tagNames = config.tag_names
tagDict = config.tag_dict
test_start_date = config.test_start_date
test_end_date = config.test_end_date

current_stock = 0

for model_v in model_vers:
    start = time.time()
    code_the_model = os.listdir(config.model_path + str(model_v) + "/ModelSaved")
    code_list = []
    for stock_name in code_the_model:
        for pickle_name in model_list[start_index:end_index]:
            if stock_name in pickle_name:
                code_list.append(stock_name)
    current_stock = current_stock + len(code_list)
    print("Pid {} is conducting inference of model {}...\n"
          "total number of stocks in this model: {}; "
          "total number of stocks in this pid: {}"
          .format(pid, model_v, len(code_list), end_index - start_index))

    if len(code_list) > 0:
        infer_signal(
            signalPath=signalPath,
            absolutePath=modelPath + str(model_v) + "/",
            libraryName=libraryName,
            factorNames=factorNames,
            tagNames=tagNames,
            tagDict=tagDict,
            test_start_date=test_start_date,
            test_end_date=test_end_date,
            code=code_list,
            pid=pid
        )
    end = time.time()
    print("Pid {} has finished {} tasks of totally {} in this model and totally {} in this pid; "
          "the current model is {} which costs {} seconds"
          .format(pid, current_stock, len(code_list), end_index - start_index, model_v, end - start))
