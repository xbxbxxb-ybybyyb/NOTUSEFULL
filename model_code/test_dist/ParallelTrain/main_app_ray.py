import os
os.environ["use_cmo"]='True'
import ray
import pandas as pd
from parallel_train.entry import train
from parallel_train.api import SplitTaskParam, RayParams
from DataAPI.DataToolkit import *
from xquant.model.tracking import auto_log


def get_train_test_map(start_date, end_date, update_model_period):
    trading_day = get_trading_day(start_date, end_date)
    trading_day_fri = get_friday_trading_days(start_date, end_date)
    trading_day = get_trading_day(trading_day_fri[0], trading_day[-1])
    i_1 = 0
    train_test_map = {}
    temp_train_date = trading_day[0]
    for i in range(trading_day.__len__()-1):
        if i == 0 or (trading_day[i] in trading_day_fri and i - i_1 >= update_model_period):
            i_1 = i
            temp_train_date = trading_day[i]
        train_test_map.update({trading_day[i+1]: temp_train_date})
    return train_test_map


test_start_date = 20200111
test_end_date = 20200217
save_root_path = "/tmp/user/012620/own/Apollo/StrategySelectStockDay"
update_model_period = 5
strategy_types = ['vwap']
fs = pd.read_pickle("factor_list.pkl")
factor_dict = {}
for time_ in strategy_types:
    # test_factor = list(pd.read_excel(factor_dir + factor_file_name, sheet_name=time_, header=None).values.flatten())
    factor_dict[time_] = fs

train_test_map = get_train_test_map(test_start_date, test_end_date, update_model_period)
train_date_list = sorted(list(set([v for k, v in (train_test_map.items())])))

data_params = {"train_date": SplitTaskParam(train_date_list*6),
               "strategy_type_factor": SplitTaskParam([(strategy_type, factor_list) for strategy_type, factor_list in factor_dict.items()]),
               "train_test_map":train_test_map,
               "label_name": 'vwap_re',
               'gap': 5,
               'train_window': 240,
               "save_root_path": save_root_path
               }
model_params = {"params": {'n_estimators': 1000, 'seed': 1993, 'nthread': 100, 'gamma': 5.0, 'min_child_weight': 0.5,
                           'reg_alpha': 50, 'reg_lambda': 10, 'max_depth': 8, 'learning_rate': 0.05, 'subsample': 0.9,
                           'colsample_bytree': 0.9, 'tree_method': 'gpu_hist'},
                "maximize": False,
                "eval_metric": ["mae"]
                }
"""
#一、如何启动分布式Ray集群：
在AI工程化界面上，选择分布式执行任务，并设置分布式Ray集群启动配置，提交任务即可启动一个分布式的Ray集群。配置参数说明如下：
    1、主程序资源：资源用于Driver端主程序的计算结果汇总，不参与Ray分布式计算；
    2、共享内存：共享内存大小，若需调用ray.put放置大对象，建议调大共享内存；
    3、计算单元资源：设置单个任务的资源大小，并以此配置启动Ray计算单元，每个任务会在某个Ray计算单元中运行；
    4、并发度：同时运行的计算单元个数；任务数可超过并发度，任务自动排队。

#二、通过parallel_train执行并行任务：
    1、第一步自动检测Ray资源，并准备按Ray资源大小的运行任务：
        若是AI工程化分布式执行任务，由于本节点已经加入分布式Ray集群，主程序driver端直接连接；
        若是普通任务，且未检测到Ray资源，主程序driver端根据本机资源自动创建Ray资源并连接。
        若是普通任务，且检测到Ray资源，主程序driver端直接连接，此时请确保Ray资源只有当前主程序在占用，否则会产生任务冲突。
        若是普通任务，且主程序driver端调用了ray.init, 主程序将连接此组新的Ray资源（本地支持多组Ray资源）。
        此外，支持主程序调用ray.init(local_mode = True)指定非并行运行模式，此模式支持调试。

    2、第二步，调用并行训练入口函数parallel.train，并设置参数。
        parallel.train并行训练函数：
            并行框架先检测SplitTaskParam类型的参数并切分任务（切分方式见下方说明），随后在每个任务中，先调用RemoteActor中的prepare_data函数准备数据，然后调用RemoteActor中的train方法训练模型。
        参数：
            backend_actor： 指定定并行运行的RemoteActor类型，如XGBWrapActor，可自定义实现各类算法的RemoteActor。
            data_params: Dict[Any, Any]: 数据加载、存储的参数，RemoteActor的prepare_data成员函数的唯一入参，可指定SplitTaskParam类型的参数用于切分任务；
            model_params: Dict[Any, Any]: 模型算法的训练参数，RemoteActor的train成员函数的唯一入参；
            ray_params: RayParams, Ray的并行运行参数，如cpus_per_actor（单任务核数）， gpus_per_actor(支持小于1的分数，实现单卡共享)， num_actors（并行度）等，对应分布式执行的计算单元资源和并发度; 后续支持容错、回调、超参数寻优等其他配置。

        并行任务切分说明：

            data_params通过指定parallel_train.api.SplitTaskParam类型的参数，来切分任务，并行运行。非SplitTaskParam类型的参数由各个任务共享。
            比如：
            data_params = {"p1": SplitTaskParam([1,2,3], "p2":SplitTaskParam["a", "b"]), "p3": "share"}
            则根据p1和p2参数的笛卡尔积，p3参数由各个任务共享。一共生成6组参数，每个子任务接收到其中的一组参数：
                {"p1": 1, "p2": "a", "p3": "share"}
                {"p1": 1, "p2": "b", "p3": "share"}
                {"p1": 2, "p2": "a", "p3": "share"}
                {"p1": 2, "p2": "b", "p3": "share"}
                {"p1": 3, "p2": "a", "p3": "share"}
                {"p1": 3, "p2": "b", "p3": "share"}
"""
#普通任务，才需要通过RayParams指定计算单元的资源配置，分布式任务无需指定
ray_params = RayParams(cpus_per_actor=2, gpus_per_actor=1, mems_per_actor=1024, num_actors=2)
train_additional_results = train(backend_actor="XGBWrapActor", data_params=data_params, model_params=model_params, ray_params=ray_params)
print(train_additional_results)

# train_additional_results = train(backend_actor="XGBWrapActor", data_params=data_params, model_params=model_params)
# print("train_additional_results:", train_additional_results)
