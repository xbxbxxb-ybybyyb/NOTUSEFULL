import requests
import json
import random
import os
import time
import platform
import configparser
from os import path
from datetime import datetime

if platform.system().lower() == 'linux':
    import fcntl
elif platform.system().lower() == 'windows':
    import fcntlock as fcntl
else:
    raise Exception("系统：{} 暂不支持！".format(platform.system().lower()))
from FactorProvider.setEnv import xquantEnv, sysFlag



class FileLock:
    def __init__(self, filename):
        self.filename = filename
        self.handle = open(self.filename, 'w')

    def acquire(self):
        fcntl.lockf(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # LOCK_EX与LOCK_NB按位或使用不阻塞，报OSError错误

    def release(self):
        # 延迟0.5秒释放锁，其他进程非阻塞return，不再写入文件
        time.sleep(0.5)
        if platform.system().lower() == 'linux':
            fcntl.lockf(self.handle.fileno(), fcntl.LOCK_UN)
        elif platform.system().lower() == 'windows':
            fcntl.unlock(self.handle.fileno())
        else:
            raise Exception("系统：{} 暂不支持！".format(platform.system().lower()))

    def close(self):
        try:
            self.handle.close()
        except:
            pass

    def __del__(self):
        try:
            self.handle.close()
        except:
            pass


def get_apollo_conifg_mysql(name_space):
    if xquantEnv == 0:
        apollo_ip = "168.61.11.7:8085"
        appid = "XQUANT-SQLCONFIG.4de3541f231373626de652ff97a561c7"
    else:
        apollo_ip_pool = ["168.9.26.28:8080", "168.9.26.29:8080", "168.15.77.196:8080", "168.15.77.197:8080"]
        i = random.randint(0, len(apollo_ip_pool) - 1)
        apollo_ip = apollo_ip_pool[i]
        appid = "XQUANT-SQLCONFIG.4de3541f231373626de652ff97a561c7"
    apollo_http = "http://" + apollo_ip + "/configfiles/json/" + appid + f"/default/{name_space}"

    try:
        response = requests.get(apollo_http)
        status_code = response.status_code
        if status_code != 200:
            raise Exception("Apollo config connect failed !")
    except Exception as e:
        raise e
    res_json = response.text
    apollo_config = json.loads(res_json)
    return apollo_config


def write_provider_ini():
    file_path = os.path.join(os.path.dirname(__file__), "mysql_conf.ini")
    try:
        if not os.path.exists(file_path):
            if platform.system().lower() == 'linux':
                os.system("touch {}".format(file_path))
            else:
                pass
    except:
        pass
    if sysFlag == "xquant" or sysFlag == "big_data":
        name_space = "IT.xquant_" + str(xquantEnv)
    elif sysFlag == "tquant" or sysFlag == 'outside':
        name_space = "IT.tquant_" + str(xquantEnv)
    else:
        raise Exception("invalid sysFlag!")
    lock = FileLock(file_path)
    try:
        lock.acquire()
    except:
        # 有文件锁，其他进程调用时非阻塞会报错
        lock.close()
        time.sleep(1.5)  # 待第一个进程释放锁，保存文件
        return
    apollo_config = get_apollo_conifg_mysql(name_space)
    schemes = list(apollo_config.keys())
    conf_keys = ["host", "user", "passwd", "db", "port", "charset"]
    for scheme in schemes:
        lock.handle.write('[{0}]\n'.format(scheme))
        sql_config_v = apollo_config[scheme].split(",")
        for key in conf_keys:
            lock.handle.write("{0}={1}\n".format(key, sql_config_v[conf_keys.index(key)]))
        lock.handle.write('\n')

    lock.release()
    lock.close()


def file_time_interval():
    file_path = os.path.join(os.path.dirname(__file__), "mysql_conf.ini")
    if not os.path.exists(file_path):
        return 999999999
    else:
        now_time = time.time()
        time_arr = time.localtime(os.stat(file_path).st_mtime)
        local_time = time.mktime(time_arr)
        time_interval = now_time - local_time
        return time_interval



