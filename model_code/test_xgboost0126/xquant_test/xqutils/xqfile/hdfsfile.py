import errno
import io
import re
from threading import current_thread
from retrying import retry

import pandas
import pyarrow

from .setPyfilePath import *
from .setPyfilePath import _get_xquant_entry, _get_xquant_entryById, prepath, prepath_hdfs
from xquant.xqutils.utils import statisticLog
import logging
_noParmission = "Permission Denied"

ntfsClientDict = {}
#版本警告
#logging.basicConfig(format="%(levelname)s:%(message)s")
#logging.warning("下一个版本中，pyfile将被弃用，建议使用pyfilelib！详情请参考帮助文档！")

class FileOpt():
    fo = None
    mode = None
    BATCH_SIZE = None

    def __init__(self, fileobject, mode, buff_size):
        self.fo = fileobject
        self.mode = mode
        self.BATCH_SIZE = buff_size

    def __del__(self):
        #print('=====>', self.fo)
        #self.fo.close()
        pass

    def __enter__(self):
        return self
    
    def __exit__(self, type, value, trace):
        self.fo.close()

    def __iter__(self):
        return self

    def next(self):
        line = self.readline()
        if line is None:
            raise StopIteration()
        return line

    def tell(self):
        return self.fo.tell()

    def flush(self):
        pass

    def seek(self, offset, whence=0):
        return self.fo.seek(offset, whence)

    def write(self, b):
        return self.fo.write(b)

    def read(self, size=-1):
        if size < 0:
            size = 0x7fffffff
        return self.fo.read(size)
    
    def readline(self):
        line = b''
        while True:
            bytes = self.fo.read(1)
            if bytes:
                byte = bytes[0]
                if byte == 10:  # '\n'
                    line = line + bytes
                    return line
                else:
                    line = line + bytes
            else:
                if len(line) > 0:
                    return line
                else:
                    return None

    def close(self):
        self.fo.close()


class HDFSFile(object):
    @statisticLog('xqfile', 'HDFSFile')
    def __init__(self,dfs=None):
        if not dfs:
            self._creat_by_own = True
            global ntfsClientDict
            if ntfsClientDict.get(current_thread().ident) is None:
                ntfsClientDict[current_thread().ident] = pyarrow.hdfs.connect()
                ntfsClientDict[str(current_thread().ident) + "_refs"] = 0
            self._client = ntfsClientDict.get(current_thread().ident)
            ntfsClientDict[str(current_thread().ident) + "_refs"] += 1
        else:
            self._creat_by_own = False
            self._client = dfs

    def __del__(self):
        if self._creat_by_own:
            try:
                ntfsClientDict[str(current_thread().ident) + "_refs"] -= 1
                if ntfsClientDict[str(current_thread().ident) + "_refs"] <= 0:
                    del ntfsClientDict[current_thread().ident]
                    del ntfsClientDict[str(current_thread().ident) + "_refs"]
                    self._client.close()
            except:
                import logging
                logging.basicConfig(format="%(levelname)s:%(message)s")
                logging.warning("pyfile __del__ failed!")
                return

    def __check_connect(self):
        try:
            self._client.exists('/')
        except Exception as e:
            global ntfsClientDict
            ntfsClientDict[current_thread().ident] = pyarrow.hdfs.connect()
            ntfsClientDict[str(current_thread().ident) + "_refs"] = 0
            self._client = ntfsClientDict.get(current_thread().ident)
            ntfsClientDict[str(current_thread().ident) + "_refs"] += 1
            self._creat_by_own = True
            raise Exception('hdfs连接创建失败:{}'.format(repr(e)))

    @statisticLog('xqfile', 'HDFSFile')
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def listdir(self, path):
        """
        返回给定路径path下全部文件名

        :param path:
        :return: 返回路径文件列表
        :rtype: list

        """
        if not self.__check_Dir_Permissions(path):
            raise SystemException("[errno:%i] listdir(path = %s) Permission denied" % (errno.EPERM, path))
        abspath = self.getAbsolutePath(path)
        self.__check_connect()
        file_list = self._client.ls(abspath)
        result = []
        for file in file_list:
            result.append(file[file.rindex('/') + 1:])
        return result

    @statisticLog('xqfile', 'HDFSFile')
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def delete(self, path, **kwargs):
        """删除一个文件

        :param path:
        :param recursive: 默认False，如果给定的path是一个目录，且参数值为True,则删除path目录，否则抛出异常。（path给定的是一个文件，请不要设置该参数）
        :return: 如果文件成功删除返回True,否则返回False
        """
        if "$" in path[:2]:
            raise SystemException("[errno:%i] delete(path = %s) Permission denied" % (errno.EPERM, path))
        self.__check_connect()
        return self._client.delete(self.getAbsolutePath(path), **kwargs)

    @statisticLog('xqfile', 'HDFSFile')
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def exists(self, path):
        """判断给定路径下文件是否存在

        :param path:
        :return:  bool
        """
        if not self.__check_Dir_Permissions(path):
            raise SystemException("[errno:%i] exists(path = %s) Permission denied" % (errno.EPERM, path))
        self.__check_connect()
        return self._client.exists(self.getAbsolutePath(path))

    @statisticLog('xqfile', 'HDFSFile')
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def get_file_status(self, path):
        """返回给定路径下文件的状态信息

        :param path:
        :return: Return a dict object, include name, size, last_modified, last_accessed, kind
        """
        if not self.__check_Dir_Permissions(path):
            raise SystemException("[errno:%i] get_file_status(path = %s) Permission denied" % (errno.EPERM, path))
        path = self.getAbsolutePath(path)
        self.__check_connect()
        file_status = self._client.info(path)
        result = {}
        result['name'] = path[path.rindex('/') + 1:]
        result['size'] = file_status.get('size')
        result['last_modified'] = file_status.get('last_modified')
        result['last_accessed'] = file_status.get('last_accessed')
        result['kind'] = file_status.get('kind')
        return result

    @statisticLog('xqfile', 'HDFSFile')
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def list_status(self, path):
        """当给定的path是一个目录时，返回该目录下所有文件的状态信息

        :param path:
        :return: list of dict object, include name, size, last_modified, last_accessed, kind
        """
        if not self.__check_Dir_Permissions(path):
            raise SystemException("[errno:%i] list_status(path = %s) Permission denied" % (errno.EPERM, path))
        add_param = ["size", "list_modified_time", "list_access_time", "kind"]
        result = []
        self.__check_connect()
        for f in self._client.ls(self.getAbsolutePath(path), detail=True):
            item = {}
            item['name'] = f['name'][f['name'].rindex('/') + 1:]
            item['size'] = f.get('size')
            item['last_modified'] = f.get('list_modified_time')
            item['last_accessed'] = f.get('list_access_time')
            item['kind'] = f.get('kind')
            result.append(item)
        return result

    @statisticLog('xqfile', 'HDFSFile')
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def mkdir(self, path):
        """创建一个目录

        :param path:
        :return: 目录成功创建返回True,否则返回false
        """
        if "$" in path[:2]:
            raise SystemException("[errno:%i] mkdir(path = %s) Permission denied" % (errno.EPERM, path))
        try:
            self.__check_connect()
            self._client.mkdir(self.getAbsolutePath(path))
            return True
        except Exception as err:
            return False

    @statisticLog('xqfile', 'HDFSFile')
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def rename(self, path, destination):
        """将文件路径path下文件重命名为destination

        :param path:
        :param destination:

        :return: 重命名成功返回True,否则返回False

        """
        if "$" in path[:2]:
            raise SystemException("[errno:%i] rename(path = %s) Permission denied" % (errno.EPERM, path))
        try:
            self.__check_connect()
            self._client.rename(self.getAbsolutePath(path), self.getAbsolutePath(destination))
            return True
        except Exception as err:
            return False
    
    # def append(self, path, data):  # 注意文件必须存在，追加文件，编码默认为gbk
    #     """对给定目录path下的文件追加内容data
    #
    #     注意文件必须存在，追加文件
    #
    #     """
    #     if isinstance(data, int) or isinstance(data, float) or isinstance(data, bool) or isinstance(data, complex) or isinstance(data, str):
    #         with self._client.open(self.getAbsolutePath(path), "ab") as file:
    #             data = str(data).encode('gbk')
    #             file.write(data)
    #     else:
    #         raise (DataTypeError(type(data)))
    #
    # def appendline(self, path, data):  # 追加一行,编码默认为gbk
    #     """对给定目录path下的文件追加内容一行，内容为data
    #
    #     注意文件必须存在，追加一行
    #
    #     """
    #     self.append(path, data)
    #     self.append(path, "\r\n")
    #     return True
    
    def _append(self, f, data):  # pandas中数据类型难以限制，特地编写了独立的，专用于pandas.DataFrame写入
        data = str(data).encode('gbk')
        f.write(data)
    
    def _appendList(self, f, data):  # 将list写入文件
        total = 0
        for d in data:
            if total > 0:
                f.write(b",")
            total = total + 1
            self._append(f, d)
        f.write(b"\n")

    @statisticLog('xqfile', 'HDFSFile')
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def open(self, path, mode="rb"):
        """打开文件，返回文件操作对象

        :param path: 路径
        :param mode: 打开模式，仅支持: read: "r" "rb"; write with new file:"w" "wb"; append: "a" "ab"
        :return: 文件文件操作对象

        :注意:    未做编码处理，中文会乱码，读中文文件内容请用read
        """
    
        if not self.__check_Dir_Permissions(path):
            raise SystemException("[errno:%i] open(path = %s) Permission denied" % (errno.EPERM, path))
        if mode.strip().find("w") >= 0 or mode.strip().find("a") >= 0:  # 共享目录禁止写入和追加
            if "$" in path[:2]:
                raise SystemException("[errno:%i] open(path = %s) Permission denied" % (errno.EPERM, path))
        self.__check_connect()
        f = self._client.open(self.getAbsolutePath(path), mode)
        return FileOpt(f, mode, 4096)

    @statisticLog('xqfile', 'HDFSFile')
    def read(self, path):
        """读文件，返回给定路径下文件的内容

        | 直接返回文件内容的迭代器

        :param path:
        :return: string generator

        """
        if not self.__check_Dir_Permissions(path):
            raise SystemException("[errno:%i] read(path = %s) Permission denied" % (errno.EPERM, path))
        with self.open(path, "rb") as f:
            while True:
                line = f.readline()
                if line:
                    yield line.decode('gbk')
                else:
                    break

    @statisticLog('xqfile', 'HDFSFile')
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def create(self, path, overwrite=False):
        """创建指定文件

        :param overwrite: 如果文件存在，是否覆盖该文件
        :type overwrite: bool

        """
        if "$" in path[:2]:  # 共享目录禁止新增
            raise SystemException("[errno:%i] create(path = %s) Permission denied" % (errno.EPERM, path))
        self.__check_connect()
        if self.exists(path):
            if overwrite:
                with self._client.open(self.getAbsolutePath(path), "wb") as file:
                    pass
        else:
            with self._client.open(self.getAbsolutePath(path), "wb") as file:
                pass

    @statisticLog('xqfile', 'HDFSFile')
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def getdirtree(self, ddir):
        '''返回给定路径ddir下目录结构

        :param ddir:
        :return:

        '''
        if not self.__check_Dir_Permissions(ddir):
            raise SystemException("[errno:%i] getdirtree(ddir = %s) Permission denied" % (errno.EPERM, ddir))
        treedir = []
        ddir = self.getAbsolutePath(ddir)
        n = len(ddir)
        self.__check_connect()
        for dirpath, dirnames, filenames in self._client.walk(ddir):
            if dirpath == ddir:
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

    @statisticLog('xqfile', 'HDFSFile')
    def write_csvfile(self, path, df):
        """写csv文件，传入的数据 DataFrame

        :param path: 注意文件必须存在,直接使用create创建文件
        :param df: DataFrame
        :return:

        """
        if "$" in path[:2]:
            raise SystemException("[errno:%i] write_csvfile(path = %s) Permission denied" % (errno.EPERM, path))
        with self.open(path, "wb") as f:
            columns = df.columns.tolist()
            self._appendList(f, columns)
            index = len(df.index)
            for i in range(index):
                data = df.iloc[i].values.tolist()
                self._appendList(f, data)
        return True

    @statisticLog('xqfile', 'HDFSFile')
    def read_csvfile(self, path, head=True):
        """读取csv文件，返回 pandas.DataFrame

        :param path:
        :param head=True: 若第一列是DataFrame的列，head为True,否则为false, 默认为True
        :return: pandas.DataFrame

        :注意: 读取数据的列数以第一行为准

        | 第一行的值为列名，返回 pandas.DataFrame

        """
        if not self.__check_Dir_Permissions(path):
            raise SystemException("[errno:%i] read_csvfile(path = %s) Permission denied" % (errno.EPERM, path))
        f = self.read(path)
        firstline = True
        results = []
        dataName = []
        maxlen = 0
        for line in f:
            if firstline:
                dataName = line.strip().strip(',').split(',')
                maxlen = len(dataName)
                firstline = False
                if head == False:  # 当第一行不是pandas的列
                    results.append(dataName)
            else:
                result = line.strip().strip(',').split(',')
                if len(result) > maxlen:
                    maxlen = len(result)
                results.append(result)
        
        nums = len(results)
        if head == True and nums > 0 and maxlen > len(dataName):  # 当第一行是pandas的列，且列数比最大列数少时
            for i in range(maxlen - len(dataName)):
                dataName.append("Unname" + str(i))
        
        for i in range(nums):
            if i == 0 and head == True:
                pass
            else:
                if maxlen > len(results[i]):
                    addlist = [None] * (maxlen - len(results[i]))
                    results[i].extend(addlist)
        
        if head == True:
            df = pandas.DataFrame(results, columns=dataName)
        else:
            df = pandas.DataFrame(results)
        return df
    
    def __converShareDir(self, path):
        '''
        转换共享地址,把原 $12345 转换成 share_12345

        :param path:
        :return:返回转换后的路径
        '''
        if not "$" in path[:2]:
            return path
        rootId = self.__getShareRootId(path)
        # 这里只替换开头部的【$123】这种，后面的不处理
        result = "SHARE_" + rootId + path[path.find("$" + rootId) + len(rootId) + 1:]
        return result

    @statisticLog('xqfile', 'HDFSFile')
    def getAbsolutePath(self, path):
        """返回PATH在大数据平台的绝对路径

        :param path: 相对路径
        "return:"
        """
        if not self.__check_Dir_Permissions(path):  # 无权限时返回None
            return None
        
        if "$" in path[:2]:
            path = self.__converShareDir(path)
            _prepath = prepath_hdfs
        else:
            _prepath = prepath
        
        if len(path) > 0 and path[0] == '/':
            path = path[1:]

        path = os.path.join(_prepath, path)
        if path[-1] == '/':
            path = path[0:len(path) - 1]
        return path

    @statisticLog('xqfile', 'HDFSFile')
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def upload(self, dstPath, srcPath):
        """从本地把文件上传到HDFS,支持目录上传

        :param dstPath: 目标HDFS文件路径
        :param srcPath: 本地文件路径
        """
        # 例样： < / br >
        # client.upload("", "/tmp/log.txt")
        # 上传文件
        # log.txt
        # 到用户默认hdfs目录 < / br >
        # client.upload("", "/tmp/test")
        # 上传目录
        # test
        # 到用户默认hdfs目录 < / br >
        if "$" in dstPath[:2]:
            raise SystemException(
                "[errno:%i] upload(dstPath = %s ,srcPath = %s ) Permission denied" % (errno.EPERM, dstPath, srcPath))
        (src_fp, src_fn) = os.path.split(srcPath)  # 分离本地路径和文件名
        if not os.path.exists(srcPath):
            raise SystemException(
                "[errno:%i] srcPath:%s not exists" % (errno.EEXIST, srcPath))
        self.__check_connect()
        if os.path.isfile(srcPath):  # 如果文件正常处理
            if len(dstPath.strip()) == 0:  # HDFS路径为空时直接把上传文件放入
                dstPath = src_fn
            if self._client.exists(self.getAbsolutePath(dstPath)) and \
                    self._client.isdir(self.getAbsolutePath(dstPath)):
                dstPath += "/" + src_fn
            with io.open(srcPath, mode='rb') as f:
                self._client.upload(self.getAbsolutePath(dstPath), f)
            return True
        if srcPath[-1] == "/":
            srcPath = srcPath[0:-1]
        (dst_fp, dst_fn) = os.path.split(dstPath)  # 分离HDFS路径和文件名
        if not self._client.exists(self.getAbsolutePath(dstPath)):
            self._client.mkdir(self.getAbsolutePath(dstPath))
        filelist = os.listdir(srcPath)
        for file in filelist:
            filePath = srcPath + "/" + file
            if os.path.isfile(filePath):  # 文件
                with io.open(filePath, mode='rb') as f:
                    self._client.upload(self.getAbsolutePath(dstPath + "/" + file), f)
            else:  # 目录
                self.upload(dstPath + "/" + file, srcPath + "/" + file)

    @statisticLog('xqfile', 'HDFSFile')
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def download(self,dstPath,srcPath):
        """从HDFS下载文件到本地
        :param dstPath: 本地路径
        :param srcPath: HDFS
        :return:
        """

        # 例样：
        # client.download(os.getcwd(), "log.txt")
        # 把用户路径下的log.txt下载到当前运行环境目录
        # client.download(os.getcwd(), "test")
        # 把用户路径下的test目录下载到当前运行环境目录
        if "$" in srcPath[:2]:
            raise SystemException(
                "[errno:%i] download(dstPath = %s ,srcPath = %s ) Permission denied" % (errno.EPERM, dstPath, srcPath))
        (src_fp, src_fn) = os.path.split(srcPath)  # 分离路径和文件名
        absSrcPath = self.getAbsolutePath(srcPath)
        self.__check_connect()
        if not self._client.exists(absSrcPath):
            raise SystemException(
                "[errno:%i] srcPath:%s not exists" % (errno.EEXIST, srcPath))
        isFile = self._client.isfile(absSrcPath)
        if self._client.isfile(absSrcPath):  # 如果是文件
            if os.path.exists(dstPath) and \
                    os.path.isdir(dstPath):
                dstPath += "/" + src_fn
            with io.open(dstPath, mode='wb') as f:
                self._client.download(absSrcPath,f,4096)
            return True
        if not os.path.exists(dstPath) and not isFile:  # 不存在并且需要上传的是目录就建立这个本地目录
            os.mkdir(dstPath)
        filelist = self._client.ls(absSrcPath)
        for file in filelist:
            (fp, fn) = os.path.split(file)
            if self._client.isfile(file):  # 文件
                with io.open(os.path.join(dstPath,fn), mode='wb') as f:
                    self._client.download(file, f,4096)
            else:  # 目录
                os.mkdir(os.path.join(dstPath,fn))
                self.download(os.path.join(dstPath,fn), srcPath + "/" + fn)

    @statisticLog('xqfile', 'HDFSFile')
    def getShareFolders(self):
        """
        获取共享目录列表，列表每一项包含name、type、id、root字段
        其中root字段内容为：'$' + id
        :return: 共享目录列表
        """
        return _get_xquant_entry()

    @statisticLog('hdfsfile', 'HDFSFile')
    def getShareFolder(self, arg):
        """第一个符合条件的共享目录root值
        :param arg: 共享目录id、type或name
        :return: 返回第一个符合条件的共享目录root值 没有返回None
        """
        for xq in _get_xquant_entry():
            if xq["orgName"].find(str(arg)) >= 0 or \
                    xq["orgType"].find(str(arg)) >= 0 or \
                    (isinstance(arg, int) and xq['orgId'] == arg):
                return xq["root"]
        return None

    @statisticLog('xqfile', 'HDFSFile')
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def copy(self, srcpath, dstpath):
        """
        从一个hdfs路径拷贝到另一个hdfs路径
        :param srcpath:源路径
        :param dstpath:目标路径
        :return:
        """
        if not self.__check_Dir_Permissions(srcpath, dstpath):
            raise SystemException("[errno:%i] copy(srcpath = %s , dstpath = %s) Permission denied" % (
            errno.EPERM, srcpath, dstpath))
        if not self.exists(srcpath):
            raise IOError("[Errno:%i] %s not exists" % (errno.EEXIST, srcpath))

        abs_srcpath = self.getAbsolutePath(srcpath)
        abs_dstpath = self.getAbsolutePath(dstpath)
        self.__check_connect()
        if not self._client.exists(abs_dstpath):  # 目录不存时新增
            self._client.mkdir(abs_dstpath)

        if self._client.isfile(abs_srcpath):
            filelist = [srcpath]
        else:
            filelist = self.listdir(srcpath)
        for file in filelist:
            __srcFile = abs_srcpath
            if file != srcpath:
                __srcFile += "/" + file
            else:
                file = os.path.split(file)[1]
            if self._client.isfile(__srcFile):
                with self._client.open(__srcFile, "rb") as f:
                    self._client.upload(abs_dstpath + "/" + file, f)
            else:
                new_dstpath = dstpath
                if not dstpath[-1] == "/":
                    new_dstpath += "/"
                new_dstpath += file
                new_srcpath = srcpath
                if not srcpath[-1] == "/":
                    new_srcpath += "/"
                new_srcpath += file
                self.copy(new_srcpath, new_dstpath)
        return True


    @statisticLog('xqfile', 'HDFSFile')
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def copyToShare(self, sharepath, srcpath):
        """
        将自己HDFS目录中的文件或目录复制到共享目录中

        :param sharepath: 共享目录中文件路径，可以使用：getShareFolder('team') + '/sample/abc.csv' 来指定
        :param srcpath: 自己HDFS目录中的文件
        :return: 是否成功
        """
        if not self.__check_Dir_Permissions(sharepath, srcpath):
            raise SystemException("[errno:%i] copyToShare(sharepath = %s , srcpath = %s) Permission denied" % (
            errno.EPERM, sharepath, srcpath))
        if not self.exists(srcpath):  # 判断自己的HDFS是否存在
            raise IOError("[Errno:%i] %s not exists" % (errno.EEXIST, srcpath))
        (share_fp, share_fn) = os.path.split(sharepath)
        (src_fp, src_fn) = os.path.split(srcpath)
        self.__check_connect()
        if self._client.isdir(self.getAbsolutePath(srcpath)) and not share_fn == src_fn:
            if not sharepath[-1] == "/":
                sharepath += "/"
            sharepath += src_fn
        absSharepath = self.getAbsolutePath(sharepath)
        if not self._client.exists(absSharepath):  # 共享目录不存时新增
            self._client.mkdir(absSharepath)
        if self._client.isfile(absSharepath):  # 如果是共享目录并且是一个存在的文件，抛出异常
            raise IOError("[Errno %i] copyToShare : prohibition File coverage :%s" % (errno.EPERM, sharepath))
        (share_fp, share_fn) = os.path.split(absSharepath)
        if (not self._client.exists(absSharepath)) and (not share_fn == src_fn):  # 判断远程目录是否存在不存在时建立
            self._client.mkdir(absSharepath)
        if self._client.isfile(self.getAbsolutePath(srcpath)):
            filelist = [srcpath]
        else:
            filelist = self.listdir(srcpath)
        for file in filelist:
            __srcFile = self.getAbsolutePath(srcpath)
            if not file == srcpath:
                __srcFile += "/" + file
            if self._client.isfile(__srcFile):
                with self._client.open(__srcFile, "rb") as f:
                    self._client.upload(absSharepath + "/" + file, f)
            else:
                __newSharepath = sharepath
                if not sharepath[-1] == "/":
                    __newSharepath += "/"
                __newSharepath += file
                __newSrcpath = srcpath
                if not srcpath[-1] == "/":
                    __newSrcpath += "/"
                __newSrcpath += file
                self.copyToShare(__newSharepath, __newSrcpath)
        return True

    @statisticLog('xqfile', 'HDFSFile')
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def copyFromShare(self, dstpath, sharepath, force=False):
        """
        将共享HDFS目录中的文件或目录复制到自己HDFS目录中

        :param dstpath: 自己HDFS目录中的文件
        :param sharepath: 共享目录中文件路径，可以使用：getShareFolder('team') + '/sample/abc.csv' 来指定
        :param force = False: 是否允许覆盖本地目录中的文件
        :return: 是否成功
        """
        if not self.__check_Dir_Permissions(dstpath, sharepath):
            raise SystemException("[errno:%i] copyFromShare(dstpath = %s , sharepath = %s) Permission denied" % (
            errno.EPERM, dstpath, sharepath))
        absSharepath = self.getAbsolutePath(sharepath)
        self.__check_connect()
        if not self._client.exists(absSharepath):
            raise IOError("[Errno:%i] %s not exists" % (errno.EEXIST, sharepath))
        if not self.exists(dstpath):  # 本地目录不存在时建立
            self.mkdir(dstpath)
        elif not force and self._client.isfile(self.getAbsolutePath(dstpath)):  # 不允许覆盖时如果判断当前路径下有这个文件
            raise IOError("[Errno %i]:prohibition File coverage :%s" % (errno.EPERM, sharepath))
        (share_fp, share_fn) = os.path.split(sharepath)
        (dst_fp, dst_fn) = os.path.split(dstpath)
        if self._client.isdir(self.getAbsolutePath(sharepath)) and (not share_fn == dst_fn):
            if not dstpath[-1] == "/":
                dstpath += "/"
            dstpath += share_fn
            self.mkdir(dstpath)
        if self._client.isfile(absSharepath):
            filelist = [share_fn]
            absSharepath = self.getAbsolutePath(share_fp)
        else:
            filelist = self.listdir(sharepath)
        
        for file in filelist:
            __fullPath = absSharepath + "/" + file
            if self._client.isfile(__fullPath):
                if self._client.exists(
                        self.getAbsolutePath(dstpath) + "/" + file) and force == False:  # 如果用户目录文件存在并不允许覆盖，即跳过
                    continue
                with self._client.open(self.getAbsolutePath(dstpath) + "/" + file, "wb") as f:
                    self._client.download(__fullPath, f, 4096)
            else:
                __newDstpath = dstpath
                if not dstpath[-1] == "/":
                    __newDstpath += "/"
                __newDstpath += file
                __newSharepath = sharepath
                if not sharepath[-1] == "/":
                    __newSharepath += "/"
                __newSharepath += file
                self.copyFromShare(__newDstpath, __newSharepath, force)
        return True
    
    # def putFtp(self, path):
    #     ftp = pyfileFTP(self._client)
    #     return ftp.putFtp(path)
        
    def __check_Dir_Permissions(self, *paths):
        '''
        如目录中的共享目录（$1234）结构检查处理
        :param *paths:
        :return: 可操作有权限时返回True，无权限时为False
        '''
        for path in paths:
            if "$" in path[:2]:
                rootId = self.__getShareRootId(path)
                sf = _get_xquant_entryById(rootId)
                if rootId and sf == None:
                    return False
        return True
    
    def __getShareRootId(self, path):
        '''
        从路径中获取rootId
        :param path:
        :return: 如无返回空
        '''
        if not "$" in path[:2]:
            return None
        search = re.search(r'\$(\d+)', path)  # r提取出$12345中的ROOTID
        if search is None:  # 未匹配到返回
            return None
        return search.group(1)
    
    def __getKwargsStr(self, **kwargs):
        if kwargs.__len__() == 0:
            return ""
        kwargsStr = ""
        for key in kwargs.keys():
            if len(kwargsStr) > 0:
                kwargsStr += ", "
            kwargsStr += key + " = " + str(kwargs[key])
        return kwargsStr
