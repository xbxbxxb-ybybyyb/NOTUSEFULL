import shutil as su
import errno
from .utils import _check_Dir_Permissions, _noParmission

__copy = su.copy
__copy2 = su.copy2
__copyfile = su.copyfile
__rmtree = su.rmtree
__copytree = su.copytree
__move = su.move
__chown = su.chown


def st_copy(src, dst, *, follow_symlinks=True):
    if not _check_Dir_Permissions(dst):
        raise IOError("[errno:%s] copy(dst = %s) %s" % (errno.EPERM, dst, _noParmission))
    return __copy(src, dst, follow_symlinks=follow_symlinks)


def st_copy2(src, dst, *, follow_symlinks=True):
    if not _check_Dir_Permissions(dst):
        raise IOError("[errno:%s] copy2(dst = %s) %s" % (errno.EPERM, dst, _noParmission))
    return __copy2(src, dst, follow_symlinks=follow_symlinks)


def st_copyfile(src, dst, *, follow_symlinks=True):
    if not _check_Dir_Permissions(dst):
        raise IOError("[errno:%s] copyfile(dst = %s) %s" % (errno.EPERM, dst, _noParmission))
    return __copyfile(src, dst, follow_symlinks=follow_symlinks)


def st_rmtree(path, ignore_errors=False, onerror=None):
    if not _check_Dir_Permissions(path):
        raise IOError("[errno:%s] rmtree(path = %s) %s" % (errno.EPERM, path, _noParmission))
    return __rmtree(path, ignore_errors=ignore_errors, onerror=onerror)


def st_copytree(src, dst, symlinks=False, ignore=None, ignore_dangling_symlinks=False):
    if not _check_Dir_Permissions(dst):
        raise IOError("[errno:%s] copytree(dst = %s) %s" % (errno.EPERM, dst, _noParmission))
    return __copytree(src, dst, symlinks=symlinks, ignore=ignore, ignore_dangling_symlinks=ignore_dangling_symlinks)


def st_move(src, dst):
    if not _check_Dir_Permissions(dst):
        raise IOError("[errno:%s] move(dst = %s) %s" % (errno.EPERM, dst, _noParmission))
    return __move(src, dst)


def st_chown(path, user=None, group=None):
    if not _check_Dir_Permissions(path):
        raise IOError("[errno:%s] chown(path = %s) %s" % (errno.EPERM, path, _noParmission))
    return __chown(path, user=user, group=group)


def _redirect_shutil():
    su.copy = st_copy
    su.copy2 = st_copy2
    su.copyfile = st_copyfile
    su.copytree = st_copytree
    su.rmtree = st_rmtree
    su.move = st_move
    su.chown = st_chown