import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
import json
from xquant.compute.aimr import AIMR


def generate_signals_big():
    gpu_num = 4

    import CV_NEW.CV_BIG.CONFIG_BIG as cv_config_big
    config = cv_config_big.CVConfig()

    number_stock = len(config.codes)

    stocks_per_thread = number_stock // (gpu_num - 1)
    index_stock = 0
    pid = 0
    parallel_list = []
    while index_stock + stocks_per_thread < number_stock:
        parallel_list.append(str(index_stock) + "-" + str(index_stock + stocks_per_thread) + "-" + str(pid))
        pid = pid + 1
        index_stock = index_stock + stocks_per_thread
    parallel_list.append(str(index_stock) + "-" + str(number_stock) + "-" + str(pid))

    params = {
        "parallel_list": parallel_list,
        "docker_version": "cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:prd_v3.0",
        "tag": "xquant",
        "cpu": 4,
        "gpu": 1,
        "memory": 16000
    }
    print(params)

    AIMR.runTasks("CV_NEW/CV_BIG/gpu_work_infer_signal_big.py", json.dumps(params))


if __name__ == '__main__':
    generate_signals_big()
