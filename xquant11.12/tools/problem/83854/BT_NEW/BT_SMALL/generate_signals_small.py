import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
import json
import BT_NEW.BT_SMALL.CONFIG_SMALL as bt_config_small
from xquant.compute.aimr import AIMR


def generate_signals_small():
    gpu_num = 4

    import BT_NEW.BT_SMALL.CONFIG_SMALL as bt_config_small
    config = bt_config_small.BacktestConfig()

    model_vers = os.listdir(config.model_path)
    model_list = []
    for model_v in model_vers:
        code_the_model = os.listdir(
            config.model_path + str(model_v) + "/ModelSaved"
        )
        model_list.extend(code_the_model)
    number_stock = len(model_list)
    print("Generating signal of {} stocks".format(number_stock))

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
        "docker_version": "cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:prd_gpu_v3.0",
        "tag": "xquant",
        "cpu": 4,
        "gpu": 1,
        "memory": 16000
    }
    print(params)

    AIMR.runTasks("BT_NEW/BT_SMALL/gpu_work_infer_signal_small.py", json.dumps(params))


if __name__ == '__main__':
    generate_signals_small()
