# -*-coding:utf-8-*-
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
import requests
import math
import os
import sys
import psutil
import logging

import json


logger = logging.getLogger('ray.cluster')
application_json_path = r"/project/app/application.json"


RAY_IMAGE = {
    "DEV": "168.61.13.178:5000/htzq/tquant_jupyter:test",
    "UAT": "168.61.13.178:5000/htzq/tquant_jupyter:uat_v2.0",
    "PRD": "168.61.13.178:5000/htzq/tquant_jupyter:prd_v2.0"
}

RAY_START_DEFAULT = {
    "env_var": {},
    "docker_image": "168.61.13.178:5000/htzq/tquant_jupyter:uat_v2.0",
    "dashboard": True,
    "dashboard_port": 8265,
    "local_object_store_memory": 1,
    "quotaGroup": "g1"
}

RAY_MASTER_DEFAULT = {
    "role": "master",
    "num_cpus": 2,
    "num_gpus": 0,
    "memory": 2,
    "replicas": 1,
    "object-store-memory": 1
}

RAY_WORKER_DEFAULT = {
    "role": "worker",
    "num_cpus": 2,
    "num_gpus": 0,
    "memory": 2,
    "replicas": 1,
    "object-store-memory": 1
}

RAY_START_PARAMS_LIST = ['object-store-memory', 'redis-max-memory', 'log-to-driver', 'node-ip-address', 'object-id-seed',
                         'local-mode', 'driver-object-store-memory', 'ignore-reinit-error', 'num-redis-shards',
                         'redis-max-clients', 'redis-password', 'plasma-directory', 'huge-pages', 'include-java',
                         'job-id', 'configure-logging', 'configure-logging', 'logging-format',
                         'plasma-store-socket-name', 'raylet-socket-name', 'temp-dir', 'load-code-from-local',
                         'java-worker-options', 'internal-config', 'lru-evict']


@contextmanager
def ignoring(*exceptions):
    try:
        yield
    except exceptions as e:
        pass


def singleton(cls):
    _instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in _instances:
            _instances[cls] = cls(*args, **kwargs)
        return _instances[cls]

    return get_instance


@singleton
def get_application_json():
    if os.path.exists(application_json_path):

        with open(application_json_path, 'r') as f:
            data = json.load(f)
            return data
    else:
        return None


def memory_limit():
    """Get the memory limit (in bytes) for this system.

    Takes the minimum value from the following locations:

    - Total system host memory
    - Cgroups limit (if set)
    - RSS rlimit (if set)
    """
    limit = psutil.virtual_memory().total

    # Check cgroups if available
    if sys.platform == "linux":
        try:
            with open("/sys/fs/cgroup/memory/memory.limit_in_bytes") as f:
                cgroups_limit = int(f.read())
            if cgroups_limit > 0:
                limit = min(limit, cgroups_limit)
        except Exception:
            pass

    # Check rlimit if available
    try:
        import resource

        hard_limit = resource.getrlimit(resource.RLIMIT_RSS)[1]
        if hard_limit > 0:
            limit = min(limit, hard_limit)
    except (ImportError, OSError):
        pass

    return limit


def cpu_count():
    """Get the available CPU count for this system.

    Takes the minimum value from the following locations:

    - Total system cpus available on the host.
    - CPU Affinity (if set)
    - Cgroups limit (if set)
    """
    count = os.cpu_count()

    # Check CPU affinity if available
    try:
        affinity_count = len(psutil.Process().cpu_affinity())
        if affinity_count > 0:
            count = min(count, affinity_count)
    except Exception:
        pass

    # Check cgroups if available
    if sys.platform == "linux":
        # The directory name isn't standardized across linux distros, check both
        for dirname in ["cpuacct,cpu", "cpu,cpuacct"]:
            try:
                with open("/sys/fs/cgroup/%s/cpu.cfs_quota_us" % dirname) as f:
                    quota = int(f.read())
                with open("/sys/fs/cgroup/%s/cpu.cfs_period_us" % dirname) as f:
                    period = int(f.read())
                # We round up on fractional CPUs
                cgroups_count = math.ceil(quota / period)
                if cgroups_count > 0:
                    count = min(count, cgroups_count)
                break
            except Exception:
                pass

    return count


MEMORY_LIMIT = memory_limit()
CPU_COUNT = cpu_count()


def parse_memory_limit(memory_limit, nthreads, total_cores=CPU_COUNT):
    if memory_limit is None:
        return None

    if memory_limit == "auto":
        memory_limit = int(MEMORY_LIMIT * min(1, nthreads / total_cores))
    with ignoring(ValueError, TypeError):
        memory_limit = float(memory_limit)
        if isinstance(memory_limit, float) and memory_limit <= 1:
            memory_limit = int(memory_limit * MEMORY_LIMIT)

    if isinstance(memory_limit, str):
        memory_limit = parse_bytes(memory_limit)
    else:
        memory_limit = int(memory_limit)

    return min(memory_limit, MEMORY_LIMIT)


def parse_bytes(s):
    """ Parse byte string to numbers

    >>> parse_bytes('100')
    100
    >>> parse_bytes('100 MB')
    100000000
    >>> parse_bytes('100M')
    100000000
    >>> parse_bytes('5kB')
    5000
    >>> parse_bytes('5.4 kB')
    5400
    >>> parse_bytes('1kiB')
    1024
    >>> parse_bytes('1e6')
    1000000
    >>> parse_bytes('1e6 kB')
    1000000000
    >>> parse_bytes('MB')
    1000000
    >>> parse_bytes(123)
    123
    >>> parse_bytes('5 foos')  # doctest: +SKIP
    ValueError: Could not interpret 'foos' as a byte unit
    """
    if isinstance(s, (int, float)):
        return int(s)
    s = s.replace(" ", "")
    if not s[0].isdigit():
        s = "1" + s

    for i in range(len(s) - 1, -1, -1):
        if not s[i].isalpha():
            break
    index = i + 1

    prefix = s[:index]
    suffix = s[index:]

    try:
        n = float(prefix)
    except ValueError:
        raise ValueError("Could not interpret '%s' as a number" % prefix)

    try:
        multiplier = byte_sizes[suffix.lower()]
    except KeyError:
        raise ValueError("Could not interpret '%s' as a byte unit" % suffix)

    result = n * multiplier
    return int(result)


byte_sizes = {
    "kB": 10 ** 3,
    "MB": 10 ** 6,
    "GB": 10 ** 9,
    "TB": 10 ** 12,
    "PB": 10 ** 15,
    "KiB": 2 ** 10,
    "MiB": 2 ** 20,
    "GiB": 2 ** 30,
    "TiB": 2 ** 40,
    "PiB": 2 ** 50,
    "B": 1,
    "": 1,
}
byte_sizes = {k.lower(): v for k, v in byte_sizes.items()}
byte_sizes.update({k[0]: v for k, v in byte_sizes.items() if k and "i" not in k})
byte_sizes.update({k[:-1]: v for k, v in byte_sizes.items() if k and "i" in k})


def get_swagger_ip():
    """
    Docstring:
    Get swagger IP in pod.
    """
    env_dist = os.environ
    application_path = r'/project/app/application.json'
    if 'CGC_JOB_MANAGER_IP' in env_dist.keys() and env_dist['CGC_JOB_MANAGER_IP'] is not None and env_dist[
        'CGC_JOB_MANAGER_IP'] is not '':
        swagger_ip = env_dist['CGC_JOB_MANAGER_IP']
        logger.debug("get_swagger_ip function: Read swagger_ip {0} from environment variable .".format(swagger_ip))
        return swagger_ip
    elif Path(application_path).is_file():
        with open(application_path) as fp:
            application_json = json.load(fp)
            swagger_ip = application_json['runtimeInfo']['dockerStatus']['endpoints'][0]['host']
            logger.debug("get_swagger_ip function: Read swagger_ip {0} from application path .".format(swagger_ip))
            return swagger_ip
    else:
        raise Exception('Get get_swagger_IP failure !')


def get_job_detail(jobid):
    """
    Docstring:
    根据jobid获取job详细信息.

    Parameters
    ----------
    jobid ： jobid

    return
    ------
    """
    headers = {'Authorization': 'Basic YWRtaW4K', "Content-Type": "application/json"}
    get_url = ('http://{0}:30014/api/v1/jobs/{1}'.format(get_swagger_ip(), jobid))
    logger.debug('get_ray_job function get_url: {0}.'.format(get_url))
    res = requests.get(get_url, headers=headers)
    logger.debug('get ray job done.')
    return res.json()

