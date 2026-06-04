import os
import subprocess
import errno
from .utils import _check_Dir_Permissions, _noParmission


__makedirs = os.makedirs
__link = os.link
__mkdir = os.mkdir
__open = os.open
__removedirs = os.removedirs
__remove = os.remove
__rmdir = os.rmdir
__renames = os.renames
__rename = os.rename
__system = os.system
__popen = os.popen
__call = subprocess.call
__check_call = subprocess.check_call
__check_output = subprocess.check_output

def os_system(*args, **kwargs):
    raise IOError("[errno:%s]  %s" % (errno.EPERM, _noParmission))

def os_link(*args, **kwargs):
    if not _check_Dir_Permissions(args[1]):
        raise IOError("[errno:%s] link(dst = %s) %s" % (errno.EPERM, args[1], _noParmission))
    __link(*args, **kwargs)

def os_makedirs(*args, **kwargs):
    # if not _check_Dir_Permissions(args[0]):
    #     raise IOError("[errno:%s] makedirs(dst = %s) %s" % (errno.EPERM, args[0], _noParmission))
    return __makedirs(*args, **kwargs)

def os_mkdir(*args, **kwargs):
    # if not _check_Dir_Permissions(args[0]):
    #     raise IOError("[errno:%s] makedirs(dst = %s) %s" % (errno.EPERM, args[0], _noParmission))
    return __mkdir(*args, **kwargs)


def os_open(*args, **kwargs):
    if not _check_Dir_Permissions(args[0]):
        raise IOError("[errno:%s] os.open(path = %s) %s" % (errno.EPERM, args[0], _noParmission))
    return __open(*args, **kwargs)


def os_removedirs(*args, **kwargs):
    if not _check_Dir_Permissions(args[0]):
        raise IOError("[errno:%s] os.removedirs(path = %s) %s" % (errno.EPERM, args[0], _noParmission))
    return __removedirs(*args, **kwargs)



# return __removedirs(name)

def os_remove(*args, **kwargs):
    if not _check_Dir_Permissions(args[0]):
        raise IOError("[errno:%s] os.open(path = %s) %s" % (errno.EPERM, args[0], _noParmission))
    return __remove(*args, **kwargs)


def os_rmdir(*args, **kwargs):
    if not _check_Dir_Permissions(args[0]):
        raise IOError("[errno:%s] os.rmdir(path = %s) %s" % (errno.EPERM, args[0], _noParmission))
    return __rmdir(*args, **kwargs)


def os_renames(old, new):
    if not _check_Dir_Permissions(old):
        raise IOError("[errno:%s] os.renames(old = %s) %s" % (errno.EPERM, old, _noParmission))
    return __renames(old, new)


def os_rename(*args, **kwargs):
    if not _check_Dir_Permissions(args[0]):
        raise IOError("[errno:%s] os.rename(path = %s) %s" % (errno.EPERM, args[0], _noParmission))
    return __rename(*args, **kwargs)


def _redirect_os():
    # os.mkdir = os_mkdir
    os.link = os_link
    os.open = os_open
    os.remove = os_remove
    os.rmdir = os_rmdir
    os.rename = os_rename
    os.renames = os_renames
    os.removedirs = os_removedirs
    os.makedirs = os_makedirs
    # os.system = os_system
    # os.popen = os_system
    # subprocess.call = os_system
    # subprocess.check_call = os_system
    # subprocess.check_output = os_system
