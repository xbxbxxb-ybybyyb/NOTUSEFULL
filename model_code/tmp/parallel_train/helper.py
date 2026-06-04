import itertools
import os
import sys
from typing import Dict, Any, Optional
from enum import Enum
import ray
from ray import logger
import warnings
import copy


TaskMode = Enum('TaskMode', ('DistTrain', 'LocalTrain',))


def _validate_task_mode(task_mode):
    from .trainer import TaskMode
    if isinstance(task_mode, str):
        if task_mode not in [t.name for t in TaskMode]:
            raise ValueError(f"task_mode must be in [LocalTrain, DistTrain], but it was {task_mode}")
        task_mode = TaskMode[task_mode]
    else:
        raise ValueError(
            f"`task_mode` must be a str, "
            f"but it was {type(task_mode)}."
            f"\nFIX THIS preferably by passing a str in [LocalTrain, DistTrain] as the `task_mode` parameter."
        )
    return task_mode


def _validate_backend_wrapper(cls, task_mode):
    from .trainer import TaskMode
    from .backend import LocalTrainBackend, DistTrainBackend
    if task_mode == TaskMode.DistTrain:
        if not issubclass(cls, DistTrainBackend):
            raise ValueError(
                f"in `DistTrain` mode, backend must be a subclass of DistTrainBackend, but is was {cls.__name__}."
            )
    elif task_mode == TaskMode.LocalTrain:
        if not issubclass(cls, LocalTrainBackend):
            raise ValueError(
                f"in `LocalTrain` mode, backend must be a subclass of LocalTrainBackend, but is was {cls.__name__}."
            )
    else:
        raise ValueError(
            f"unsupported backend class."
        )


def _validate_ray_params(ray_params):
    from .trainer import RayParams
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
    if ray_params.num_workers <= 0:
        raise ValueError(
            "The `num_actors` parameter is set to 0. Please always specify "
            "the number of distributed actors you want to use."
            "\nFIX THIS by passing a `RayParams(num_actors=X)` argument.")
    elif ray_params.num_workers < 2:
        warnings.warn(
            f"`num_actors` in `ray_params` is smaller than 2 "
            f"({ray_params.num_workers}). XGBoost will NOT be distributed!")
    return ray_params


def _ray_get_cluster_resource(resource_name=None):
    """
    ray.cluster_resources():
    {'memory': 3930233243.0, 'CPU': 4.0, 'object_store_memory': 1965116620.0, 'node:168.61.73.100': 1.0}
    :return:
    """
    resources = ray.cluster_resources()
    if not resources.get("GPU"):
        resources["GPU"] = 0
    if resource_name:
        return resources.get(resource_name, None)
    else:
        return resources


def get_xqconfig():
    return {
        "num_workers": int(os.environ.get("num_actors", -1)),
        "gpus_per_worker": float(os.environ.get("gpus_per_actor", -1)),
        "cpus_per_worker": int(os.environ.get("cpus_per_actor", -1)),
    }


def auto_connect_ray():
    #自动连接ray集群
    os.environ.setdefault("RAY_IGNORE_UNHANDLED_ERRORS", "1")
    if not ray.is_initialized():
        try:
            #连接已有的ray集群
            ray.init("auto")
            logger.info("连接已有Ray资源成功! 已检测到一组正在运行的Ray资源，自动连接成功！请确认此集群没有其他主程序在占用，否则会造成任务冲突。")
        except:
            ray.init()
                #默认10%的内存作为共享内存
            logger.info("启动Ray资源并连接成功！未检测到正在运行的Ray资源， 在本地启动一组新的Ray资源成功！")
    resources = _ray_get_cluster_resource()
    logger.info(f"Ray总共资源为：[CPU：{resources['CPU']}, GPU：{resources.get('GPU')}]。")


def get_total_ray_resources():
    params = get_xqconfig()
    if params["cpus_per_worker"] != -1:
        #分布式模式
        return {
            'CPU': params['num_workers']*params['cpus_per_worker'],
            'GPU': params['num_workers']*params['gpus_per_worker'],
        }
    else:
        #单机模式
        return {
            'CPU': _ray_get_cluster_resource("CPU"),
            'GPU': _ray_get_cluster_resource("GPU"),
        }


def split_task_by_data_param(data_params: Dict[str, Any], num_actors: int, is_mode_actor=True):
    """
    根据data_params切分任务
    Args:
        num_actors:
        data_params:
        is_mode_actor:
    """
    from .trainer import SplitTaskParam
    total_task_nums = 0
    single_task_key = []
    share_params = {}
    single_task_params = {}
    for key, value in data_params.items():
        if isinstance(value, SplitTaskParam):
            single_task_params[key] = value.value
            single_task_key.append(key)
        else:
            share_params[key] = value

    if single_task_params:
        total_tasks = []
        for task in itertools.product(*single_task_params.values()):
            total_tasks.append(task)
        total_task_nums = len(total_tasks)

    if total_task_nums < num_actors:
        warnings.warn(f"资源闲置告警！切分的并行任务数{total_task_nums}小于当前设置并发度{num_actors}！请调小并发度，或者通过SplitTaskParam设置更多任务！")
    # elif total_task_nums > num_actors:
    #     if is_mode_actor:
    #         raise Exception(f"资源不够告警！当前Actor计算模式下，任务与Actor一对一绑定运行，请保证任务数{total_task_nums}和并发度{num_actors}一致！")

    data_params_groups = []
    if len(single_task_key) == 0:
        warnings.warn(f"任务data_params一致告警！未通过SplitTaskParam设置并行任务参数，当前每个任务的data_params一致，请确认是否是重复任务运行！")
        # 若没有并行参数，则返回
        for i in range(num_actors):
            data_params_groups.append(data_params)

    for value in total_tasks:
        #按并行参数切分出任务
        params = copy.copy(share_params)
        for idx, sub_v in enumerate(value):
            params[single_task_key[idx]] = sub_v
        logger.debug("split_task_by_data_param: 切分的单个任务参数为{}。".format(params))
        data_params_groups.append(params)
    return data_params_groups


def get_backend_config(backend) -> type:
    from .backend import DistBackendConfig, DistTrainBackend, LocalTrainBackend
    class ConfigToBackend(DistBackendConfig):
        _backend = None
        backend: Optional[str] = None
        init_method: str = "env"
        timeout_s: int = 1800
        @property
        def backend_cls(self):
            return self._backend

    if issubclass(backend, DistTrainBackend):
        # Actor模式传递用户自定义Backend进BackendExecutor
        config = ConfigToBackend()
        ConfigToBackend._backend = backend
        return config
    elif issubclass(backend, LocalTrainBackend):
        # LocalTrain模式传递模拟基类LocalTrainBackend进BackendExecutor，不改变源代码情况下，backend_cfg必传
        config = ConfigToBackend()
        ConfigToBackend._backend = DistTrainBackend
        return config
    elif isinstance(backend, str):
        from .trainer import BACKEND_NAME_TO_CONFIG_CLS_NAME
        if backend in BACKEND_NAME_TO_CONFIG_CLS_NAME:
            import importlib
            config_cls = getattr(
                importlib.import_module(f"train"
                                        f".{backend}"),
                BACKEND_NAME_TO_CONFIG_CLS_NAME[backend])
        else:
            sys.path.append('.')
            import importlib
            try:
                config_cls = getattr(
                    importlib.import_module(f"{backend}"), backend)
            except:
                raise ValueError(f"Invalid backend str: {backend}. "
                                 f"Supported string values are: "
                                 f"{BACKEND_NAME_TO_CONFIG_CLS_NAME.keys()}")
        return config_cls
    else:
        raise TypeError(f"Invalid type for backend: {type(backend)}.")
