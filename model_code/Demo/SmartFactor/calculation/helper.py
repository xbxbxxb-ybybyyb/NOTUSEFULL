import ray
import inspect
import os
import signal


def get_docker_memory():
    with open('/sys/fs/cgroup/memory/memory.limit_in_bytes') as f:
        byte_memory_limit = int(f.read())
    with open('/sys/fs/cgroup/memory/memory.usage_in_bytes') as f:
        byte_memory_usage = int(f.read())
    return min(int((byte_memory_limit - byte_memory_usage) * 0.4), 10000000000)


def get_docker_cpu():
    with open('/sys/fs/cgroup/cpu/cpu.cfs_quota_us') as f:
        cpu_quota = int(f.read())
    with open('/sys/fs/cgroup/cpu/cpu.cfs_period_us') as f:
        cpu_period = int(f.read())
    return int(cpu_quota / cpu_period)


def set_ray_options(num_cpus, object_store_memory, options, start_mode='task'):
    """
    start_mode: actor模式示num_cpus为1，task模式num_cpus为docker的所有cpu
    """
    if ray.is_initialized():
        raise Exception("Ray计算环境启动失败：当前有正在使用的Ray计算环境，请用ps -ef|grep ray查看并停止！")
    if num_cpus is None:
        num_cpus = max(1, get_docker_cpu() - 1)
    if options is None:
        options = {}
    if object_store_memory is None:
        object_store_memory = get_docker_memory()
    try:
        if not start_mode == 'actor':
            print('Ray启动占用的CPU数：{}'.format((num_cpus)))
            print('Ray启动占用的内存数：{}'.format(object_store_memory))
            ray.init(num_cpus=num_cpus, object_store_memory=object_store_memory, **options)
        else:
            print('Ray启动占用的CPU数：{}'.format(1))
            print('Ray启动占用的内存数：{}'.format(object_store_memory * 0.5))
            ray.init(num_cpus=1, object_store_memory=int(object_store_memory * 0.5), **options)
    except Exception as e:
        # print('Ray启动占用的CPU数：{}'.format((num_cpus)))
        # print('Ray启动占用的内存数：{}'.format(object_store_memory))
        raise e


def parse_callback_params(func, has_factor_list=False):
    sig = inspect.signature(func)
    parameters = sig.parameters
    new_params_dict = {}
    for pidx, param_key in enumerate(parameters):
        param = parameters[param_key]
        if param.name != 'self' and pidx == 0:
            print('ERROR: calc_callback第一个参数必须为self！当前为{}！'.format(param.name))
            os.killpg(os.getpgid(os.getpid()), signal.SIGINT)
        if not has_factor_list:
            if param.name != 'df_dict' and pidx == 1:
                print('ERROR: calc_callback第二个参数必须为df_dict！当前为{}！'.format(param.name))
                os.killpg(os.getpgid(os.getpid()), signal.SIGINT)
        else:
            if param.name != 'factor_list' and pidx == 1:
                print('ERROR: calc_callback第二个参数必须为factor_list！当前为{}！'.format(param.name))
                os.killpg(os.getpgid(os.getpid()), signal.SIGINT)
            if param.name != 'df_dict' and pidx == 2:
                print('ERROR: calc_callback第三个参数必须为df_dict！当前为{}！'.format(param.name))
                os.killpg(os.getpgid(os.getpid()), signal.SIGINT)
        try:
            if not param.default == param.empty:
                new_params_dict[param.name] = param.default
        except:
            # 无法识别的类型，必然是用户自定义传参
            new_params_dict[param.name] = param.default
    return new_params_dict
