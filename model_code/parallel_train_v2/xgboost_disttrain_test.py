from typing import Dict
import warnings
import pandas as pd
import xgboost as xgb
import inspect
import torch
import os

from parallel_train.backend import XGBoostBackend, get_rabit_centext
from parallel_train.trainer import ParallelTrainer, SplitTaskParam, RayParams
from parallel_train import world_size, world_rank, local_rank, report



class XGBoostDistBackendExample(XGBoostBackend):
    def __init__(self):
        pass

    def check_model_params(self, model_params):
        func_name = "xgb.train()"
        valid_keys = inspect.getfullargspec(xgb.train)[0]
        invalid_kwargs = [k for k in model_params if k not in valid_keys]
        if invalid_kwargs:
            raise TypeError(
                f"Got invalid keyword arguments to be passed to `{func_name}`. "
                f"Invalid keys: {invalid_kwargs}")


        params = model_params["params"]
        tree_method = params.get("tree_method", "auto") or "auto"
        if self.ray_params.gpus_per_actor > 0 and not tree_method.startswith("gpu_"):
            warnings.warn(
                f"GPUs have been assigned to the actors, but the current XGBoost "
                f"tree method is set to `{tree_method}`. Thus, GPUs will "
                f"currently not be used. To enable GPUs usage, please set the "
                f"`tree_method` to a GPU-compatible option, "
                f"e.g. `gpu_hist`.")

        cpus_per_actor = self.ray_params.cpus_per_actor
        if "nthread" in model_params or "n_jobs" in model_params:
            if ("nthread" in params and params["nthread"] > cpus_per_actor) or (
                    "n_jobs" in params and params["n_jobs"] > cpus_per_actor):
                raise ValueError(
                    f"Specified number of threads {params['nthread']} greater than number of CPUs {cpus_per_actor}.")
        else:
            params["nthread"] = int(self.ray_params.cpus_per_actor)
            params["n_jobs"] = int(self.ray_params.cpus_per_actor)



    def prepare_data(self, data_params:Dict) -> None:
        """
        （待实现的成员方法）用于train或者predict执行前的准备工作(如加载数据，加载模型等)，由并行训练框架内部调用。
        :param data_params: 数据加载、存储的参数，可指定SplitTaskParam类型的参数用于切分任务。
        :return: None，数据请赋值给成员变量后使用。
        """
        self.world_rank = world_rank()

        data = torch.randn(data_params['num_samples'], data_params['input_size']).numpy()
        label = torch.randint(2, (data_params['num_samples'], data_params['output_size'])).numpy()
        self.dtrain = xgb.DMatrix(**{"data": data, "label": label})
        self.evals = [(xgb.DMatrix(**{"data": data, "label": label}), "eval_data")]


    def train(self, model_params: Dict) -> None:
        """
        （待实现的成员方法）模型训练函数，在Actor的准备步骤都完成后，开始执行，由并行训练框架内部调用。
        :param model_params: 模型算法的训练参数，train成员函数的唯一入参；
        :return: None， 可调用parallel_train.report方法将训练过程中数据回传给主程序，可在主程序中汇总各个worker的结果
        """
        evals_result = {}
        result_dict = {}

        num_boost_round = model_params.pop("num_boost_round")
        params = model_params.pop("params")

        # 分布式改造1：必须将模型放入rabit_context会话中训练，以保证各个worker协同训练
        with get_rabit_centext():
            print(f"world_rank {self.world_rank} start training...")
            bst = xgb.train(
                params,
                self.dtrain,
                num_boost_round,
                evals=self.evals,
                evals_result = evals_result,
                **model_params
            )

            result_dict.update({
                "bst": bst,
                "evals_result": evals_result,
            })

        # # 分布式改造2（可选）：将训练过程中数据回传给主程序，可在主程序中汇总各个worker的结果
        # report(evals_result=evals_result, world_rank=self.world_rank)
        # print(f"world_rank {self.world_rank} finish training!")


def main():
    # step2: 实例化Trainer，设置Trainer入参，已继承并实现的Backend类，任务类型（DistTrain or LocalTrain），以及ray_params参数类型
    trainer = ParallelTrainer(backend=XGBoostDistBackendExample,
                              task_mode='DistTrain',
                              ray_params=RayParams(cpus_per_worker=1, gpus_per_worker=1))

    # step3: trainer开始处理，可以添加initial_hook函数
    trainer.start()

    # step4: 设置data_params进行数据参数切分，如下被切分为两组参数，share_factor为共享参数
        # {'share_factor': 'factor_share', 'train_date': '20220418', 'strategy_type_factor': 'factor1'}
    # {'share_factor': 'factor_share', 'train_date': '20220419', 'strategy_type_factor': 'factor1'}
    data_params = {"train_date": SplitTaskParam(["20220418"]),
                   "strategy_type_factor": SplitTaskParam(["factor1"]),
                   "num_samples": 20, "input_size": 10, "output_size":1,
                   "share_factor": "factor_share"}

    # 模型参数
    model_params = {"num_boost_round": 20, "params": {'tree_method': 'approx', 'objective': 'binary:logistic',
                                                       'eval_metric': ['logloss', 'error']}}
    callback_iterator = trainer.parallel_run(model_params=model_params, data_params=data_params)

    # step5: 异步返回worker的回调信息，若worker中有调用parallel_train.report方法发送信息，可在此主程序中获取到。
    for result in callback_iterator:
        print("获取parallel_train.report方法传递的回调结果：")
        # print(pd.DataFrame(result))
    print(1111)
    # step6: 关闭Trainer
    trainer.shutdown()


if __name__=="__main__":
    import ray
    # ray.init(num_cpus = 8)
    main()
    import time
    time.sleep(10)
