import json
import os
import errno
import signal
import sys
from xquant.setXquantEnv import xquantEnv,testEnv
try:
    from ht_dubbo_client import ZookeeperRegistry, DubboClient, DubboClientError, ApplicationConfig
except:
    pass
from xquant.sandbox.utils import _check_Dir_Permissions, _noParmission
import time
import pickle
from functools import wraps
from threading import Thread
from hashlib import sha1
from subprocess import getstatusoutput
from pathlib import Path
import json
import sys
import threading
import time
try:
    from kafka import KafkaProducer
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError
except:
    pass

import logging
logging.getLogger('kazoo').setLevel(logging.CRITICAL)

_ROOT_DST_PATH = Path('/export/XTraderModel/')
_PRODUCT_PATH = 'PRODUCT'
_UAT_PATH = 'UAT'

def copyToUAT(src, dst):
    """
    拷贝文件到UAT目录
    :param src: 源目录
    :param dst: 目标目录（自动放入UAT）
    :return:
    """
    dst = _reHeadRoot(dst)
    dst = _ROOT_DST_PATH / _UAT_PATH / dst
    src = Path(src)
    # 对源和目标点进行判断
    # #   判断源是否存在
    if not src.exists():
        raise IOError("[errno:%s] copyToProduct(src = %s ) not exists" % (errno.EEXIST, src))
    # 记录源是文件名目录状态
    isSrcFile = src.is_file()
    
    (src_fp, src_fn) = os.path.split(src)
    (dst_fp, dst_fn) = os.path.split(dst)
    # 判断目标是否存在
    isDstExists = dst.exists()
    if isDstExists:  # 判定目录点
        if dst.is_dir():  # 目录
            # 目录点为目录，但源点为文件时把源文件名加在目标点
            if isSrcFile:
                dst = dst / src_fn
        else:  # 文件
            if not isSrcFile:  # 源为目录 而目标为存在的文件
                raise IOError("[errno:%s] copyFileGenMd5(dst = %s ) is File" % (errno.EEXIST, dst.__str__()))

    # 拷贝目录或文件
    re = _copyFile(src, dst)
    _genDirFileMd5(src, dst)
    return re


def copyToProduct(src, dst):
    """
    从UAT目录拷入文件或目录到PRODUCT目录
    :param src: 源目录（自动定向到UAT目录）
    :param dst: 目标目录（自动定向到PRODUCT目录）
    :return:
    """
    src = _reHeadRoot(src)
    dst = _reHeadRoot(dst)
    src = _ROOT_DST_PATH / _UAT_PATH / src
    dst = _ROOT_DST_PATH / _PRODUCT_PATH / dst
    # 对源和目标点进行判断
    # #   判断源是否存在
    if not src.exists():
        raise IOError(  "[errno:%s] copyToUAT(src = %s ) not exists" % (errno.EEXIST, src))
    # 记录源是文件名目录状态
    isSrcFile = src.is_file()
    (src_fp, src_fn) = os.path.split(src)
    # 判断目标是否存在
    if dst.exists():  # 判定目录点
        if dst.is_dir():  # 目录
            # 目录点为目录，但源点为文件时把源文件名加在目标点
            if isSrcFile:
                dst = dst / src_fn
        else:  # 文件
            if not isSrcFile:  # 源为目录 而目标为存在的文件
                raise IOError("[errno:%s] copyFileGenMd5(dst = %s ) is File" % (errno.EEXIST, dst.__str__()))

    # 拷贝目录或文件
    return _copyFile(src, dst)


def _reHeadRoot(src):
    if src[0] =='/':
        if len(src) > 1:
            src = src[1:]
        else:
            src = ''
    return src
#
# def coverFile(src : str,dst : str)-> str:
#     """
#     覆盖拷贝文件
#
#     :param dst: 目标目录
#     :param src: 源目录
#     :return:
#     """
#     if dst[0] =='/':
#         if len(dst) > 1:
#             dst = dst[1:]
#         else:
#             dst = ''
#
#     dst = os.path.join(_ROOT_DST_PATH,dst)
#
#     #对源和目标点进行判断
#     # #   判断源是否存在
#     if not os.path.exists(src):
#         raise IOError("[errno:%s] copyFileGenMd5(src = %s ) not exists" % (errno.EEXIST, src))
#     #记录源是文件名目录状态
#     isSrcFile = False
#     if os.path.isfile(src):
#         isSrcFile = True
#     (src_fp, src_fn) = os.path.split(src)
#     (dst_fp, dst_fn) = os.path.split(dst)
#     #判断目标是否存在
#     isDstExists = os.path.exists(dst)
#     if os.path.exists(dst): # 判定目录点
#         if os.path.isdir(dst): # 目录
#             # 目录点为目录，但源点为文件时把源文件名加在目标点
#             if isSrcFile:
#                 dst += src_fn
#         else: # 文件
#             if not isSrcFile: #源为目录 而目标为存在的文件
#                 raise IOError("[errno:%s] copyFileGenMd5(dst = %s ) is File" % (errno.EEXIST, dst))
#
#     #拷贝目录或文件
#     return _copyFile(src,dst)
#
#
# def genDirFileMd5(src: str, dst: str) -> None:
#     """
#     对目录文件生成md5
#
#     :param src: 源目录
#     :param dst: 目标目录 （由源向该目标写入对应文件的md5文件）
#     :return:
#     """
#     if dst[0] == '/':
#         dst = dst[1:] if len(dst) > 1 else ''
#
#     dst = os.path.join(_ROOT_DST_PATH, dst)
#     abssrc = os.path.abspath(src)
#
#     _genDirFileMd5(abssrc,dst)

def _rmDirTree(path: str) -> bool:
    """
    删除目录，如包含文件也一并删除

    :param path:
    :return:
    """
    if not _check_Dir_Permissions(path):
        raise IOError("[errno:%s] rmDirTree(path = %s) %s" % (errno.EPERM, path, _noParmission))
    
    if not os.path.exists(path):
        raise IOError("[errno:%s] rmDirTree(path = %s ) not exists" % (errno.EEXIST, path))
    abspath = os.path.abspath(path)
    if os.path.isfile(abspath):
        raise IOError("[errno:%s] rmDirTree(path = %s ) is file" % (errno.EFAULT, path))
    files = os.listdir(abspath)
    if len(files) == 0:
        os.rmdir(abspath)
        return True
    for file in files:
        tmpPath = os.path.join(abspath, file)
        if os.path.isfile(tmpPath):
            os.remove(tmpPath)
        else:
            rmDirTree(os.path.join(path, file))
    os.rmdir(abspath)
    return True


def _genDirFileMd5(src, dst):
    if src.is_file():
        (status, msg) = getstatusoutput("md5sum -b %s | awk '{print $1}' > %s.md5" % (src.__str__(), dst.__str__()))
        # (status, msg) = getstatusoutput("md5sum -b %s " % (src.__str__()))
        
        if not status == 0:
            raise SystemError(
                "[errno:%s] genDirFileMd5 md5sum error %s" % (errno.EFAULT, msg)
            )
        return
    paths = os.listdir(src)
    for p in paths:
        _genDirFileMd5(src/p,dst/p)


def _copyFile(src, dst) :
    (status, msg) = getstatusoutput("cp -rfv %s/. %s" % (src.__str__(),dst.__str__()))
    if not status == 0:
        raise SystemError(
            "[errno:%s] copyFile error %s" % (errno.EFAULT, msg)
        )
    return True
   

def statisticLog(module: str = '', genus: str = ''):
    """
    监控日志装饰器
    :return:
    :param module:  类型如下
            bigdata	大数据文件操作
            marketdata	高频行情访问模块
            tensorflow	tensorflow库操作
            factordata	量化因子访问模块
    :param genus:   所属类名
    :return:
    """
    def printStar(func):
        def _call(*args, **kw):
            # 日志输出
            # $statistic - log：为固定的埋点开始标识
            # module：为埋点模块名称（必填）
            # submodule：为埋点子模块名称（可选）
            # subject：为操作类型（可选）
            # platform：为平台标识（必填），预定义值见下文
            subject = func.__name__
            if len(genus)>0:
                subject = genus + "." + subject
            if os.environ.get('BIG_DATA_PREPATH', False) or not os.environ.get('ENV_VERSION',False):
                print("$statistic-log,module=%s,subject=%s,platform=XQUANT-Cloud" % (module, subject))
                # print(
                #     {
                #         "module":module,
                #         "subject":subject,
                #         "platform":"XQUANT-Cloud"
                #     }
                # )
            else:
                try:
                    # value = {"tag": "statistic", "message":"$statistic-log,module=%s,subject=%s,platform=XQUANT-Cloud" % (module,subject)}
                    value = {
                        "tag": "statistic",
                        "message":{
                        "module": module,
                        "subject":subject,
                        "platform":"XQUANT-Cloud"
                        }
                    }
                    producer = Kafka_producer(KAFKA_TOPIC)
                    producer.sendjsondata(value)
                except:
                    pass
            return func(*args, **kw)
        return _call
    return printStar


# GRPC自动缓存处理
# _cache = None  # 缓存字典
# _CACHE_FILE = '__tmp_cache.dump'
# def memorize(duration=-1):
#     '''
#     自动缓存
#     :param duration:
#     :return:
#     '''
#     def _memoize(fun):
#         @wraps(fun)  # 自动复制函数信息
#         def __memoize(*args, **kw):
#             key = pickle.dumps((fun.func_name, args, kw))
#             key = sha1(key).hexdigest()
#
#             # 是否已缓存？
#             if key in _cache:
#                 # 是否过期？
#                 if duration == -1:  # 永不过期
#                     return False
#                 if time.time() - _cache[key]['time'] > duration :
#                     return _cache[key]['value']
#                 else:
#                     del(_cache[key])
#                     # 运行函数
#             result = fun(*args, **kw)
#             # 保存结果
#             _cache[key] = {
#                 'value': result,
#                 'time': time.time()
#             }
#             def inFile(cache):
#                 with open(_CACHE_FILE,"wb") as f:
#                     pickle.dump(cache, f)
#                     f.flush()
#             Thread(target=inFile,args=(_cache,)).start()
#             return result
#         return __memoize
#     return _memoize
#
# def initCache():
#     """
#     初始化缓存(从文件中读取)
#     :return:
#     """
#     global _cache
#     global _CACHE_FILE
#     if _cache is None:
#         _cache = {}
#         def readCacheFile():
#             if os.path.exists(_CACHE_FILE):
#                 with open(_CACHE_FILE,"rb") as f :
#                     pickle.load(f,_cache)
#         Thread(target=readCacheFile).start()
# initCache()


def queryEnv():
    import socket
    try:
        env_HOSTNAME = socket.gethostname()
        if env_HOSTNAME.startswith("datanode"):
            return 'bigdata-platform'
        elif env_HOSTNAME.startswith('proxy'):
            return 'deeplearning-gpu-platform'
        elif env_HOSTNAME.startswith('cproxy'):
            return 'deeplearning-cpu-platform'
        elif env_HOSTNAME.startswith('xquant'):
            return 'cloud-platform'
        else:
            import logging
            logging.basicConfig(format="%(levelname)s:%(message)s")
            logging.warning("The execution environment is unknown and may be a new host ")
    except:
        raise Exception("queryEnv failed!: unknown Executor Environment!")

def __find_config(path):
    while True:
        path = os.path.split(path)[0]
        dir_list = os.listdir(path)
        for dir in dir_list:
            if dir == "__xquant_config.py":
                return path
        if path == os.path.split(path)[0]:
            break
    raise Exception("未找到__xquant_config文件！")

from xquant.conf.DubboConf import DUBBO_CONFIG
DUBBO_APPLICATIONCONFIG_UTILS = DUBBO_CONFIG["DUBBO_CONFIG_UTILS"]
DUBBO_APPLICATIONCONFIG = DUBBO_CONFIG["DUBBO_CONFIG"]
DUBBO_CONFIG_IP = DUBBO_CONFIG["DUBBO_CONFIG_IP"]

if os.environ.get('ENV_VERSION',False):
    # jurisdictionData dubbo配置
    jurisdictionData_service_interface = 'com.htsc.xquant.factor.manager.server.python.GenerateJurisdictionFileService'
    jurisdictionData_config = ApplicationConfig(DUBBO_APPLICATIONCONFIG_UTILS)
    jurisdictionData_registry = ZookeeperRegistry(DUBBO_CONFIG_IP, jurisdictionData_config)
    jurisdictionData_user_provider = DubboClient(jurisdictionData_service_interface, jurisdictionData_registry, version="1.0.0")

    # xquantConfig dubbo配置
    xquantConfig_service_interface = 'com.htsc.xquant.factor.manager.server.python.CreateXquantConfigService'
    xquantConfig_config = ApplicationConfig(DUBBO_APPLICATIONCONFIG_UTILS)
    xquantConfig_registry = ZookeeperRegistry(DUBBO_CONFIG_IP, xquantConfig_config)
    xquantConfig_user_provider = DubboClient(xquantConfig_service_interface, xquantConfig_registry, version="1.0.0")
    
else:
     # jurisdictionData dubbo配置
    jurisdictionData_service_interface = None
    jurisdictionData_config = None
    jurisdictionData_registry = None
    jurisdictionData_user_provider = None

    # xquantConfig dubbo配置
    xquantConfig_service_interface = None
    xquantConfig_config = None
    xquantConfig_registry = None
    xquantConfig_user_provider = None

def get_jurisdictionData():
    if os.environ.get('BIG_DATA_PREPATH', False) or not os.environ.get('ENV_VERSION',False):
        abs_path = os.environ['BIG_DATA_PREPATH']
        sys_path = __find_config(abs_path)
        sys.path.append(sys_path)
        import __jurisdictionData_config
        jurisdictionData_dict = __jurisdictionData_config.jurisdictionData_dict
        return jurisdictionData_dict
    else:
        userAccount = get_userid()
        if not userAccount:
            raise Exception("未获取到userId!")
        try:
            # 调用dubbo接口
            json_dict = {"request": {"userAccount": str(userAccount)}}
            json_str = json.dumps(json_dict)
            get_result = jurisdictionData_user_provider.GenerateJurisdictionFile(json_str)
            return json.loads(get_result.split("=")[1].strip())
        except DubboClientError as e:
            raise "Exception " + str(e)

def get_userid():
    XQUANT_CONF_FILE = os.environ['XQUANT_CONF_FILE']
    # XQUANT_CONF_FILE = "/tmp/python/xquant_conf"
    with open(XQUANT_CONF_FILE, 'r') as f:
        r = f.readlines()
        for line in r:
            if line.startswith("userId"):
                return line.strip().split("=")[-1].strip()

def get_xquantConfig():
    if os.environ.get('BIG_DATA_PREPATH', False) or not os.environ.get('ENV_VERSION',False):
        abs_path = os.environ['BIG_DATA_PREPATH']
        sys_path = __find_config(abs_path)
        sys.path.append(sys_path)
        import __xquant_config
        __xquant_config_dict = __xquant_config.__xquant_config_json
        return __xquant_config_dict
    elif os.environ.get('IS_JUPYTER', False):
        abs_path = "/app/anaconda/lib/python3.6/site-packages/xquant/"
        sys_path = __find_config(abs_path)
        sys.path.append(sys_path)
        import __xquant_config
        __xquant_config_dict = __xquant_config.__xquant_config_json
        return __xquant_config_dict
    else:
        userAccount = get_userid()
        if not userAccount:
            raise Exception("未获取到userId!")
        try:
            # 调用dubbo接口
            json_dict = {"request": {"userAccount": str(userAccount)}}
            json_str = json.dumps(json_dict)
            get_result = xquantConfig_user_provider.CreateXquantConfig(json_str)
            return json.loads(get_result.split("=")[1])
        except:
            raise Exception("用户配置文件生成失败！")


def getKafkaKey():
    XQUANT_CONF_FILE = os.environ['XQUANT_CONF_FILE']
    # XQUANT_CONF_FILE = "/tmp/python/xquant_conf"
    with open(XQUANT_CONF_FILE, 'r') as f:
        r = f.readlines()
        for line in r:
            if line.startswith("logkeyPrefix"):
                return line.strip().split("=")[-1].strip()

if xquantEnv == 0:
    KAFAKA_CONFIG = "168.61.2.47:9092,168.61.2.48:9092,168.61.2.49:9092"
    # KAFKA_TOPIC = "cgc_task_log"
    KAFKA_TOPIC = "XQUANT-STATISTIC-LOG-NOPRD"
elif xquantEnv == 1:
    KAFAKA_CONFIG = "168.9.65.49:9092,168.9.65.50:9092,168.9.65.51:9092,168.9.65.136:9092,168.9.65.137:9092,168.11.225.16:9092,168.11.225.17:9092,168.11.225.18:9092"
    # KAFKA_TOPIC = "MXSF-AIMAP-TASK-LOG"
    KAFKA_TOPIC = "XQUANT-STATISTIC-LOG"


def kafka_singleton(Kafka_producer):
    #instance_mark是除了进程id之外，单例的标志符
    _instance = {}
    def inner(*args, **kargs):
        if kargs.get("topic"):
            #判断哪个参数字段作为标志符
            instance_mark = kargs["topic"]
        else:
            instance_mark = args[0]
        if (os.getpid(), instance_mark) not in _instance:
            _instance[(os.getpid(), instance_mark)] = Kafka_producer(*args, **kargs)
        return _instance[(os.getpid(), instance_mark)]
    return inner

@kafka_singleton
class Kafka_producer():
    '''''
    生产模块：根据不同的key，区分消息
    '''
    def __init__(self,topic):
        self.kafkatopic = topic
        self.key = getKafkaKey()
        if not self.key:
            raise Exception("获取kafka key 失败！")
        bootstrap_servers = KAFAKA_CONFIG
        self.producer = KafkaProducer(bootstrap_servers = bootstrap_servers)

    def sendjsondata(self, params):
        try:
            parmas_message = json.dumps(params,ensure_ascii=False)
            producer = self.producer
            v = parmas_message.encode('utf-8')
            k = self.key.encode('utf-8')
            producer.send(self.kafkatopic, key=k, value= v)
            producer.flush()
        except KafkaError as e:
            print(e)


def utils_set_timeout(num,callback):
    def wrap(func):
        def handle(signum, frame):  # 收到信号 SIGALRM 后的回调函数，第一个参数是信号的数字，第二个参数是the interrupted stack frame.
            raise Exception(callback)

        def to_do(*args, **kwargs):
            signal.signal(signal.SIGALRM, handle)  # 设置信号和回调函数
            signal.alarm(num)  # 设置 num 秒的闹钟
            r = func(*args, **kwargs)
            signal.alarm(0)  # 关闭闹钟
            return r
        return to_do
    return wrap