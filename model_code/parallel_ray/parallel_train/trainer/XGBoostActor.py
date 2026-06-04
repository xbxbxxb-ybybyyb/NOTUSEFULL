from typing import Tuple, Dict, Any, List, Optional, Callable, Union, Sequence
import pickle
import warnings
import pandas as pd
import xgboost as xgb
from xgboost.core import XGBoostError
import inspect
from ray import logger
from parallel_train.helper import RayActorTrainingError, RayXGBoostTrainingStopped
from parallel_train.supervisor import Queue
from parallel_train.trainer.BaseActor import BaseActor



class XGBoostActor(BaseActor):
    """Remote paralleltrain XGBoost actor class.

    The actor with rank 0 also checkpoints the model periodically and
    sends the checkpoint back to the driver.

    Args:
        rank (int): Rank of the actor. Must be ``0 <= rank < num_actors``.
        num_actors (int): Total number of actors.
        queue (Queue): Ray queue to communicate with main process.
        checkpoint_frequency (int): How often to store checkpoints. Defaults
            to ``5``, saving checkpoints every 5 boosting rounds.

    """
    def __init__(self):
        """
        成员变量：
        rank_id: int, Actor的唯一标识, 从0开始计数（rank_id可作为data_params或者model_params的key，让各个Actor各自识别自己的参数）;
        data_params: Dict[Any, Any]: 指数据加载、存储的参数，RemoteActor的prepare_data成员函数的唯一入参，可指定SplitTaskParam类型的参数用于切分任务；
        model_params: Dict[Any, Any]: 指模型算法的训练参数，RemoteActor的train成员函数的唯一入参；
        ray_params: RayParams, 指并行任务运行的配置参数，可获取RemoteActor的运行参数，如cpus_per_actor， gpus_per_actor， num_actors等，对应提交任务时的最小资源组和资源组个数; 后续支持容错、回调、超参数寻优等其他配置。
        成员方法：
        reset_rank_id(rank_id: int)：重置rank_id的方法，rank_id由框架自动分配，一般不需要手动指定，一些调试场景时可以指定rank_id来分配特定的任务。
        put_queue(item: Dict[str, [_Checkpoint, Any]): 用于传递结果到drive端。driver端定时（默认30s）获取queue中的结果，并填入train函数的返回值additional_results。key为additional_results中的key名。
        """
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
        :param data_params: 数据参数，可结合rank_id识别各个actor的数据；
        :return: None，数据请赋值给成员变量后使用。
        """
        data, label = data_params["train"][0], data_params["train"][1]
        self.dtrain = xgb.DMatrix(**{"data": data, "label": label})
        self.evals = [(xgb.DMatrix(**{"data": pd.read_pickle(data_params["eval"][0]), "label": pd.read_pickle(data_params["eval"][1])}), "eval_data")]

        if False:
            self.dtest = xgb.DMatrix(**{"data": data_params["test"][0], "label": data_params["test"][0]})




    def train(self, model_params: Dict) -> None:
        """
        （待实现的成员方法）模型训练函数，在Actor的准备步骤都完成后，开始执行，由并行训练框架内部调用。
        :param model_params:
        :return: None，训练结果返回值请通过put_queue函数传递到driver端的parallel_train.train的additional_results返回值。
        """
        #训练的并行度不超过Ray分配的CPU数
        self.check_model_params(model_params)

        if "xgb_model" in model_params:
            if isinstance(model_params["xgb_model"], bytes):
                # bytearray type gets lost in remote actor call
                model_params["xgb_model"] = bytearray(model_params["xgb_model"])

        evals_result = dict()
        result_dict = {}

        try:
            num_boost_round = model_params.pop("num_boost_round")
            params = model_params.pop("params")
            bst = xgb.train(
                params,
                self.dtrain,
                num_boost_round,
                evals=self.evals,
                evals_result=evals_result,
                **model_params)

            with open("xgb_model{}.pkl".format(self.rank_id), "wb") as f:
                pickle.dump(bst, f)
        except XGBoostError as e:
            raise RayActorTrainingError("XGBoostError: Training failed.") from e
        self.put_queue({"model_path": "xgb_model{}.pkl".format(self.rank_id)})


    # def predict(self, model_params: Dict[str, Any]) -> None:
    #     model = pd.read_pickle(model_params["model_path"])
    #     predictions = model.predict(self.dtest)
    #     self.put_queue({"predictions": predictions})

