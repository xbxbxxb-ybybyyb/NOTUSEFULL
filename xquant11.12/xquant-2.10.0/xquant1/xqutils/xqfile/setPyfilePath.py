import argparse
import os
import sys
from xquant1.setXquantEnv import xquantEnv,testEnv
from xquant1.utils.utils import *

class SystemException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

__xquant_config_dict = get_xquantConfig()


# HDFS设置项===================================================>>
os.environ['ARROW_LIBHDFS_DIR'] = '/opt/cloudera/parcels/CDH/lib64'
os.environ['HADOOP_CONF_DIR'] = '/etc/hadoop/conf'
os.environ['HADOOP_USER_NAME'] = 'xquant'

# HDFS根路径
if xquantEnv == 0:
    if testEnv == 40:
        prepath_hdfs = "/user/gaoshixiang1/"
    elif testEnv == 63:
        prepath_hdfs = "/user/gaoshixiang1/"
elif xquantEnv == 1:
    prepath_hdfs = "/analysis/xquant/"
else:
    raise Exception("perpath_hdfs 配置错误！")

# 用户HDFS根路径
prepath = prepath_hdfs
# parser = argparse.ArgumentParser()
# parser.add_argument("-u", "--user", help="get user name")
# parser.add_argument("-j", "--jobid", help="get job id")
# parser.add_argument("-t", "--run-type", help="get run type")
# __args = parser.parse_args()
try:
    user = __xquant_config_dict.get("userAccount")
except:
    user = ""
if user:
    if not os.environ.get('BIG_DATA_PREPATH',False) or os.environ.get('ENV_VERSION',False):
        prepath = prepath + user + "/"
else:
    raise SystemException("xquant system lack user name")
# HDFS设置项结束<<===============================

#NFS设置项
if os.environ.get("IS_DOCKER",False):
    nfspathRoot = "/data/"
    nfspath = "/data/"
else:
    nfspathRoot = "/app/data/"
    nfspath = nfspathRoot + user + "/"

# Local设置项
localpath = os.path.abspath("")

# FTP设置项===================================>>
# 新的
if xquantEnv ==0:
    _ftpEnv = {"url": "168.8.2.60", "port": 21, "username": "htzq", "password": "htzq", "dir": "/002609/"}
elif xquantEnv == 1:
    _ftpEnv = {"url": "168.8.2.68", "port": 21, "username": "xquant", "password": "Xquant-32", "dir": "/XQuant/"}
else:
    raise Exception("_ftpEnv 配置错误！")
_tmpName = ".tmp_"
# FTP设置项结束<<================================


# 用于传入共享列表
__share_folders = []
# 用于快速读取共享列表   key = rootId
__share_foldersDict = {}

def set_xquant_entry(share_folders):
    __set_xquant_entry(__xquant_config_dict)

def __set_xquant_entry(share_folders):
    """
    初始化传入共享权限
    :param share_folders:
    :return:
    """
    share_folders = share_folders["shareDirList"]
    for __sf in share_folders:
        __sf["root"] = "$" + str(__sf["orgId"])
        __share_folders.append(__sf)
        __share_foldersDict[__sf["orgId"]] = __sf

def _get_xquant_entry():
    """
    获取共享列表
    :return:
    """
    return __share_folders

def _get_xquant_entryById(rootId):
    """
    根据rootId获取共享项
    :param rootId:
    :return:
    """
    try:
        return __share_foldersDict[int(rootId)]
    # except KeyError as err:
    except :
        return None