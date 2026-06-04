import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
import json
from xquant.compute.aimr import AIMR


def generate_signals_big():
    gpu_num = 10

    import BT_NEW.BT_BIG.CONFIG_BIG as bt_config_big
    config = bt_config_big.BacktestConfig()
    number_stock = len(config.codes)

    print("Generating signal of {} stocks".format(number_stock))

    gpu_num = min(gpu_num, number_stock)
    stocks_per_thread, residuals = divmod(number_stock, gpu_num)
    stocks_per_thread_list = [stocks_per_thread] * (gpu_num - residuals) + [stocks_per_thread + 1] * residuals
    start_index_list = [sum(stocks_per_thread_list[:i]) for i in range(len(stocks_per_thread_list))]
    end_index_list = start_index_list[1:] + [number_stock]
    parallel_list = [str(start_index_list[i]) + "-" + str(end_index_list[i]) + "-" + str(i)
                     for i in range(len(start_index_list))]

    params = {
        "parallel_list": parallel_list,
        "docker_version": "cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:prd_gpu_v3.0",
        "tag": "xquant",
        "cpu": 1,
        "gpu": 1,
        "memory": 16000
    }
    print(params)

    AIMR.runTasks("BT_NEW/BT_BIG/gpu_work_infer_signal_big.py", json.dumps(params))


if __name__ == '__main__':
    generate_signals_big()
