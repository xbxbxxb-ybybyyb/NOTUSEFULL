import os
import ray
import pandas as pd
from parallel_train.api import SplitTaskParam, RayParams
from parallel_train.entry import train


# XGBoostActor.train入参
model_params = {"num_boost_round": 100, "params": {'tree_method': 'approx', 'objective': 'binary:logistic',
                                                        'eval_metric': ['logloss', 'error']}}
# XGBoostActor.prepare_data入参,SplitTaskParam表示将任务切分成4块
data_params = {"train": SplitTaskParam([[pd.read_pickle("../data/features.pkl"), pd.read_pickle("../data/label.pkl")],
                                        [pd.read_pickle("../data/features.pkl"), pd.read_pickle("../data/label.pkl")],
                                        [pd.read_pickle("../data/features.pkl"), pd.read_pickle("../data/label.pkl")],
                                        [pd.read_pickle("../data/features.pkl"), pd.read_pickle("../data/label.pkl")],
                                        [pd.read_pickle("../data/features.pkl"), pd.read_pickle("../data/label.pkl")],
                                        [pd.read_pickle("../data/features.pkl"), pd.read_pickle("../data/label.pkl")],
                                        [pd.read_pickle("../data/features.pkl"), pd.read_pickle("../data/label.pkl")],
                                        ]),
            "eval": ["../data/features.pkl", "../data/label.pkl"]}

#如果是普通任务，需指定计算单元配置，如果是分布式任务则无需指定。
ray_params = RayParams(cpus_per_actor=1, gpus_per_actor=0, mems_per_actor=1024, num_actors=4)
train_additional_results = train(backend_actor="XGBoostActor", data_params=data_params, model_params=model_params, ray_params = ray_params)
print("train_additional_results:", train_additional_results)
