import errno
import os
import io
import re
from threading import current_thread

import pandas
import pyarrow

# from .setPyfilePath import *
from xquant.pyfile.setPyfilePath import *

# from .setPyfilePath import _get_xquant_entry, _get_xquant_entryById, prepath
from xquant.pyfile.setPyfilePath import _get_xquant_entry, _get_xquant_entryById, prepath
from xquant.utils import statisticLog

_noParmission = "Permission Denied"

ntfsClientDict = {}


class PyFile():
    fo = None
    mode = None
    BATCH_SIZE = None

    @statisticLog('bigdata', 'PyFile')
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

    def readlines(self):
        line_list = []
        while True:
            msg = self.readline()
            if not msg:
                return line_list
            line_list.append(msg)

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


class Hdfsfile(object):
    @statisticLog('bigdata', 'Pyfile')
    def __init__(self):
        global ntfsClientDict
        if ntfsClientDict.get(current_thread().ident) is None:
            print("create pyarrow connection:", end = "")
            ntfsClientDict[current_thread().ident] = pyarrow.hdfs.connect()
            print(pyarrow.hdfs.connect())
            ntfsClientDict[str(current_thread().ident) + "_refs"] = 0
        self._client = ntfsClientDict.get(current_thread().ident)
        ntfsClientDict[str(current_thread().ident) + "_refs"] += 1

    def __del__(self):
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

    def isFile(self,path):
        '''
        判断目标路径是否是文件
        :param path: 绝对路径
        :return: bool值
        '''
        if self._client.isfile(path):
            return True
        return False

    def isDir(self,path):
        '''
        判断目标路径是否是文件夹
        :param path: 绝对路径
        :return: bool值
        '''
        if self._client.isdir(path):
            return True
        return False

    def listdir(self, path):
        """
        返回给定路径path下全部文件名
        :param path:
        :return: 返回路径文件列表
        :rtype: list
        """
        file_list = self._client.ls(path)
        result = []
        for file in file_list:
                result.append(file[file.rindex('/') + 1:])
        return result


    def remove(self, path, **kwargs):
        '''
        删除文件
        :param path:绝对路径
        :param kwargs:
        :return:
        '''
        if not self.exists(path):
            raise Exception("file does not exist!")
        if not self._client.isfile(path):
            raise Exception("Reference error! You need to pass in a file!")
        return self._client.delete(path, **kwargs)

    def __recursion_removedirs(self, path):
        '''
        递归删除文件夹及其子文件夹下的所有文件
        :param path:
        :return:
        '''
        for file in self.listdir(path):
            if self._client.isfile(path+"/"+file):
                self.remove(path+"/"+file)
            else:
                if not self.listdir(path+"/"+file):
                    self._client.delete(path+"/"+file)
                else:
                    self.__recursion_removedirs(path+"/"+file)
        self._client.delete(path)

    def removedirs(self, path, recursion,**kwargs):
        '''
        删除文件夹
        :param recursion:
        :param kwargs:
        :return:
        '''
        if not self.exists(path):
            raise Exception("Folder does not exist!")
        if not self._client.isdir(path):
            raise Exception("Reference error! You need to pass in a Folder!")
        if recursion:
            return self.__recursion_removedirs(path)
        else:
            try:
                return self._client.delete(path, **kwargs)
            except:
                raise Exception(path,"Not an empty directory! Please Set 'recursion=True' for recursive deletion!")

    def __get_file_status(self, path):
        """返回给定路径下文件的状态信息

        :param path:
        :return: Return a dict object, include name, size, last_modified, last_accessed, kind
        """
        file_status = self._client.info(path)
        result = {}
        result['name'] = path[path.rindex('/') + 1:]
        result['size'] = file_status.get('size')
        result['last_modified'] = file_status.get('last_modified')
        result['last_accessed'] = file_status.get('last_accessed')
        result['kind'] = file_status.get('kind')
        return result

    def list_status(self, path):
        """当给定的path是一个目录时，返回该目录下所有文件的状态信息

        :param path:
        :return: list of dict object, include name, size, last_modified, last_accessed, kind
        """
        result = []
        for f in self._client.ls(path, detail=True):
            item = {}
            item['name'] = f['name'][f['name'].rindex('/') + 1:]
            item['size'] = f.get('size')
            item['last_modified'] = f.get('list_modified_time')
            item['last_accessed'] = f.get('list_access_time')
            item['kind'] = f.get('kind')
            result.append(item)
        return result

    def exists(self, path):
        """判断给定路径下文件是否存在

        :param path:绝对路径
        :return:  bool
        """
        return self._client.exists(path)

    def mkdir(self, path):
        """创建一个目录
        :param path:绝对路径
        :return: 目录成功创建返回True,否则返回false
        """
        try:
            self._client.mkdir(path)
            return True
        except Exception as err:
            return False

    def rename(self, path, destination):
        """将文件路径path下文件重命名为destination
        :param path:路径
        :param destination:
        :return: 重命名成功返回True,否则返回False

        """
        try:
            self._client.rename(path, destination)
            return True
        except Exception as err:
            print("Exception:", err)
            return False

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
        f.write(b"\r\n")

    @statisticLog('bigdata', 'Pyfile')
    def open(self, path, mode):
        """打开文件，返回文件操作对象
        :param path: 路径
        :param mode: 打开模式，仅支持: read: "r" "rb"; write with new file:"w" "wb"; append: "a" "ab"
        :return: 文件文件操作对象
        :注意:    未做编码处理，中文会乱码，读中文文件内容请用read
        """
        f = self._client.open(path, mode, buffer_size=4096)
        return PyFile(f,mode,4096)

    def __read(self, path):
        """读文件，返回给定路径下文件的内容
        | 直接返回文件内容的迭代器
        :param path:
        :return: string generator
        """
        with self.open(path, "rb") as f:
            while True:
                line = f.readline()
                if line:
                    yield line.decode('gbk')
                else:
                    break

    def getdirtree(self, ddir):
        '''返回给定路径ddir下目录结构
        :param ddir:
        :return:
        '''
        treedir = []
        n = len(ddir)

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

    def write_csvfile(self, path, df):
        """写csv文件，传入的数据 DataFrame

        :param path: 注意文件必须存在,直接使用create创建文件
        :param df: DataFrame
        :return:

        """
        with self.open(path, "wb") as f:
            columns = df.columns.tolist()
            self._appendList(f, columns)
            index = len(df.index)
            for i in range(index):
                data = df.iloc[i].values.tolist()
                self._appendList(f, data)
        return True

    def read_csvfile(self, path, head=True):
        """读取csv文件，返回 pandas.DataFrame

        :param path:
        :param head=True: 若第一列是DataFrame的列，head为True,否则为false, 默认为True
        :return: pandas.DataFrame

        :注意: 读取数据的列数以第一行为准

        | 第一行的值为列名，返回 pandas.DataFrame

        """
        f = self.__read(path)
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

    def create(self, path, overwrite=False):
        """创建指定文件
        :param overwrite: 如果文件存在，是否覆盖该文件
        :type overwrite: bool
        """
        if self.exists(path):
            if overwrite:
                with self._client.open(path, "wb") as file:
                    pass
                return True
            raise Exception("Failed to create file! The file already exists!")
        else:
            with self._client.open(path, "wb") as file:
                pass

    def upload(self, dstPath, srcPath):
        """从本地把文件上传到HDFS,支持目录上传

        :param dstPath: 目标HDFS文件路径
        :param srcPath: 本地文件路径
        """
        (src_fp, src_fn) = os.path.split(srcPath)  # 分离本地路径和文件名
        (dst_fp, dst_fn) = os.path.split(dstPath)
        if not os.path.exists(srcPath):
            raise SystemException("%s failed! The %s file or folder does not exist!")
        isFile = os.path.isfile(srcPath)
        if isFile:  # 如果文件正常处理
            if self._client.exists(dstPath):
                if self._client.isdir(dstPath):
                    dstPath += "/" + src_fn
                else:
                    raise Exception("The file already exists!")
            if self._client.exists(dstPath):
                raise Exception("The file already exists!")
            if not self.exists(dst_fp):
                self.mkdir(dst_fp)
            with io.open(srcPath, mode='rb') as f:
                self._client.upload(dstPath, f)
            return True
        if self._client.exists(dstPath):
            if self._client.isfile(dstPath):
                raise Exception("The target path is not a folder!")
        if not self._client.exists(dstPath):
            self.mkdir(dstPath)
        if not self._client.exists(os.path.join(dstPath, src_fn)) \
                and not isFile:
            dstPath = os.path.join(dstPath, src_fn)
            self._client.mkdir(dstPath)
        if self._client.exists(os.path.join(dstPath, src_fn)):
            raise IOError("%s failed! The %s folder already exists!")
        filelist = os.listdir(srcPath)
        for file in filelist:
            filePath = srcPath + "/" + file
            if os.path.isfile(filePath):  # 文件
                with io.open(filePath, mode='rb') as f:
                    self._client.upload(os.path.join(dstPath,file), f)
            else:  # 目录
                self.upload(dstPath , filePath)

    def download(self, srcPath, dstPath):
        """从HDFS下载文件到本地
        :param dstPath: 本地路径
        :param srcPath: HDFS
        :return:
        """
        (src_fp, src_fn) = os.path.split(srcPath)  # 分离路径和文件名
        (dst_fp, dst_fn) = os.path.split(dstPath)
        if not self._client.exists(srcPath):
            raise SystemException("%s failed! The %s file or folder does not exist!")
        isFile = self._client.isfile(srcPath)
        if isFile:  # 如果是文件
            if os.path.exists(dstPath):
                if os.path.isdir(dstPath):
                    dstPath += "/" + src_fn
                else:
                    raise Exception("The file already exists!")
            if os.path.exists(dstPath):
                raise Exception("The file already exists!")
            if not self.exists(dst_fp):
                self.mkdir(dst_fp)
            with io.open(dstPath, mode='wb') as f:
                self._client.download(srcPath, f, 4096)
            return True
        if os.path.exists(dstPath):
            if os.path.isfile(dstPath):
                raise Exception("The target path is not a folder!")
        if not os.path.exists(dstPath): # 不存在目录就建立这个本地目录
            os.mkdir(dstPath)
        if not os.path.exists(os.path.join(dstPath, src_fn)) and not isFile:
            dstPath = os.path.join(dstPath, src_fn)
            os.mkdir(dstPath)
        if os.path.exists(os.path.join(dstPath, src_fn)):
            raise Exception("%s failed! The %s folder already exists!")
        filelist = self._client.ls(srcPath)
        for file in filelist:
            (fp, fn) = os.path.split(file)
            if self._client.isfile(file):  # 文件
                with io.open(os.path.join(dstPath, fn), mode='wb') as f:
                    self._client.download(file, f, 4096)
            else:  # 目录
                self.download(srcPath + "/" + fn, dstPath)

    def copyToShare(self, sharepath, srcpath):
        """
        将自己HDFS目录中的文件或目录复制到共享目录中
        :param sharepath: 共享目录中文件路径，可以使用：getShareFolder('team') + '/sample/abc.csv' 来指定
        :param srcpath: 自己HDFS目录中的文件
        :return: 是否成功
        """
        (src_fp, src_fn) = os.path.split(srcpath)
        (dst_fp, dst_fn) = os.path.split(sharepath)
        if not self.exists(srcpath):  # 判断自己的HDFS是否存在
            raise IOError("%s failed! The %s file or folder does not exist!")
        isFile = self._client.isfile(srcpath)
        if isFile:
            if self._client.exists(sharepath):
                 if self._client.isdir(sharepath):
                    sharepath += "/" + src_fn
                 else:
                     raise Exception("The file already exists!")
            if self._client.exists(sharepath):
                raise Exception("The file already exists!")
            if not self.exists(dst_fp):
                self.mkdir(dst_fp)
            with self._client.open(srcpath, "rb") as f:
                self._client.upload(sharepath,f)
            return True
        if self._client.exists(sharepath):
            if self._client.isfile(sharepath):
                raise Exception("The target path is not a folder!")
        if not self._client.exists(sharepath):
            self.mkdir(sharepath)
        if not self._client.exists(os.path.join(sharepath, src_fn)) \
                and not isFile:
            sharepath = os.path.join(sharepath, src_fn)
            self.mkdir(sharepath)
        if self._client.exists(os.path.join(sharepath, src_fn)):
            raise IOError("%s failed! The %s folder already exists!")
        filelist = self._client.ls(srcpath)
        for file in filelist:
            (fp, fn) = os.path.split(file)
            if self._client.isfile(file):
                with self._client.open(file, "rb") as f:
                    self._client.upload(sharepath + "/" +fn, f)
            else:
                self.copyToShare(sharepath, srcpath + "/" + fn)

    def copyFromShare(self, dstpath, absSharepath):
        """
        将共享HDFS目录中的文件或目录复制到自己HDFS目录中
        :param dstpath: 自己HDFS目录中的文件
        :param sharepath: 共享目录中文件路径，可以使用：getShareFolder('team') + '/sample/abc.csv' 来指定
        :return: 是否成功
        """
        (src_fp, src_fn) = os.path.split(absSharepath)
        (dst_fp, dst_fn) = os.path.split(dstpath)
        if not self._client.exists(absSharepath):
            raise IOError("%s failed! The %s file or folder does not exist!")
        isFile = self._client.isfile(absSharepath)
        if isFile:
            if self._client.exists(dstpath):
                if self._client.isdir(dstpath):
                    dstpath += "/" + src_fn
                else:
                    raise Exception("The file already exists!")
            if self._client.exists(dstpath):
                raise Exception("The file already exists!")
            if not self.exists(dst_fp):
                self.mkdir(dst_fp)
            with open(dstpath,mode='wb') as f:
                self._client.download(absSharepath, f, 4096)
            return True
        if self._client.exists(dstpath):
            if self._client.isfile(dstpath):
                raise Exception("The target path is not a folder!")
        if not self._client.exists(dstpath):
            self.mkdir(dstpath)
        if not self._client.exists(os.path.join(dstpath, src_fn)) \
                and not isFile:
            dstpath = os.path.join(dstpath, src_fn)
            self.mkdir(dstpath)
        if self._client.exists(os.path.join(dstpath, src_fn)):
            raise IOError("%s failed! The %s folder already exists!")
        filelist = self._client.ls(absSharepath)
        for file in filelist:
            (fp, fn) = os.path.split(file)
            if self._client.isfile(file):
                with self._client.open(dstpath + "/" + fn, "wb") as f:
                    self._client.download(file, f, 4096)
            else:
                self.copyFromShare(dstpath, absSharepath + "/" + fn)

    def personal_copy(self,dstpath,srcpath):
        '''
        HDFS个人目录复制到个人目录
        :return:
        '''
        (src_fp, src_fn) = os.path.split(srcpath)
        (dst_fp, dst_fn) = os.path.split(dstpath)
        if not self.exists(srcpath):  # 判断自己的HDFS是否存在
            raise IOError("%s failed! The %s file or folder does not exist!")
        isFile = self._client.isfile(srcpath)
        if isFile:
            if self._client.exists(dstpath):
                if self._client.isdir(dstpath):
                    dstpath += "/" + src_fn
                else:
                    raise Exception("The file already exists!")
            if self._client.exists(dstpath):
                raise Exception("The file already exists!")
            if not self.exists(dst_fp):
                self.mkdir(dst_fp)
            with self._client.open(srcpath, "rb") as fsrc:
                with self._client.open(dstpath,"wb") as fdst:
                    self.__copyfileobj(fsrc, fdst)
            return True
        if self._client.exists(dstpath):
            if self._client.isfile(dstpath):
                raise Exception("The target path is not a folder!")
        if not self._client.exists(dstpath):
            self.mkdir(dstpath)
        if not self._client.exists(os.path.join(dstpath, src_fn)) \
                and not isFile:
            dstpath = os.path.join(dstpath, src_fn)
            self.mkdir(dstpath)
        if self._client.exists(os.path.join(dstpath, src_fn)):
            raise IOError("%s failed! The %s folder already exists!")
        filelist = self._client.ls(srcpath)
        for file in filelist:
            (fp, fn) = os.path.split(file)
            if self._client.isfile(file):
                with self._client.open(file, "rb") as fsrc:
                    with self._client.open(dstpath + "/" +fn,"wb") as fdst:
                        self.__copyfileobj(fsrc,fdst)
            else:
                self.copyToShare(dstpath, srcpath + "/" + fn)

    def __copyfileobj(self,fsrc, fdst, length=16 * 1024):
        """copy data from file-like object fsrc to file-like object fdst"""
        while True:
            buf = fsrc.read(length)
            if not buf:
                break
            fdst.write(buf)