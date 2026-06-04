import ray
from ray import logger
import os
import psutil
import inspect
from typing import Tuple, Dict, Any, List, Optional, Callable


def _validate_kwargs_for_func(kwargs: Dict[str, Any], func: Callable,
                              func_name: str):
    """Raise exception if kwargs are not valid for a given function."""
    valid_keys = inspect.getfullargspec(func)[0]
    invalid_kwargs = [k for k in kwargs if k not in valid_keys]
    if invalid_kwargs:
        raise TypeError(
            f"Got invalid keyword arguments to be passed to `{func_name}`. "
            f"Invalid keys: {invalid_kwargs}")


class RayActorTrainingError(RuntimeError):
    """Raised from RayXGBoostActor.train() when the local xgb.train function
    did not complete."""
    pass


class RayXGBoostTrainingStopped(RuntimeError):
    """Raised from RayXGBoostActor.train() when training was deliberately
    stopped."""
    pass


class RayXGBoostActorAvailable(RuntimeError):
    """Raise from `_update_scheduled_actor_states()` when new actors become
    available in elastic training"""
    pass

def _is_client_connected() -> bool:
    try:
        return ray.util.client.ray.is_connected()
    except Exception:
        return False


def _is_local_mode() -> bool:
    from ray.worker import LOCAL_MODE
    if ray.worker.global_worker.mode == LOCAL_MODE:
        return True
    else:
        return False


# def _ray_get_actor_cpus():
#     """
#     <class 'dict'>: {'CPU': [(0, 2.0)]}
#     如果通过资源组调度，资源为'CPU_group_f70e4996220f25bb82d4872501439af2': [(0, 1.0)]
#     :return:
#     """
#     # Get through resource IDs
#     resource_ids = ray.worker.get_resource_ids()
#     print(resource_ids)
#     if "CPU" in resource_ids:
#         return sum(cpu[1] for cpu in resource_ids["CPU"])
#     return None


def _ray_get_cluster_resource(resource_name = "CPU"):
    #检测集群总共的资源
    """
    ray.cluster_resources():
    {'memory': 3930233243.0, 'CPU': 4.0, 'object_store_memory': 1965116620.0, 'node:168.61.73.100': 1.0}
    :return:
    """
    resource = ray.cluster_resources()
    return resource.get(resource_name, None)


def _get_min_node_cpus():
    """
    ray.nodes()
    [{
    '

    ': 'fc3ec39225cedca52c8c258a23314b978baac9fe2b0ae99678bc7aca',
    'Alive': True,
    'NodeManagerAddress': '168.61.73.100',
    'NodeManagerHostname': '168-61-73-100',
    'NodeManagerPort': 38224,
    'ObjectManagerPort': 22896,
    'ObjectStoreSocketName': '/tmp/ray/session_2021-12-09_20-04-39_698912_5610/sockets/plasma_store',
    'RayletSocketName': '/tmp/ray/session_2021-12-09_20-04-39_698912_5610/sockets/raylet',
    'MetricsExportPort': 50377,
    'alive': True,
    'Resources': {
        'CPU': 4.0,
        'object_store_memory': 1965116620.0,
        'node:168.61.73.100': 1.0,
        'memory': 3930233243.0
    }
    }]
    :return:
    """
    min_node_cpus = min(
        node.get("Resources", {}).get("CPU", 0.0) for node in ray.nodes()
        if node.get("Alive", False))
    return min_node_cpus if min_node_cpus > 0.0 else 1.0



def force_on_current_node(task_or_actor):
    """Given a task or actor, place it on the current node.

    If the task or actor that is passed in already has custom resource
    requirements, then they will be overridden.

    If using Ray Client, the current node is the client server node.
    """
    def get_current_node_resource_key() -> str:
        """Get the Ray resource key for current node.
        It can be used for actor placement.
        If using Ray Client, this will return the resource key for the node that
        is running the client server.
        """
        #NodeID(fc3ec39225cedca52c8c258a23314b978baac9fe2b0ae99678bc7aca)
        current_node_id = ray.get_runtime_context().node_id.hex()
        for node in ray.nodes():
            if node["NodeID"] == current_node_id:
                # Found the node.
                for key in node["Resources"].keys():
                    if key.startswith("node:"):
                        return key
        else:
            raise ValueError("Cannot found the node dictionary for current node.")
    node_resource_key = get_current_node_resource_key()
    options = {"resources": {node_resource_key: 0.01}}
    return task_or_actor.options(**options)



def _validate_kwargs_for_func(kwargs: Dict[str, Any], func: Callable,
                              func_name: str):
    """Raise exception if kwargs are not valid for a given function."""
    valid_keys = inspect.getfullargspec(func)[0]
    invalid_kwargs = [k for k in kwargs if k not in valid_keys]
    if invalid_kwargs:
        raise TypeError(
            f"Got invalid keyword arguments to be passed to `{func_name}`. "
            f"Invalid keys: {invalid_kwargs}")


def get_xqconfig(key = "taskParam"):
    return {
        "mems_per_actor" : int(os.environ.get("mems_per_actor", -1))*1024,
        "num_actors" : int(os.environ.get("num_actors", -1)),
        "gpus_per_actor" : float(os.environ.get("gpus_per_actor", -1)),
        "cpus_per_actor" : int(os.environ.get("cpus_per_actor", -1)),
    }


def get_total_ray_resources():
    params = get_xqconfig()
    if params["cpus_per_actor"]!=-1:
        #分布式模式
        return {
            'CPU': params['num_actors']*params['cpus_per_actor'],
            'GPU': params['num_actors']*params['gpus_per_actor'],
        }
    else:
        #单机模式
        return {
            'CPU': _ray_get_cluster_resource("CPU"),
            'GPU': _ray_get_cluster_resource("GPU"),
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
            logger.info("启动Ray资源并连接成功！未检测到正在运行的Ray资源， 在本地启动一组新的Ray资源成功！")
    resources = ray.cluster_resources()
    logger.info(f"Ray总共资源为：[CPU：{resources['CPU']}, GPU：{resources['GPU']}]。")