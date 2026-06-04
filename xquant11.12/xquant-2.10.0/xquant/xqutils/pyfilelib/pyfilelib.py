import os
import shutil
import pandas as pd
from xquant.utils import statisticLog
from xquant.pyfile import setPyfilePath
# from .setPyfilePath import *
from xquant.pyfile.setPyfilePath import *
# from .setPyfilePath import _get_xquant_entry, _get_xquant_entryById, prepath
from xquant.pyfile.setPyfilePath import _get_xquant_entry,SystemException
from .hdfsfile import *
_noParmission = "Permission Denied"

if not setPyfilePath.__share_folders:
    setPyfilePath.set_xquant_entry(setPyfilePath.__share_folders)
    setPyfilePath.nfspathRoot = "/data/"
    setPyfilePath.nfspath = "/data/"
pyfile_share_folders = setPyfilePath.__share_folders

class Pyfile():
    @statisticLog("xqutils","pyfilelib")
    def __init__(self):
        self.hf = Hdfsfile()

    def __is_Admin(self, path):
        '''
        判断该用户对于该路径是否是管理员身份
        :param path:绝对路径
        :return:True/False
        '''
        if path[0] == "$":
            path = path[1:]
        id = self.__getShareRootId(path)
        admin_list = []
        for sf in self.getShareFoldersConf():
            if sf.get("orgType") == "team" or sf.get("orgType") == "department":
                if sf.get("isAdmin"):
                    admin_list.append(str(sf.get("orgId")))
        if id in admin_list:
            return True
        return False

    def __converShareDir(self, relapath):
        '''
        转换共享地址,如把原 团队标识符 转换成 SHARE_12345
        :param relapath: 用户传入的相对路径
        :return:返回转换后的路径
        '''
        # modify
        if not re.match(r'\$(\d+)/',relapath):
            return relapath
        if relapath[0] == "$":
            search = re.search(r'\$(\d+)', relapath)
            rootId = search.group(1)
            result = "SHARE_" + rootId + relapath[relapath.find("$" + rootId) + len(rootId) + 1:]
            return result

    @statisticLog("xqutils", "pyfilelib")
    def abspath(self,path,Absolute=False):
        """
        返回PATH的绝对路径
        :param path: 用户传入的路径
        :param Absolute: 管理员专用，若为True则传入"$/"开头的绝对路径
        :return:
        参数详解 path：传入路径的打头标识约定
        +----------------+-----------+-------------------------+---------------------------------------------------------------+
        | 文件系统      | 目录类别  | 用户约定传入方式        |  映射的全路径                                                  |
        +==============+===============+==========================+============================================================+
        |              |  个人目录    |   $/ModelSaved/         |  /analysis/xquant/工号/ModelSaved                            |
        |    HDFS      +-----------+-------------------------+---------------------------------------------------------------+
        |              |  团队目录    |   $团队标识/ModelSaved  |  /analysis/xquant/SHARE_团队标识/ModelSaved                 |
        +--------------+-----------+-------------------------+---------------------------------------------------------------+
        |              |  绝对路径    |   /data/ModelSaved       |  /data/ModelSaved                                            |
        +    LOCAL     +-----------+-------------------------+---------------------------------------------------------------+
        |              |  相对路径    |   ModelSaved            |  执行目录+ModelSaved                       |
        +--------------+-----------+-------------------------+---------------------------------------------------------------+
        """
        if Absolute:
            if self.__is_Admin(path):
                admin_abspath = self.__abspath(path, Absolute)
                if admin_abspath[0] == '$':
                    return admin_abspath[1:]
                else:
                    return admin_abspath
            else:
                raise Exception("Enter the agreed header logo and relative path! Set Ablolute to False")
        else:
            if path[:2] == "$/" or re.match(r'\$(\d+)/',path):
                return self.__abspath(path,Absolute)[1:]
            else:
                return self.__abspath(path,Absolute)


    def __abspath(self,path,Absolute=False):
        '''
        内部调用，返回的路径带有打头标识，可以判定是否是hdfs
        :param path: 用户传入的路径
        :param Absolute: 若为True则传入HDFS的绝对路径
        :return: 带有标识的全路径
        '''
        if Absolute:
            if self.__is_Admin(path):
                if self.__isHDFS(path):
                    if self.hf.exists(path):
                        return path
                    else:
                        raise Exception("The input path does not exist!")
                elif path[:1] == "/":
                    if os.path.exists(path):
                        return path
                    else:
                        raise Exception("The input path does not exist!")
                else:
                    raise Exception("Absolute is True, please enter the absolute path")
            else:
                raise Exception("Enter the agreed header logo and relative path! Set Ablolute to False!")
        else:
            return self.__concatPath(path)

    def __concatPath(self, path):
        '''
        处理Absolute为False的相对路径
        :param path: 用户传入的路径
        :return: 带有标识的全路径
        '''
        user_path = path
        if path[:2] == "$/":
            _prepath = setPyfilePath.prepath
        elif re.match(r'\$(\d+)/',path):
            path = self.__converShareDir(path)
            _prepath = setPyfilePath.prepath_hdfs
        elif not re.match(r'/',path):
            _prepath = setPyfilePath.localpath
        elif path[0] == "/":
            _prepath = '/'
        else:
            raise SystemException("Please enter the correct path header logo! ")

        if len(path) > 0 and path[0] == '/':
            path = path[1:]
        elif len(path) > 0 and path[:2] == '$/':
            path = path[2:]
        path = os.path.join(_prepath,path)
        if path == '/':
            return path
        if path[-1] == '/':
            path = path[:-1]
        abs_path = os.path.abspath(path)
        if user_path[:2] == "$/" or re.match(r'\$(\d+)/',user_path):
            abs_path = '$' + abs_path
            return abs_path
        else:
            return abs_path

    @statisticLog("xqutils", "pyfilelib")
    def getShareFoldersConf(self):
        """
        获取用户权限下的共享目录列表，列表每一项包含name、type、id、root字段
        :return: 共享目录列表
        """
        #return _get_xquant_entry()
        return pyfile_share_folders

    @statisticLog("xqutils", "pyfilelib")
    def getShareFolders(self, arg):
        """符合条件的共享目录
        :param arg: 共享目录id、type或name
        :return: 返回一个字典，key是HDFS和NFS，value是其符合条件的共享目录列表
        """
        shareFolder_list = {
            "HDFS": [],
            "NFS": []
        }
        for xq in pyfile_share_folders:
            if xq["orgName"].find(str(arg)) >= 0 or \
                    xq["orgType"].find(str(arg)) >= 0 or \
                    (isinstance(arg, int) and xq['orgId'] == arg):
                shareFolder_list["HDFS"].append(xq["root"])
                shareFolder_list["NFS"].append(setPyfilePath.nfspathRoot + "SHARE_" + str(xq["orgId"]))
        return shareFolder_list

    def __check_Dir_Permissions(self, *paths,Absolute=True):
        '''
        判断文件夹操作权限
        :param *paths:绝对路径(可以同时传入多个路径进行判断)
        :return: 有可读权限时返回True，无可读权限时为False
        '''
        for path in paths:
            rootId = self.__getShareRootId(path)
            rootIdlist = self.getTeamInfo().values()
            if not rootId:
                if self.__isHDFS(path):
                    if "/".join(path.split("/")[1:4]) != setPyfilePath.prepath_hdfs[1:] + setPyfilePath.user:
                        return False
            else:
                if int(rootId) not in rootIdlist:
                    return False
        return True

    def __getShareRootId(self, path):
        '''
        从绝对路径中获取用户权限下的rootId
        :param path:绝对路径
        :return: rootid（如无返回空）
        '''
        splitPath_list = path.split("/")
        hdfs_share = setPyfilePath.prepath_hdfs + "SHARE_"
        local_share = setPyfilePath.nfspathRoot+"SHARE_"
        try:
            if hdfs_share in path or local_share in path:
                for splitPath in splitPath_list:
                    if "SHARE_" in splitPath:
                        return splitPath[6:]
            return None
        except:
            return None

    @statisticLog("xqutils", "pyfilelib")
    def getTeamInfo(self):
        '''
        获取用户权限下的团队名称及团队标识
        :return: key是team名称，value是团队标识的字典
        '''
        teamId = {}
        for xq in self.getShareFoldersConf():
            teamId[xq["orgName"]] = xq["orgId"]
        return teamId

    def __isHDFS(self,path):
        '''
        判断绝对路径是否是HDFS上的
        :param path: 绝对路径
        :return: True/False
        '''
        if path[0] == "$":
            return True
        else:
            return False

    def __is_shareForlder(self,path):
        '''
        判断是否是共享文件夹
        :param path:绝对路径
        :return:True/False
        '''
        hdfs_share = setPyfilePath.prepath_hdfs + "SHARE_"
        local_share = setPyfilePath.nfspathRoot+"SHARE_"
        if hdfs_share in path or local_share in path:
            return True
        return False

    @statisticLog("xqutils", "pyfilelib")
    def removedirs(self,path,recursion=False,Absolute=False):
        '''
        在用权限范围内删除文件夹。若文件夹不存在，则报错。支持删除空文件夹。
        :param path:用户传入路径
        :param Absolute: 管理员专用，若为True则传入$/"开头的绝对路径
        :param recursion: 是否递归删除，默认False(不递归)
        :return: 状态(成功返回True)
        '''
        absPath = self.__abspath(path,Absolute)
        if not self.__check_Dir_Permissions(absPath):
            raise SystemException("[errno:%i] removedirs(path = %s) Permission denied" % (errno.EPERM, path))
        if self.__is_Admin(absPath):
            if self.__isHDFS(absPath):
                self.hf.removedirs(absPath[1:],recursion)
            else:
                if not self.exists(path):
                    raise Exception("removedirs failed! The folder does not exist!")
                if os.path.isdir(absPath):
                    if recursion:
                        shutil.rmtree(absPath)
                    else:
                        os.removedirs(absPath)
                else:
                    raise Exception("removedirs failed! The incoming path is not a folder!")
        else:
            if self.__is_shareForlder(absPath):
                raise SystemException("[errno:%i] removedirs(path = %s) Permission denied" % (errno.EPERM, path))
            else:
                if self.__isHDFS(absPath):
                    self.hf.removedirs(absPath[1:],recursion)
                else:
                    if not self.exists(path):
                        raise Exception("removedirs failed! The folder does not exist!")
                    if os.path.isdir(absPath):
                        if recursion:
                            shutil.rmtree(absPath)
                        else:
                            os.removedirs(absPath)
                    else:
                        raise Exception("removedirs failed! The incoming path is not a folder!")
        return True

    @statisticLog("xqutils", "pyfilelib")
    def remove(self,path,Absolute=False):
        '''
        在用权限范围内删除文件，若传入的路径不是文件或者文件不存在，则报错。
        :param path: 用户传入路径
        :param Absolute: 管理员专用，若为True则传入"$/"开头的绝对路径
        :return: 状态(成功返回True)
        '''
        absPath = self.__abspath(path,Absolute)
        if not self.__check_Dir_Permissions(absPath):
            raise SystemException("[errno:%i] remove(path = %s) Permission denied" % (errno.EPERM, path))
        if self.__is_Admin(absPath):
            if self.__isHDFS(absPath):
                self.hf.remove(absPath[1:])
            else:
                if not self.exists(path):
                    raise Exception("remove failed! file do not exist!")
                if os.path.isfile(absPath):
                    os.remove(absPath)
                else:
                    raise Exception("remove failed! The incoming path is not a file!")
        else:
            if self.__is_shareForlder(absPath):
                raise SystemException("[errno:%i] remove(path = %s) Permission denied" % (errno.EPERM, path))
            else:
                if not self.exists(path):
                    raise Exception("remove failed! file do not exist!")
                if self.__isHDFS(absPath):
                    self.hf.remove(absPath[1:])
                else:
                    if os.path.isfile(absPath):
                        os.remove(absPath)
                    else:
                        raise Exception("remove failed! The incoming path is not a file!")
        return True

    def __local_recursion_listdir(self,absPath):
        '''
        递归返回本地目录下所有文件，在listdir中被调用
        :param absPath: 绝对路径
        :return: 文件列表
        '''
        treedir = []
        n = len(absPath)
        for dirpath, dirnames, filenames in os.walk(absPath):
            if dirpath == absPath:
                string = ''
                for f in filenames:
                    string = str(f)
                    treedir.append(string)
            else:
                dirn = dirpath[n:]
                dirn = dirn.strip((os.sep))
                treedir.append(dirn + "/")
                for f in filenames:
                    string = dirn + "/" + str(f)
                    treedir.append(string)
        return treedir

    @statisticLog("xqutils", "pyfilelib")
    def listdir(self,path,recursion=False,Absolute=False):
        '''
        在用户权限范围内返回给定路径path下全部文件名，若路径释文件或者不存在，则报错
        :param path: 路径
        :param Absolute: 管理员专用，若为True则传入"$/"开头的绝对路径
        :param recursion: 是否递归显示，默认False(只显示当前目录下的文件和文件夹)
        :return: 给定路径path下全部文件名列表
        '''
        absPath = self.__abspath(path,Absolute)
        if not self.__check_Dir_Permissions(absPath):
            raise SystemException("[errno:%i] listdir(path = %s) Permission denied" % (errno.EPERM, path))
        if not self.exists(path):
            raise Exception("No such file or directory:%s"%(path))
        if self.__isHDFS(absPath):
            if self.hf.isFile(absPath[1:]):
                raise Exception("The directory name is invalid:",path)
            if not recursion:
                return self.hf.listdir(absPath[1:])
            else:
                return self.hf.getdirtree(absPath[1:])
        else:
            if os.path.isfile(absPath):
                raise Exception("The directory name is invalid:",path)
            if not recursion:
                return os.listdir(absPath)
            else:
                return self.__local_recursion_listdir(absPath)

    @statisticLog("xqutils", "pyfilelib")
    def get_file_status(self,path,Absolute=False):
        '''
        在用户权限下返回给定路径下文件夹下或文件的状态信息
        :param path: 用户传入路径
        :param Absolute: 管理员专用，若为True则传入"$/"开头的绝对路径
        :return: 给定路径下文件夹下或文件的状态信息
        '''
        absPath = self.__abspath(path, Absolute)
        if not self.__check_Dir_Permissions(absPath):
            raise SystemException("[errno:%i] get_file_status(path = %s) Permission denied" % (errno.EPERM, path))
        if self.__isHDFS(absPath):
            return self.hf.list_status(absPath[1:])
        else:
            if os.path.isfile(absPath):
                path_ = absPath
                file_status = os.stat(path_)
                result = {}
                result['name'] = path_[path_.rindex('/') + 1:]
                result['size'] = file_status.st_size
                result['last_modified'] = file_status.st_mtime
                result['last_accessed'] = file_status.st_atime
                result['kind'] = "file"
                return [result]
            elif os.path.isdir(absPath):
                rootPath = absPath + "/"
                dir_list = self.listdir(path)
                result = []
                for dir in dir_list:
                    path_ = rootPath + dir
                    file_status = os.stat(path_)
                    item = {}
                    item['name'] = dir
                    item['size'] = file_status.st_size
                    item['last_modified'] = file_status.st_mtime
                    item['last_accessed'] = file_status.st_atime
                    item['kind'] = "file"
                    result.append(item)
                return result

    def __local_open(self,path,mode):
        '''
        本地文件操作
        :param path:绝对路径
        :param mode: 打开文件的模式
        :return: 本地文件操作对象
        '''
        f = open(path,mode)
        return  f

    @statisticLog("xqutils", "pyfilelib")
    def open(self,path,mode="rb",Absolute=False):
        '''
        在用户权限下访问文件，返回文件操作对象
        :param path: 用户传入路径
        :param Absolute: 管理员专用，若为True则传入"$/"开头的绝对路径
        :param mode: 打开文件的模式
        :return: 文件操作对象
        '''
        absPath = self.__abspath(path, Absolute)
        if not self.__check_Dir_Permissions(absPath):
            raise SystemException("[errno:%i] open(path = %s) Permission denied" % (errno.EPERM, path))
        if not self.__is_Admin(absPath):
            if mode.strip().find("w") >= 0 or mode.strip().find("a") >= 0:  # 共享目录禁止写入和追加
                if self.__is_shareForlder(absPath):
                    if self.exists(path):
                        raise SystemException("Unable to open file: Permission denied!")
        if absPath[:-1] == "/":
            _absPath = absPath[1:]
        (fp, fn) = os.path.split(absPath)
        if not self.exists(fp):
            self.mkdir(fp)
        if self.__isHDFS(absPath):
            return self.hf.open(absPath[1:],mode)
        else:
            return self.__local_open(absPath,mode)

    @statisticLog("xqutils", "pyfilelib")
    def mkdir(self,path,Absolute=False):
        """
        创建文件夹，根据传入路径打头标识可在HDFS、NFS、Local创建文件夹
        :param path:用户传入路径
        :param Absolute: 管理员专用，若为True则传入"$/"开头的绝对路径
        :return:
        参数详解 path：传入路径的打头标识约定
        """
        _absPath = self.__abspath(path, Absolute)
        if not self.__check_Dir_Permissions(_absPath):
            raise SystemException("[errno:%i] mkdir(path = %s) Permission denied" % (errno.EPERM, path))
        if self.__isHDFS(_absPath):
            absPath = _absPath[1:]
            if not self.exists(path):
                self.hf.mkdir(absPath)
            else:
                raise Exception("Directory already exists! Failed to create HDFS folder!")
        else:
            if not self.exists(path):
                os.makedirs(_absPath)
            else:
                raise Exception("Directory already exists! Failed to create local folder!")
        return True

    @statisticLog("xqutils", "pyfilelib")
    def exists(self,path,Absolute=False):
        """
        查看文件或文件夹是否存在
        :param path: 用户传入路径
        :param Absolute: 管理员专用，若为True则传入"$/"开头的绝对路径
        :return: True/False
        """
        _absPath = self.__abspath(path,Absolute)
        if not self.__check_Dir_Permissions(_absPath):
            raise SystemException("[errno:%i] exists(path = %s) Permission denied" % (errno.EPERM, path))
        if self.__isHDFS(_absPath):
            absPath = _absPath[1:]
            return self.hf.exists(absPath)
        else:
            return os.path.exists(_absPath)

    @statisticLog("xqutils", "pyfilelib")
    def createFile(self,path,overwrite=False,Absolute=False):
        """
        创建文件，根据传入路径打头标识可在HDFS、NFS、Local创建文件
        :param path: 路径打头标识
        :param overwrite: 若文件已存在是否覆盖，默认False
        :param Absolute: 管理员专用，若为True则传入"$/"开头的绝对路径
        :return:True/False
        """
        _absPath = self.__abspath(path, Absolute)
        if not self.__check_Dir_Permissions(_absPath):
            raise SystemException("[errno:%i] createFile(path = %s) Permission denied" % (errno.EPERM, path))
        if self.__isHDFS(_absPath):
            absPath = _absPath[1:]
            self.hf.create(absPath,overwrite)
        else:
            if _absPath[:-1] == "/":
                _absPath = _absPath[1:]
            (fp,fn) = os.path.split(_absPath)
            if not os.path.exists(fp):
                os.makedirs(fp)
            if self.exists(path):
                if overwrite:
                    with open(_absPath, "wb") as file:
                        pass
                    return True
                raise Exception("Failed to create file! The file already exists!")
            else:
                with open(_absPath, "wb") as file:
                    pass
        return True

    def __local_copy(self,_srcAbsolutePath,_dstAbsolutePath,):
        '''
        本地文件或文件夹复制，在cp中被调用
        :param _dstAbsolutePath: 目标路径
        :param _srcAbsolutePath: 源路径
        :return:
        '''
        (src_fp, src_fn) = os.path.split(_srcAbsolutePath)
        if not os.path.exists(_srcAbsolutePath):
            raise SystemException("%s failed! The %s file or folder does not exist!")
        try:
            if os.path.isfile(_dstAbsolutePath):
                raise IOError("%s failed! The %s file already exists!")
        except:
            pass
        isFile = os.path.isfile(_srcAbsolutePath)
        if isFile:
            shutil.copy(_srcAbsolutePath, _dstAbsolutePath)
            return True
        else:
            _dstAbsolutePath += "/" + src_fn
            shutil.copytree(_srcAbsolutePath,_dstAbsolutePath)

    def __path_inclusion(self,src,dst):
        '''
        判断目标文件是否包含原文件
        :param src:原路径
        :param dst:目标路径
        :return:True/False
        '''
        if dst.find(src) == 0 :
            return True
        return False

    @statisticLog("xqutils", "pyfilelib")
    def cp(self,source,target,Absolute=False):
        '''
        在用户权限范围内，复制文件或文件夹，若目标路径父文件夹不存在，则创建。
        若复制文件，源路径是文件，目标路径是文件或者文件夹
        若复制文件夹，源路径是文件夹，目标路径是文件夹。
        不支持强制复制，不会覆盖目标路径中的原有文件。
        :param source: 源路径
        :param target: 目标路径
        :param Absolute:管理员专用，若为True则传入为"$/"或"$/"开头的绝对路径
        :return:
        '''
        _targetAbsolutePath = self.__abspath(target, Absolute)
        _sourceAbsolutePath = self.__abspath(source, Absolute)
        if _targetAbsolutePath[-1] == "/":
            _targetAbsolutePath = _targetAbsolutePath[:-1]
        if _sourceAbsolutePath[-1] == "/":
            _sourceAbsolutePath = _sourceAbsolutePath[:-1]
        if not self.__check_Dir_Permissions(_targetAbsolutePath, _sourceAbsolutePath):
            raise SystemException("[errno:%i] cp(path = %s) Permission denied" % (errno.EPERM,source))
        if self.__path_inclusion(_sourceAbsolutePath,_targetAbsolutePath):
            raise Exception("The target path cannot contain the original path!")
        try:
            self.__copy(_sourceAbsolutePath,_targetAbsolutePath)
        except Exception as e:
            if "%s" in str(e):
                err_msg = str(e)%("copy","copy")
                raise Exception(err_msg)
            else:
                raise
        return True

    def __copy(self,_sourceAbsolutePath,_targetAbsolutePath,):
        '''
        复制功能，cp中被调用
        :param _sourceAbsolutePath: 源路径
        :param _targetAbsolutePath: 目标路径
        :return:
        '''
        if self.__isHDFS(_targetAbsolutePath) and self.__isHDFS(_sourceAbsolutePath):
            if self.__is_shareForlder(_targetAbsolutePath):
                #hdfs个人到共享
                self.hf.copyToShare(_targetAbsolutePath[1:],_sourceAbsolutePath[1:])
            elif self.__is_shareForlder(_sourceAbsolutePath):
                #hdfs共享到个人
                self.hf.copyFromShare(_targetAbsolutePath[1:],_sourceAbsolutePath[1:])
            else:
                #hdfs其他
                self.hf.personal_copy(_targetAbsolutePath[1:], _sourceAbsolutePath[1:])
        elif not self.__isHDFS(_targetAbsolutePath) and self.__isHDFS(_sourceAbsolutePath):
            #hdfs到本地
            self.hf.download(_sourceAbsolutePath[1:],_targetAbsolutePath)
        elif self.__isHDFS(_targetAbsolutePath) and not self.__isHDFS(_sourceAbsolutePath):
            #本地到hdfs
            self.hf.upload(_targetAbsolutePath[1:],_sourceAbsolutePath)
        elif not self.__isHDFS(_targetAbsolutePath) and not self.__isHDFS(_sourceAbsolutePath):
            # 本地到本地
            self.__local_copy(_sourceAbsolutePath,_targetAbsolutePath)

    @statisticLog("xqutils", "pyfilelib")
    def mv(self,source,target,Absolute=False):
        '''
        在用户权限范围内对文件或文件夹移动（剪切）。
        若移动文件，源路径是文件，目标路径是文件或者文件夹
        若移动文件夹，源路径是文件夹，目标路径是文件夹。
        不支持强制移动，不会覆盖目标路径中的原有文件。
        :param source:源路径
        :param target: 目标路径
        :param Absolute: 管理员专用，若为True则传入"$/"开头的绝对路径
        :return: True/False
        '''
        # rename,upload,download,copy
        _targetAbsolutePath = self.__abspath(target, Absolute)
        _sourceAbsolutePath = self.__abspath(source, Absolute)
        if _targetAbsolutePath[-1] == "/":
            _targetAbsolutePath = _targetAbsolutePath[:-1]
        if _sourceAbsolutePath[-1] == "/":
            _sourceAbsolutePath = _sourceAbsolutePath[:-1]
        if not self.__check_Dir_Permissions(_targetAbsolutePath, _sourceAbsolutePath):
            raise SystemException("[errno:%i] mv(path = %s) Permission denied" % (errno.EPERM,source))
        if not self.__is_Admin(_sourceAbsolutePath) and self.__is_shareForlder(_sourceAbsolutePath):
            raise SystemException("[errno:%i] mv Permission denied" % (errno.EPERM))
        if self.__path_inclusion(_sourceAbsolutePath,_targetAbsolutePath):
            raise Exception("The target path cannot contain the original path")
        try:
            self.__copy(_sourceAbsolutePath,_targetAbsolutePath)
        except Exception as e:
            if "%s" in str(e):
                err_msg = str(e)%("move","move")
                raise Exception(err_msg)
            else:
                raise
        if self.__isHDFS(_sourceAbsolutePath):
            if self.hf.isFile(_sourceAbsolutePath[1:]):
                self.hf.remove(_sourceAbsolutePath[1:])
            else:
                self.hf.removedirs(_sourceAbsolutePath[1:],recursion=True)
        else:
            if os.path.isfile(_sourceAbsolutePath):
                os.remove(_sourceAbsolutePath)
            else:
                shutil.rmtree(_sourceAbsolutePath)
        return True

    @statisticLog("xqutils", "pyfilelib")
    def read_csvfile(self, path, head=True,Absolute=False):
        '''
        读取csv文件，返回 pandas.DataFrame
        :param path: 用户传入的路径
        :param head: head=True: 若第一列是DataFrame的列，head为True,否则为false, 默认为True
        :param Absolute: 管理员专用，若为True则传入"$/"开头的绝对路径
        :return: pandas.DataFrame
        '''
        abspath = self.__abspath(path,Absolute)
        if not self.__check_Dir_Permissions(abspath):
            raise SystemException("[errno:%i] read_csvfile(path = %s) Permission denied" % (errno.EPERM,abspath))
        if self.__isHDFS(abspath):
            return self.hf.read_csvfile(abspath[1:],head)
        else:
            return pd.read_csv(abspath,index_col=0)

    @statisticLog("xqutils", "pyfilelib")
    def write_csvfile(self,path,df,Absolute=False):
        '''
        写csv文件，传入的数据 DataFrame
        :param path: 用户出入路径
        :param df: dataframe
        :param Absolute: 管理员专用，若为True则传入"$/"开头的绝对路径
        :return: True/False
        '''
        abspath = self.__abspath(path, Absolute)
        if not self.__check_Dir_Permissions(abspath):
            raise SystemException("[errno:%i] write_csvfile(path = %s) Permission denied" % (errno.EPERM, abspath))
        if not self.__is_Admin(abspath):
            if self.__is_shareForlder(abspath):# 共享目录禁止写入和追加
                if self.exists(path):
                    raise SystemException("Unable to write_csvfile: Permission denied!")
        if self.__isHDFS(abspath):
            self.hf.write_csvfile(abspath[1:],df)
        else:
            df.to_csv(abspath)
        return True









