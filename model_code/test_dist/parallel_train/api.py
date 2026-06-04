from typing import TYPE_CHECKING, Dict, Any, List, Optional, Union
from collections import Iterable
import ray
from ray import logger
from dataclasses import dataclass, field
import warnings

from parallel_train.helper import auto_connect_ray, get_xqconfig

if TYPE_CHECKING:
    from parallel_train.entry import train



@dataclass
class RayParams:
    """Parameters to configure Ray-specific behavior.

    Args:
        num_actors (int): Number of parallel Ray actors.
        cpus_per_actor (int): Number of CPUs to be used per Ray actor.
        gpus_per_actor (int): Number of GPUs to be used per Ray actor. -1自动根据xgboost参数检验是否使用GPU.
        resources_per_actor (Optional[Dict]): Dict of additional resources
            required per Ray actor.
        elastic_training (bool): If True, training will continue with
            fewer actors if an actor fails. Default False.
        max_failed_actors (int): If `elastic_training` is True, this
            specifies the maximum number of failed actors with which
            we still continue training.
        max_actor_restarts (int): Number of retries when Ray actors fail.
            Defaults to 0 (no retries). Set to -1 for unlimited retries.
        checkpoint_frequency (int): How often to save checkpoints. Defaults
            to ``5`` (every 5th iteration).
    """
    # Actor scheduling
    num_actors: int = -1
    cpus_per_actor: int = -1
    gpus_per_actor: float = -1
    mems_per_actor: int = -1
    resources_per_actor: Optional[Dict] = None

    # Placement Strategy, PACK
    placement_strategy: str = "PACK"

    # Fault tolerance
    elastic_training: bool = False
    max_failed_actors: int = 5
    max_actor_restarts: int = 0
    checkpoint_frequency: int = 5

    # Distributed callbacks
    distributed_callbacks: Optional[List] = None

    def __post_init__(self):
        # 自动连接至Ray集群
        auto_connect_ray()
        taskParam = get_xqconfig()
        if taskParam.get("cpus_per_actor") != -1:
            logger.info("RayParams: 当前任务是分布式任务，将自动获取Ray集群计算单元的资源配置.")
            if self.num_actors == -1 and self.cpus_per_actor == -1 and self.gpus_per_actor == -1 and self.mems_per_actor == -1:
                logger.debug("未指定RayParams运行资源, 将使用分布式任务的运行参数...")
            else:
                warnings.warn(
                    "RayParams: 传入RayParams的以下参数将被分布式任务参数覆盖：num_actors、cpus_per_actor、gpus_per_actor、mems_per_actor！")
            self.cpus_per_actor = taskParam.get("cpus_per_actor")
            self.gpus_per_actor = taskParam.get("gpus_per_actor")
            self.num_actors = taskParam.get("num_actors")
            self.mems_per_actor = taskParam.get("mems_per_actor")

        assert type(self.cpus_per_actor)==int, "RayParams的cpus_per_actor参数类型必须为int！"
        assert type(self.gpus_per_actor)==float or type(self.gpus_per_actor)==int, "RayParams的gpus_per_actor参数类型必须为float！"
        assert type(self.num_actors)==int, "RayParams的num_actors参数类型必须为int！"
        assert type(self.mems_per_actor)==int, "RayParams的mems_per_actor参数类型必须为int！"

        assert self.cpus_per_actor > 0, "每个计算单元的cpu数cpus_per_actor必须大于0，当前值为{}！当前为普通任务，请为RayParams指定cpus_per_actor！".format(
            self.cpus_per_actor)
        assert self.gpus_per_actor >= 0, "每个计算单元的gpu数gpus_per_actor必须大于等于0，当前值为{}！当前为普通任务，请为RayParams指定gpus_per_actor！".format(
            self.gpus_per_actor)
        assert self.num_actors > 0, "计算单元的个数num_actors(即最大并行度)必须大于0，当前值为{}！当前为普通任务，请为RayParams指定num_actors！".format(
            self.num_actors)
        assert self.mems_per_actor > 0, "计算单元的个数num_actors(即最大并行度)必须大于0，当前值为{}！当前为普通任务，请为RayParams指定num_actors！".format(
            self.num_actors)

        logger.info(
            f"单个计算单元资源为: [cpus_per_actor: {self.cpus_per_actor}, gpus_per_actor: {self.gpus_per_actor}, mems_per_actor: {self.mems_per_actor}, 最大并行度为: {self.num_actors}].")
        if self.elastic_training and self.max_failed_actors == 0:
            raise ValueError(
                "Elastic training enabled but the maximum number of failed "
                "actors is set to 0. This means that elastic training is "
                "effectively disabled. Please set `RayParams.max_failed_actors` "
                "to something larger than 0 to enable elastic training.")

        if self.elastic_training and self.max_actor_restarts == 0:
            raise ValueError(
                "Elastic training enabled but the maximum number of actor "
                "restarts is set to 0. This means that elastic training is "
                "effectively disabled. Please set `RayParams.max_actor_restarts` "
                "to something larger than 0 to enable elastic training.")

    # def get_tune_resources(self):
    #     """Return the resources to use for training with Tune."""
    #     if self.cpus_per_actor <= 0 or self.num_actors <= 0:
    #         raise ValueError("num_actors and cpus_per_actor both must be "
    #                          "greater than 0.")
    #     return _get_tune_resources(
    #         num_actors=self.num_actors,
    #         cpus_per_actor=self.cpus_per_actor,
    #         gpus_per_actor=max(0, self.gpus_per_actor),
    #         resources_per_actor=self.resources_per_actor)


class SplitTaskParam:
    def __init__(self, value):
        # 用于切分任务
        if not isinstance(value, Iterable):
            raise Exception("SplitTaskParam的值必须为可迭代的对象！")
        self.value = value


def _validate_ray_params(ray_params: Union[None, RayParams, dict]) \
        -> RayParams:
    if ray_params is None:
        ray_params = RayParams()
    elif isinstance(ray_params, dict):
        ray_params = RayParams(**ray_params)
    elif not isinstance(ray_params, RayParams):
        raise ValueError(
            f"`ray_params` must be a `RayParams` instance, a dict, or None, "
            f"but it was {type(ray_params)}."
            f"\nFIX THIS preferably by passing a `RayParams` instance as "
            f"the `ray_params` parameter.")
    if ray_params.num_actors <= 0:
        raise ValueError(
            "The `num_actors` parameter is set to 0. Please always specify "
            "the number of distributed actors you want to use."
            "\nFIX THIS by passing a `RayParams(num_actors=X)` argument.")
    elif ray_params.num_actors < 2:
        warnings.warn(
            f"`num_actors` in `ray_params` is smaller than 2 "
            f"({ray_params.num_actors}). XGBoost will NOT be distributed!")
    return ray_params


@dataclass
class LocalRayParams:
    """Parameters to configure Ray-specific behavior.

    Args:
        num_actors (int): Number of parallel Ray actors.
        cpus_per_actor (int): Number of CPUs to be used per Ray actor.
        gpus_per_actor (int): Number of GPUs to be used per Ray actor. -1自动根据xgboost参数检验是否使用GPU.
        resources_per_actor (Optional[Dict]): Dict of additional resources
            required per Ray actor.
        elastic_training (bool): If True, training will continue with
            fewer actors if an actor fails. Default False.
        max_failed_actors (int): If `elastic_training` is True, this
            specifies the maximum number of failed actors with which
            we still continue training.
        max_actor_restarts (int): Number of retries when Ray actors fail.
            Defaults to 0 (no retries). Set to -1 for unlimited retries.
        checkpoint_frequency (int): How often to save checkpoints. Defaults
            to ``5`` (every 5th iteration).
    """
    # Actor scheduling
    num_actors: int = -1
    cpus_per_actor: int = -1
    gpus_per_actor: float = -1
    mems_per_actor: int = -1
    resources_per_actor: Optional[Dict] = None

    # Placement Strategy, PACK
    placement_strategy: str = "PACK"

    # Fault tolerance
    elastic_training: bool = False
    max_failed_actors: int = 5
    max_actor_restarts: int = 0
    checkpoint_frequency: int = 5

    # Distributed callbacks
    distributed_callbacks: Optional[List] = None