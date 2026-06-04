import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
import json
from INFER_SIGNAL_SMALL.SignalConfig import InferSignalConfig
from xquant.compute.aimr import AIMR


def generate_signals_small(gpu_num=2):

    config = InferSignalConfig()
    #
    model_vers = os.listdir(config.model_path)
    model_vers.sort()

    code_list = config.code_list
    model_list = []
    for code in code_list:
        if code in model_vers:
            model_list.append(code)

    model_list.sort()

    number_stock = len(model_list)

    print("Generating Signal of {} Stocks".format(number_stock))

    gpu_num = min(gpu_num, number_stock)
    stocks_per_thread, residuals = divmod(number_stock, gpu_num)
    stocks_per_thread_list = [stocks_per_thread] * (gpu_num - residuals) + [stocks_per_thread + 1] * residuals
    start_index_list = [sum(stocks_per_thread_list[:i]) for i in range(len(stocks_per_thread_list))]
    end_index_list = start_index_list[1:] + [number_stock]
    parallel_list = [str(start_index_list[i]) + "-" + str(end_index_list[i]) + "-" + str(i)
                     for i in range(len(start_index_list))]

    params = {
        "parallel_list": parallel_list,
        # "docker_version": "cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:prd_gpu_v3.0",
        "tag": "xquant",
        "cpu": 20,
        "gpu": 0,
        "memory": 1024*60
    }
    print(params)

    AIMR.runTasks("INFER_SIGNAL_SMALL/GPUInferSignal.py", json.dumps(params))

    # params = {
    #     "parallel_list": parallel_list,
    #     "docker_version": "cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:research_prd_gpu_v3.0",
    #     "tag": "xquant",
    #     "cpu": 2,
    #     "gpu": 1,
    #     "memory": 1024*32
    # }

    # gpu：cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:research_prd_gpu_v3.0
    # cpu：cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:research_prd_v3.0


if __name__ == '__main__':
    gpu_num = 6
    generate_signals_small(gpu_num=gpu_num)
