import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
import time
from CONFIG import USER_ID
from INFER_SIGNAL_CHECK.SignalConfig import InferSignalConfig
from INFER_SIGNAL_CHECK.InferSignal import infer_signal
from xquant.xqutils.helper import multicore_init
from Logger.Logger import Logger
from xquant.compute.aimr import AIMR


passed_str = AIMR.getParam()
start_index, end_index, pid = passed_str.split('-')
start_index = int(start_index)
end_index = int(end_index)

config = InferSignalConfig()

# 计算所有有小模型的股票的信号
# model_vers = os.listdir(config.model_path)
# model_vers.sort()

code_list = config.code_list
model_list = sorted(code_list)

log_file_path = "/data/user/{}/Logging/inferSignal/{}_pid_{}/".format(USER_ID,
    config.test_start_date + "-" + config.test_end_date,
    pid
)
if not os.path.exists(log_file_path):
    os.makedirs(log_file_path)

file_name = str(pid) + "_" + "debug.txt"
log_debug_file = log_file_path + file_name
log_fd = Logger(log_debug_file, level='debug')
log_fd.logger.debug("Start to Infer Signal ...")
log_fd.logger.debug("All Models Num: {} Are in the Path: {}".format(len(model_list), config.model_path))

signalPath = config.signal_path
logPath = config.log_path
modelPath = config.model_path
libraryName = config.library_name
signalLibrary = config.signal_library
factorNames = config.factor_names
factorIndex = config.factorIndex
tagNames = config.tag_names
tagDict = config.tag_dict
is_multiprocess = config.is_multiprocess

current_stock = 0
target_code_list = []
for code in code_list:
    if code in model_list[start_index:end_index]:
        target_code_list.append(code)

current_stock = current_stock + len(target_code_list)
print("Pid {} is Conducting Inference of Model...\n"
      "Total Number of Stocks in this Model: {}; "
      "Total Number of Stocks in this Pid: {}"
        .format(pid, len(target_code_list), end_index - start_index))

start = time.time()
if len(target_code_list) > 0:
    if not is_multiprocess:
        infer_signal(
            signalPath=signalPath,
            logPath=logPath,
            absolutePath=modelPath,
            libraryName=libraryName,
            signalLibrary=signalLibrary,
            factorNames=factorNames,
            factorIndex=factorIndex,
            tagNames=tagNames,
            tagDict=tagDict,
            codeList=target_code_list,
            pid=pid
        )

    else:

        import multiprocessing as mp
        process_num = min(len(target_code_list), 20)
        assert multicore_init() == True
        pool = mp.Pool(processes=process_num)

        for code in target_code_list:
            pool.apply_async(infer_signal, (signalPath, logPath, modelPath, libraryName, signalLibrary, factorNames, factorIndex, tagNames, tagDict,
                                            [code], pid, ))
        pool.close()
        pool.join()

end = time.time()
print("Pid {} Has Finished {} Tasks of Totally {} in this Model and Totally {} in this Pid; "
       "Time Cost: {} Seconds".format(pid, current_stock, len(code_list), end_index - start_index, end - start))
