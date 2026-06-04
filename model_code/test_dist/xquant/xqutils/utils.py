import os
import shutil
import errno
import signal
import json
import stat
import threading
import base64
from os import path
from datetime import datetime
from xquant.setXquantEnv import xquantEnv, testEnv
from functools import wraps
from hashlib import sha1
from subprocess import getstatusoutput
from pathlib import Path
from Crypto.Cipher import AES


try:
    import paramiko
except:
    pass
import warnings
import hashlib

try:
    from kafka import KafkaProducer
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError
except:
    pass

import logging

logging.getLogger('kazoo').setLevel(logging.CRITICAL)

CIPHER_KEY = 'eUMMn9zWE8EBPHt6hkNooQ=='


def decrypt(ciphertext):
    def _unpad(s):
        return s[:-ord(s[len(s) - 1:])]

    enc = base64.b64decode(ciphertext)
    iv = enc[:AES.block_size]
    cipher = AES.new(CIPHER_KEY, AES.MODE_CBC, iv)
    return _unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')


def _uat_limit_time():
    from FactorProvider.factordata.xqfactor import tradingDay

    today = datetime.today().strftime("%Y%m%d")
    # 非交易日不做限制
    if len(tradingDay(today, today)) == 0:
        return True

    begin_time = datetime.strptime('{}09'.format(today), '%Y%m%d%H')
    end_time = datetime.strptime('{}16'.format(today), '%Y%m%d%H')
    now = datetime.now()
    if begin_time < now < end_time:
        return False
    return True


def _copyFile(src, dst):
    (status, msg) = getstatusoutput("cp -rfv %s/. %s" % (src.__str__(), dst.__str__()))
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
            if len(genus) > 0:
                if module == "thirdpartydata" and genus == "FactorData" and subject == "get_factor_value":
                    table_name = kw.get("library_name", "unknow") if kw.get("library_name", None) else args[1]
                    subject = "TABLE_"+str(table_name)
                else:
                    subject = genus + "." + subject
            subject = subject[:50]
            if os.environ.get('BIG_DATA_PREPATH', False):
                print("$statistic-log,module=%s,subject=%s,platform=XQUANT-Cloud" % (module, subject))
            else:
                try:
                    # value = {"tag": "statistic", "message":"$statistic-log,module=%s,subject=%s,platform=XQUANT-Cloud" % (module,subject)}
                    value = {
                        "tag": "statistic",
                        "message": {
                            "module": module,
                            "subject": subject,
                            "platform": "XQUANT-Cloud"
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
    # instance_mark是除了进程id之外，单例的标志符
    _instance = {}

    def inner(*args, **kargs):
        if kargs.get("topic"):
            # 判断哪个参数字段作为标志符
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

    def __init__(self, topic):
        self.kafkatopic = topic
        self.key = getKafkaKey()
        if not self.key:
            raise Exception("获取kafka key 失败！")
        bootstrap_servers = KAFAKA_CONFIG
        self.producer = KafkaProducer(bootstrap_servers=bootstrap_servers)

    def sendjsondata(self, params):
        try:
            parmas_message = json.dumps(params, ensure_ascii=False)
            producer = self.producer
            v = parmas_message.encode('utf-8')
            k = self.key.encode('utf-8')
            producer.send(self.kafkatopic, key=k, value=v)
            producer.flush()
        except KafkaError as e:
            print(e)


def utils_set_timeout(num, callback):
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


@statisticLog('xqutils', "utils")
def copy2XTrader(copy_path, md5_check=False, **kargs):
    """
    拷贝文件到XTrader，目标文件路径和源文件路径相同
    :param src:源目录或文件
    :param dst:目标目录或文件
    :param md5_check:是否进行MD5校验
    :return:
    """
    assert copy_path[:5] == "/data", "拷贝文件路径必须以'/data'开头，请重新输入！"
    try:
        file_path = path.join(path.dirname(__file__), "encrypted_copy.json")
        with open(file_path, 'rb') as f:
            ENCRYPTED_HOSTS = json.load(f)
    except Exception as e:
        raise Exception("无法读取加密文件")

    ip_config = {}
    if xquantEnv == 0:
        ip_config['ip'] = "168.63.17.205"
        ip_config['port'] = 22
        ip_config['username'] = "log"
        ip_config['password'] = decrypt(ENCRYPTED_HOSTS['xtrade']['test']['ciphertext'])
        ip_config['root_path'] = "/home/log/test/"
    else:
        # ip_config['ip'] = "168.9.38.11"
        # ip_config['port'] = 22
        # ip_config['username'] = "ats-model"
        # ip_config['password'] = "ats-model"
        # ip_config['root_path'] = "/home/ats-model/"
    
        ip_config['ip'] = "168.11.225.121"#"168.11.248.214"
        ip_config['port'] = 22
        ip_config['username'] = "appadmin"
        ip_config['password'] = decrypt(ENCRYPTED_HOSTS['xtrade']['prd']['ciphertext'])
        ip_config['root_path'] = "/"
    if os.path.isdir(copy_path):
        src = dst = copy_path
    else:
        fname,fename=os.path.split(copy_path)
        dst = fname
        src = copy_path
    _genDirFileMd5(src)
    _copy2server(src, dst, md5_check=md5_check, ip_config=ip_config)


@statisticLog('xqutils', "utils")
def copy2sim(src, dst):
    """
    拷贝文件到UAT
    :param src:源目录或文件
    :param dst:目标目录或文件
    :param md5_check:是否进行MD5校验
    :return:
    """
    if not _uat_limit_time():
        raise Exception("交易日早上9点-16点禁止调用")
    try:
        file_path = path.join(path.dirname(__file__), "encrypted_copy.json")
        with open(file_path, 'rb') as f:
            ENCRYPTED_HOSTS = json.load(f)
    except Exception as e:
        raise Exception("无法读取加密文件")

    ip_config = {}
    if xquantEnv == 0:
        ip_config['ip'] = "168.63.17.205"
        ip_config['port'] = 22
        ip_config['username'] = "log"
        ip_config['password'] = decrypt(ENCRYPTED_HOSTS['uat']['test']['ciphertext'])
        ip_config['root_path'] = "/home/log/test/"
    else:
        ip_config['ip'] = "168.6.20.204"
        ip_config['port'] = 22
        ip_config['username'] = "appadmin"
        ip_config['password'] = decrypt(ENCRYPTED_HOSTS['uat']['prd']['ciphertext'])
        ip_config['root_path'] = "/bigdata/XTraderModel/UAT/"

    _copy2server(src, dst, md5_check=False, ip_config=ip_config, mode='UAT')


@statisticLog('xqutils', "utils")
def copy2simfree(src, dst):
    """
    拷贝文件到UAT
    :param src:源目录或文件
    :param dst:目标目录或文件
    :param md5_check:是否进行MD5校验
    :return:
    """
    if not _uat_limit_time():
        raise Exception("交易日早上9点-16点禁止调用")
    try:
        file_path = path.join(path.dirname(__file__), "encrypted_copy.json")
        with open(file_path, 'rb') as f:
            ENCRYPTED_HOSTS = json.load(f)
    except Exception as e:
        raise Exception("无法读取加密文件")

    ip_config = {}
    if not os.path.isabs(dst):
        raise Exception("dst目标路径必须为绝对路径！")
    root_path, dst = os.path.split(dst)

    if xquantEnv == 0:
        ip_config['ip'] = "168.63.17.205"
        ip_config['port'] = 22
        ip_config['username'] = "log"
        ip_config['password'] = decrypt(ENCRYPTED_HOSTS['uat']['test']['ciphertext'])
        ip_config['root_path'] = root_path
    else:
        ip_config['ip'] = "168.6.20.204"
        ip_config['port'] = 22
        ip_config['username'] = "appadmin"
        ip_config['password'] = decrypt(ENCRYPTED_HOSTS['uat']['prd']['ciphertext'])
        ip_config['root_path'] = root_path

    _copy2server(src, dst, md5_check=False, ip_config=ip_config, mode='UAT')


@statisticLog('xqutils', "utils")
def deleteFromSim(dst):
    """
    删除UAT文件
    :param dst:目标目录或文件
    :return:
    """
    if not _uat_limit_time():
        raise Exception("交易日早上9点-16点禁止调用")
    try:
        file_path = path.join(path.dirname(__file__), "encrypted_copy.json")
        with open(file_path, 'rb') as f:
            ENCRYPTED_HOSTS = json.load(f)
    except Exception as e:
        raise Exception("无法读取加密文件")

    ip_config = {}
    if xquantEnv == 0:
        ip_config['ip'] = "168.63.17.205"
        ip_config['port'] = 22
        ip_config['username'] = "log"
        ip_config['password'] = decrypt(ENCRYPTED_HOSTS['uat']['test']['ciphertext'])
        ip_config['root_path'] = "/home/log/test/"
    else:
        ip_config['ip'] = "168.6.20.204"
        ip_config['port'] = 22
        ip_config['username'] = "appadmin"
        ip_config['password'] = decrypt(ENCRYPTED_HOSTS['uat']['prd']['ciphertext'])
        ip_config['root_path'] = "/bigdata/XTraderModel/UAT/"
    _deleteFromServer(dst, ip_config=ip_config)


def _copy2server(src, dst, md5_check=False, ip_config=None, mode='XTrader'):
    """
    从源目录拷入文件或目录到目标目录
    :param src:源目录或文件
    :param dst:目标目录或文件
    :return:
    """
    warnings.filterwarnings("ignore")
    dst = repr(dst)[1: -1]
    if "\\" in dst:
        raise Exception("【dst】参数的路径分隔符请用'/'（斜杠）！")
    tran = paramiko.Transport(ip_config['ip'], ip_config['port'])
    tran.connect(username=ip_config['username'], password=ip_config['password'])
    sftp = paramiko.SFTPClient.from_transport(tran)
    _root_dst = Path(ip_config['root_path'])
    if dst and dst[0] == "/":
        dst = dst[1:]
    if src and src[-1] == "/":
        src = src[0:-1]
    file_prefix = os.path.split(dst)[0]
    dst_path = os.path.join(_root_dst, dst)

    if mode == 'UAT':
        tmp = datetime.today().strftime('%Y%m%d%H%M%s') + str(threading.currentThread().ident)
        tmp_md5 = hashlib.md5(tmp.encode('utf-8')).hexdigest()
        tmp_dir = 'tmp-' + tmp_md5
        tmp_path = os.path.join('/tmp', tmp_dir)

        try:
            if os.path.isfile(src):
                os.mkdir(tmp_path)
                shutil.copy2(src, tmp_path)
                src = tmp_path
            elif os.path.isdir(src):
                tmp_dir = os.path.join(tmp_path, os.path.split(src)[1])
                shutil.copytree(src, tmp_dir)
                src = tmp_dir
            else:
                raise Exception("【src】参数为文件或文件夹，请重新输入！")
        except Exception as e:
            raise Exception("拷贝失败：%s" % e)

        _genDirFileMd5(src)

    if os.path.isfile(src):
        path_list = dst.split('/')
        _upload_file(sftp, src, dst_path, _root_dst, path_list=path_list, md5_check=md5_check)
    elif os.path.isdir(src):
        _upload_dir(sftp, src, dst_path, _root_dst, file_prefix, md5_check)
    else:
        raise Exception("【src】参数为文件或文件夹，请重新输入！")

    if mode == 'UAT':
        shutil.rmtree(tmp_path)

    tran.close()


def _deleteFromServer(dst, ip_config=None):
    """
    删除指定目录或文件
    :param dst:目标目录或文件
    :return:
    """
    warnings.filterwarnings("ignore")
    dst = repr(dst)[1: -1]
    if "\\" in dst:
        raise Exception("【dst】参数的路径分隔符请用'/'（斜杠）！")
    tran = paramiko.Transport(ip_config['ip'], ip_config['port'])
    tran.connect(username=ip_config['username'],
                 password=ip_config['password'])
    sftp = paramiko.SFTPClient.from_transport(tran)
    _root_dst = Path(ip_config['root_path'])
    if dst and dst[0] == "/":
        dst = dst[1:]
    dst_path = os.path.join(_root_dst, dst)
    if not _exists(sftp, dst_path):
        raise Exception("路径{}不存在".format(dst_path))

    print('Warning: 正在删除文件{}...'.format(dst_path))
    # 判断是否为文件
    if _is_dir(sftp, dst_path):
        _delete_dir(sftp, dst_path)
    else:
        _delete_file(sftp, dst_path)
    tran.close()


def _is_dir(sftp, dst):
    fileattr = sftp.lstat(dst)
    if stat.S_ISDIR(fileattr.st_mode):
        return True
    return False


def _upload_dir(sftp, dir, remote_dir, root_dst, file_prefix=None, md5_check=False):
    if file_prefix:
        folder_list = file_prefix.split('/')
        dst = root_dst
        for folder in folder_list:
            dst = os.path.join(dst, folder)
            if not _exists(sftp, dst):
                sftp.mkdir(dst)
    if not _exists(sftp, remote_dir):
        sftp.mkdir(remote_dir)
    paths = os.listdir(dir)
    for p in paths:
        dst = os.path.join(remote_dir, p)
        p = os.path.join(dir, p)
        if os.path.isdir(p):
            _upload_dir(sftp, p, dst, root_dst, md5_check=md5_check)
        else:
            _upload_file(sftp, p, dst, root_dst, md5_check=md5_check)
    return True


def _upload_file(sftp, file, dst_path, root_dst, file_prefix=None, path_list=[], md5_check=False):
    if len(path_list) > 1 or (len(path_list) == 1 and path_list[0] != ''):
        dst = root_dst
        for dir in path_list:
            dst = os.path.join(dst, dir)
            if not _exists(sftp, dst):
                sftp.mkdir(dst)
    if file_prefix:
        dir_list = file_prefix.split('/')
        dst = root_dst
        for dir in dir_list:
            dst = os.path.join(dst, dir)
            if not _exists(sftp, dst):
                sftp.mkdir(dst)
    if len(path_list) > 0:
        file_name = os.path.split(file)[-1]
        remote_file = os.path.join(dst_path, file_name)
    else:
        remote_file = dst_path
    try:
        sftp.put(file, remote_file)
        if md5_check:
            with sftp.open(remote_file, 'r') as f_remote:
                content_remote = f_remote.read()
            md5_remote = hashlib.md5(content_remote).hexdigest()
            with open(file, 'rb') as f_local:
                content_local = f_local.read()
            md5_local = hashlib.md5(content_local).hexdigest()
            if md5_local == md5_remote:
                return True
            else:
                raise Exception('MD5校验失败，请重新上传！')
        return True
    except Exception as e:
        raise Exception("文件上传失败：%s" % e)


def _delete_file(sftp, dst_path):
    try:
        sftp.remove(dst_path)
        print('文件{}删除成功'.format(dst_path))
        return True
    except Exception as e:
        raise Exception("文件删除失败：%s" % e)


def _delete_dir(sftp, dst_path):
    try:
        files = sftp.listdir(dst_path)
        for file in files:
            file_path = os.path.join(dst_path, file)
            if _is_dir(sftp, file_path):
                _delete_dir(sftp, file_path)
            else:
                sftp.remove(file_path)
        sftp.rmdir(dst_path)
        print('文件夹{}删除成功'.format(dst_path))
        return True
    except Exception as e:
        raise Exception("文件夹删除失败：%s" % e)


def _exists(sftp, dir):
    status = None
    try:
        status = sftp.stat(dir)
    except:
        pass
    if status:
        return True
    else:
        return False

def _genDirFileMd5(src):
    if os.path.isfile(src):
        if not src.endswith('md5'):
            (status, msg) = getstatusoutput("md5sum -b %s | awk '{print $1}' > %s.md5" % (src.__str__(), src.__str__()))
            # (status, msg) = getstatusoutput("md5sum -b %s " % (src.__str__()))
            if not status == 0:
                raise SystemError(
                    "[errno:%s] genDirFileMd5 md5sum error %s" % (errno.EFAULT, msg)
                )
        return
    paths = os.listdir(src)
    for p in paths:
        _genDirFileMd5(os.path.join(src, p))
