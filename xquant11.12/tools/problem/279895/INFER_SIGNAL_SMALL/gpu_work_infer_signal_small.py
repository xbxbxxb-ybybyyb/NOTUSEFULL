import sys
import os

sys.path.append( "/".join(os.path.abspath(__file__).split("/")[:-2])   )
import time
import INFER_SIGNAL_SMALL.CONFIG_SMALL as CONFIG_SMALL
from INFER_SIGNAL_SMALL.infer_signal_small import infer_signal
from Logger.Logger import Logger

start_index, end_index, pid =0,0,111111
start_index = int(start_index)
end_index = int(end_index)

config = CONFIG_SMALL.InferSignalConfig()


log_file_path = "{}_pid_{}/".format(
    config.test_start_date + "-" + config.test_end_date,
    pid
)
if not os.path.exists(log_file_path):
    os.makedirs(log_file_path)

file_name = str(pid) + "_" + "debug.txt"
log_debug_file = log_file_path + file_name
log_fd = Logger(log_debug_file, level='debug')
log_fd.logger.debug("Start to infer signal...")

signalPath = config.signal_path
modelPath = config.model_path
libraryName = config.library_name
factorNames = config.factor_names
tagNames = config.tag_names
tagDict = config.tag_dict
test_start_date = config.test_start_date
test_end_date = config.test_end_date

current_stock = 0

start = time.time()
code_the_model = os.listdir(config.model_path)
code_list = ["000553.SZ"]

current_stock = current_stock + len(code_list)
print("Pid {} is conducting inference of model...\n"
      "total number of stocks in this model: {}; "
      "total number of stocks in this pid: {}"
      .format(pid, len(code_list), end_index - start_index))

if len(code_list) > 0:
    infer_signal(
        signalPath=signalPath,
        absolutePath=modelPath,
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
      " which costs {} seconds"
      .format(pid, current_stock, len(code_list), end_index - start_index, end - start))

