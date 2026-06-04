import errno
import builtins
import os
import time
import psutil

from .new_os import _redirect_os
from .new_shutil import _redirect_shutil
# 内部变量
from .utils import _init_args, _check_Dir_Permissions, _open_mode_limit, _noParmission

import io

__has_sandbox = False
__open = builtins.open
__ioOpen =  io.open

def has_sandbox():
    """
    返回沙箱是否已经预处理
    :return:
    """
    global __has_sandbox
    return __has_sandbox

def func(seq):
    print(seq, os.sched_getaffinity(psutil.Process().pid))
    while True:
        # print(seq, time.time())
        # time.sleep(1)
        pass

def init_sandbox():
    """
    初始化沙箱
    :return:
    """
    global __has_sandbox
    # CPU限制
    cpus = os.cpu_count()
    cpu_start = int(cpus * 0.25)
    if cpu_start > 4:
        cpu_start = 4
    cpu_mask = set()
    for i in range(cpu_start, cpus):
        cpu_mask.add(i)
    os.sched_setaffinity(0, cpu_mask)
    
    _init_args()
    # 重定向open
    builtins.open = new_open
    io.open = new_ioOpen
    # builtins.exec = new_exec
    # builtins.eval = new_exec
    # builtins.compile = new_exec
    _redirect_os()
    _redirect_shutil()
    __has_sandbox = True

def __local_recursion_listdir(absPath):
    '''
    递归调出共享文件夹里面的所有文件
    :param absPath: 路径
    :return: 文件列表
    '''
    rootpath = absPath[absPath.rindex("/")+1:] + "/"
    treedir = []
    n = len(absPath)
    for dirpath, dirnames, filenames in os.walk(absPath):
        if dirpath == absPath:
            string = ''
            for f in filenames:
                string = str(f)
                treedir.append(rootpath + string)
        else:
            dirn = dirpath[n:]
            dirn = dirn.strip((os.sep))
            treedir.append(rootpath + dirn + "/")
            for f in filenames:
                string = dirn + "/" + str(f)
                treedir.append(rootpath + string)
    return treedir

def __sharefolder_permission(file):
    # modify
    from xquant1.pyfile import setPyfilePath
    shareDirList = setPyfilePath.__xquant_config_dict.get('shareDirList')
    orgIdList = []
    share_folders = []
    readable_file = []
    for shareDir in shareDirList:
        if not shareDir.get("isAdmin", False):
            orgId = shareDir['orgId']
            orgIdList.append(orgId)
    for orgId in orgIdList:
        share_folders.append("/app/data/SHARE_" + str(orgId))
        share_folders.append("/data/SHARE_" + str(orgId))
    for folders in share_folders:
        try:
            readable_file += __local_recursion_listdir(folders)
        except:
            pass
    _fn = ""
    if "app/data/SHARE_" in file:
        for _pn in file.split("/"):
            if "SHARE_" in _pn:
                _fn = "/".join(file.split("/")[file.split("/").index(_pn):])
    (fp, fn) = os.path.split(file)
    fullpath = os.path.abspath(fp) + '/'
    for opDir in share_folders:
        if fullpath.find(opDir) == 0:
            if not _fn:
                return False
            if _fn not in readable_file:
                return True
            else:
                return False
    return False

def new_open(file, mode='r', buffering=1, encoding=None, errors=None, newline=None, closefd=True):
    for s in mode:
        if s.lower() in _open_mode_limit:
            if not _check_Dir_Permissions(file):
                if __sharefolder_permission(file):
                    break
                else:
                    raise IOError("[Errno %i]:%s" % (errno.EPERM, _noParmission))
            else:
                break
    return __open(file, mode, buffering, encoding, errors, newline, closefd)

def new_ioOpen(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
    for s in mode:
        if s.lower() in _open_mode_limit:
            if not _check_Dir_Permissions(file):
                if __sharefolder_permission(file):
                    break
                else:
                    raise IOError("[Errno %i]:%s" % (errno.EPERM, _noParmission))
            else:
                break
    return __ioOpen(file,mode,buffering,encoding,errors,newline,closefd,opener)


def new_exec(*args, **kwargs):
    raise IOError("[Errno %i]:%s" % (errno.EPERM, _noParmission))