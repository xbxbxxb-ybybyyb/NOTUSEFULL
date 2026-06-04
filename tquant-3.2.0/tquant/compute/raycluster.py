# -*-coding:utf-8-*-
from .util import *

from htds.compute.htdcf import HtdcfContext
from FactorProvider.setEnv import xquantEnv
from tquant.utils.event_trace import event_trace, EventTrace


def check_obj_store_mem(object_store_memory):
    """
    检查系统资源是否满足开启共享内存
    :param object_store_memory:
    :return:
    """
    local_mem = int(memory_limit()) / 1024 / 1024 / 1024
    if object_store_memory > local_mem:
        return False

    return True

def check_params(params, params_name):
    for params_type in ['num_cpus', 'memory', 'replicas']:
        if params_type not in params:
            raise Exception('{}中必须包含{}'.format(params_name, params_type))
        else:
            if type(params[params_type]) != int:
                raise Exception('参数{}必须为int'.format(params_type))
    return True

@event_trace
def RayCluster(master: dict, worker: dict, is_client=False, autoclose=True, local_object_store_memory=1, env_var=None):
    """
    初始化ray集群
    :param master: ray集群master的资源配置信息，num_cpus:cpu个数，memory：内存大小(单位GB)，replicas：pod副本数
    :param worker: ray集群worker的资源配置信息，num_cpus:cpu个数，memory：内存大小(单位GB)，replicas：pod副本数
    :param is_client: 判断为client模式还是cluster模式，默认值为False为cluster模式，如果填True为client模式
    :param autoclose: 是否开启ray集群计算完毕后自动回收功能,默认为True
    :param local_object_store_memory: 本地启动ray服务设置的对象存储的内存量,上限为20GB(单位GB)
    :param env_var: 启动ray集群时给各节点注入的环境变量
    :return:
    """
    params = {}
    if xquantEnv == 1:
        params['image'] = "168.61.13.178:5000/htzq/tquant_jupyter:prd_v2.0"
    else:
        params['image'] = "168.61.13.178:5000/htzq/tquant_jupyter:uat_v2.0"
    if type(local_object_store_memory) != int:
        raise Exception("local_object_store_memory必须为int")
    if local_object_store_memory > 20:
        raise Exception("local_object_store_memory上限为20G")
    params['master'] = master
    params['worker'] = worker
    params['is_client'] = is_client
    params['autoclose'] = autoclose
    params['local_object_store_memory'] = local_object_store_memory

    check_params(master, 'master')
    check_params(worker, 'worker')
    if not check_obj_store_mem(local_object_store_memory):
        raise Exception('内存不足')

    if env_var:
        if type(env_var) != dict:
            raise Exception("env_var的类型必须为dict")
        params['env_var'] = env_var

    hc = HtdcfContext(
        type='ray',
        is_remote=True,
        ray_cluster_params=params
    )
    return hc