import ftplib
import os
import time
import errno
from pyarrow import HadoopFileSystem
from .setPyfilePath import *
from .setPyfilePath import _ftpEnv, SystemException, _tmpName
from pathlib import Path
from pyarrow import hdfs

class FTPFile():
    __ftp = None
    __hdfsClient = None
    __lines = []
    
    
    def __init__(self):
        """
        初始化时需要放入HadoopFileSystem连接完成的对象
        :param ntfsClient:
        """
        # if not isinstance(ntfsClient, HadoopFileSystem):
        #     raise SystemException("[errno: %s] ntfsClient[%s] type err" % (errno.EFAULT, type(ntfsClient)))
        # self.__hdfsClient = ntfsClient
        self._connection()
        
    def _getHDFS(self):
        if self.__hdfsClient is None:
            self.__hdfsClient = hdfs.connect()
        return self.__hdfsClient
    
    def _connection(self):
        """
        连接FTP，连接使用配置项
        :return:
        """
        self.__ftp = ftplib.FTP(_ftpEnv["url"], _ftpEnv["username"], _ftpEnv["password"])
        self.__ftp.encoding = "UTF-8"
        self.__ftp.cwd(_ftpEnv["dir"])
    
    
    def _checkConnection(self):
        """
        检查连接是否正常
        :return:
        """
        try:
            self.__ftp.sendcmd("NOOP")
        except Exception as err:
            self._connection()
    
    
    def _put(self, path):
        """
        从本地上传到FTP服务器
        :param path:
        :return:
        """
        isClean = True
        if not os.path.exists(path):# 判断路径是否存在
            raise SystemException("[errno:%s] path: %s not exists" % (errno.EEXIST, path))
        isFile = os.path.isfile(path)
        (fp, fn) = os.path.split(path)
        ftpPath = os.path.join(_ftpEnv["dir"], fn)
        # 检查FTP文件或目录是否存在，存在报错
        if self.exist(ftpPath):  # 文件或目录已经存在
            raise SystemException("[errno:%s] path: %s exists" % (errno.EEXIST, fn))
        # 如果是目录新建临时目录 使用_时间戳方式
        now = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        _tmpName = fn + now
        try:
            # 上传（支持多级目录）,并下载到本地/tmp目录 进行文件比较
            remoteFilePath = os.path.join(_ftpEnv["dir"], _tmpName )
            if isFile:  # 文件
                self._uploadFile(path, remoteFilePath)
                if not self.checkFileConsistency(path, remoteFilePath):
                    return False
            else:  # 目录
                self.__ftp.mkd(_tmpName + now)
                self._uploadDir(path, remoteFilePath)
                if not self.checkDirConsistency(path, remoteFilePath):
                    return False
            # 更名（只传文件时从临时目录中取出并删除临时目录）
            self.__ftp.rename(remoteFilePath,ftpPath)
            isClean = False
            return True
        except Exception as err:
            raise err
        finally:  # 保证原子操作把文件删除
            if isClean:
                delFilePath = os.path.join(_ftpEnv["dir"], _tmpName + now)
                if isFile:
                    self.__ftp.delete(delFilePath)
                else:
                    self._rmDir(delFilePath)
                return False
    
    
    def _putHDFS(self, hdfsPath):
        """
        从HDFS上传到FTP服务器上
        保证原子性（一次上传，过程失败就删除并提示错误）
        检验一致性（上传完成对二端下载并进行数据校验比较文件一致性），如不一致删除FTP端提示
        :param hdfsPath:
        :return: boolean  成功True 失败False
        """
        isClean = True
        if not self._getHDFS().exists(hdfsPath):
            raise SystemException("[errno:%s] hdfsPath: %s not exists" % (errno.EEXIST, hdfsPath))
        isFile = self._getHDFS().isfile(hdfsPath)
        # 检查FTP文件或目录是否存在，存在报错
        (fp, fn) = os.path.split(hdfsPath)
        ftpPath = os.path.join(_ftpEnv["dir"], fn)
        if self.exist(ftpPath):  # 文件或目录已经存在
            raise SystemException("[errno:%s] path: %s exists" % (errno.EEXIST, fn))
        # 如果是目录新建临时目录 使用_时间戳方式
        now = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        _tmpName = fn + now
        try:
            # 上传（支持多级目录）,并下载到本地/tmp目录 进行文件比较
            remoteFilePath = os.path.join(_ftpEnv["dir"], _tmpName)
            if isFile:  # 文件
                self._uploadHDFSFile(hdfsPath, remoteFilePath)
                if not self.checkHDFSFileConsistency(hdfsPath, remoteFilePath):
                    return False
            else:   # 目录
                self.__ftp.mkd(_tmpName + now)
                self._uploadHDFSDir(hdfsPath, remoteFilePath)
                if not self.checkHDFSDirConsistency(hdfsPath, remoteFilePath):
                    return False
            # 更名（只传文件时从临时目录中取出并删除临时目录）
            self.__ftp.rename(remoteFilePath,ftpPath)
            isClean = False
            return True
        except Exception as err:
            raise err
        finally:  # 保证原子操作把文件删除
            if isClean:
                delFilePath = os.path.join(_ftpEnv["dir"], _tmpName + now)
                if isFile:
                    self.__ftp.delete(delFilePath)
                else:
                    self._rmDir(delFilePath)
                return False
    
    
    def _rmFile(self, remotefilepath):
        """
        删除FTP上文件
        :param remotefilepath:
        :return:
        """
        self.__ftp.delete(remotefilepath)
        return True
    
    
    def _rmDir(self, remotePath):
        """
        删除服务器中目录，使用递归方式下级
        :param remotePath:
        :return:
        """
        if remotePath[-1] == "/":
            remotePath = remotePath[:-1]
        for (name, entry) in self.__ftp.mlsd(remotePath):
            if entry['type'] == 'dir':  # 目录
                self._rmDir(remotePath + "/" + name)
            if entry['type'] == 'file':  # 文件
                self._rmFile(remotePath + "/" + name)
        self.__ftp.rmd(remotePath)
        return True

    def uploadDir(self, dir, remoteDir):
        """
        从本地上传目录到FTP
        :param hdfsDir:
        :param remoteDir:
        :return:
        """
        remoteDir = self._addRootPath(remoteDir)
        self._uploadDir(dir,remoteDir)

    def uploadHDFSDir(self, hdfsDir, remoteDir):
        """
        从HDFS上传目录到FTP
        :param hdfsDir:
        :param remoteDir:
        :return:
        """
        remoteDir = self._addRootPath(remoteDir)
        hdfsDir = self._addHDFSRootPath(hdfsDir)
    
        self._uploadHDFSDir(hdfsDir, remoteDir)
    
    def uploadFile(self, file, remoteFile):
        """
        从本地上传文件到FTP
        :param hdfsFile:
        :param remoteFile:
        :return:
        """
        remoteFile = self._addRootPath(remoteFile)
        self._uploadFile(file,remoteFile)

    def uploadHDFSFile(self, hdfsFile, remoteFile):
        """
        从HDFS上传文件到FTP
        :param hdfsFile:
        :param remoteFile:
        :return:
        """
        hdfsFile = self._addHDFSRootPath(hdfsFile)
        remoteFile = self._addRootPath(remoteFile)
        self._uploadHDFSFile(hdfsFile, remoteFile)

    def downloadDir(self, remotePath, dstPath):
        """
        下载目录到本地路径
        :param remotePath:
        :param dstPath:
        :return:
        """
        remotePath = self._addRootPath(remotePath)
        self._downloadDir(remotePath, dstPath)

    def downloadFile(self, remoteFile, dstFilePath):
        """
        下载文件到本地路径
        注意这里是本地路径
        :param remoteFile:
        :param dstFilePath:
        :return:
        """
        remoteFile = os.path.join(_ftpEnv['dir'], remoteFile)
        self._downloadFile(remoteFile, dstFilePath)

    def _uploadDir(self, dir, remoteDir):
        """
        从本地上传目录到FTP
        :param hdfsDir:
        :param remoteDir:
        :return:
        """
        self._checkConnection()
        
        if os.path.isdir(dir) == False:
            return False
        if not self.exist(remoteDir):
            self.__ftp.mkd(remoteDir)
        if not self.isDir(remoteDir):
            raise IOError("[errno:%s] remoteDir = %  not Dir" % (errno.EFAULT, remoteDir))
        paths = os.listdir(dir)
        for p in paths:
            dst = os.path.join(remoteDir, p)
            p=os.path.join(dir,p)
            if os.path.isdir(p):
                self._uploadDir(p, dst)
            else:
                self._uploadFile(p, dst)
        return True
    
    def _uploadHDFSDir(self, hdfsDir, remoteDir):
        """
        从HDFS上传目录到FTP
        :param hdfsDir:
        :param remoteDir:
        :return:
        """
        self._checkConnection()
        if self._getHDFS().isdir(hdfsDir) == False:
            return False
        if not self.exist(remoteDir):
            self.__ftp.mkd(remoteDir)
        if not self.isDir(remoteDir):
            raise IOError("[errno:%s] remoteDir = %  not Dir" % (errno.EFAULT,remoteDir))
        hdfsFiles = self._getHDFS().ls(hdfsDir)
        for file in hdfsFiles:
            (fp, fn) = os.path.split(file)
            dst = os.path.join(remoteDir, fn)
            if self._getHDFS().isdir(file):
                self._uploadHDFSDir(file, dst)
            else:
                self._uploadHDFSFile(file, dst)
        return True
    
    def _uploadFile(self, file, remoteFile):
        """
        从本地上传文件到FTP
        :param hdfsFile:
        :param remoteFile:
        :return:
        """
        self._checkConnection()
        with open(file,'rb') as f:
            self.__ftp.storbinary('STOR %s' % remoteFile, f, 4096)
        return True

    
    def _uploadHDFSFile(self, hdfsFile, remoteFile):
        """
        从HDFS上传文件到FTP
        :param hdfsFile:
        :param remoteFile:
        :return:
        """
        self._checkConnection()
        if not self._getHDFS().isfile(hdfsFile):
            return False
        with self._getHDFS().open(hdfsFile,'rb') as f:
            self.__ftp.storbinary('STOR %s' % remoteFile, f, 4096)
        return True
    
    
    def checkDirConsistency(self, dir, remoteDir):
        """
        检查目录的一致
        通过下载到本地的/tmp下进行文件比较
        :param dir:
        :param remoteDir:
        :return:
        """
        paths = os.listdir(dir)
        for p in paths:
            ftpFilePath = os.path.join(remoteDir, p)
            fullPath = os.path.join(dir,p)
            if os.path.isdir(fullPath):
                if not self.exist(ftpFilePath) or \
                        not self.isDir(ftpFilePath):
                    return False
                if not self.checkDirConsistency(fullPath, ftpFilePath):
                    return False
            else:
                if not self.checkFileConsistency(fullPath, ftpFilePath):
                    return False
        return True
    
    
    def checkHDFSDirConsistency(self, hdfsDir, remoteDir):
        """
        检查目录的一致
        通过下载到本地的/tmp下进行文件比较
        :param hdfsDir:
        :param remoteDir:
        :return:
        """
        hdfsFiles = self._getHDFS().ls(hdfsDir)
        for hdfsPath in hdfsFiles:
            (fp,fn) = os.path.split(hdfsPath)
            ftpFilePath = os.path.join(remoteDir, fn)
            if self._getHDFS().isdir(hdfsPath):
                if not self.exist(ftpFilePath) or \
                        not self.isDir(ftpFilePath):
                    return False
                if not self.checkHDFSDirConsistency(hdfsPath, ftpFilePath):
                    return False
            else:
                if not self.checkHDFSFileConsistency(hdfsPath, ftpFilePath):
                    return False
        return True
    
    
    def checkFileConsistency(self, file, remoteFile):
        """
        检查HDFS文件和FTP文件的一致性
        遇到文件时会下载到本地路径/tmp下进行文件比较
        :param file:
        :param remoteFile:
        :return: True|False
        """
        #下载远程文件到本地/tmp目录
        tmpFile = "/tmp/.tmp_" + time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        self._downloadFile(remoteFile, tmpFile)
        #下载后判断临时文件是否存在
        if not os.path.exists(tmpFile) or \
                not os.path.isfile(tmpFile):
            return False
        if not os.path.exists(file) or \
                not os.path.isfile(file):
            return False
        #对比下载的文件大小
        if not os.path.getsize(tmpFile) == os.path.getsize(file):
            return False
        #从流中每次读到十个字节对比
        with open(tmpFile,"rb") as tf:
            with open(file, "rb") as f:
                while True:
                    s = tf.read(1024)
                    s2 = f.read(1024)
                    if not s==s2:
                        return False
                    if not s:
                        break
        #删除本地文件
        os.remove(tmpFile)
        return True
    
    
    def checkHDFSFileConsistency(self, hdfsFile, remoteFile):
        """
        检查HDFS文件和FTP文件的一致性
        遇到文件时会下载到本地路径/tmp下进行文件比较
        :param hdfsFile:
        :param remoteFile:
        :return: True|False
        """
        #下载远程文件到本地/tmp目录
        tmpFile = "/tmp/.tmp_" + time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        self._downloadFile(remoteFile, tmpFile)
        #下载后判断临时文件是否存在
        if not os.path.exists(tmpFile) or not os.path.isfile(tmpFile):
            return False
        if not self._getHDFS().exists(hdfsFile) or \
                not self._getHDFS().isfile(hdfsFile):
            return False
        #对比下载的文件和HDFS文件大小
        if not os.path.getsize(tmpFile) == self._getHDFS().stat(hdfsFile)["size"]:
            return False
        #从流中每次读到十个字节对比
        with open(tmpFile,"rb") as file:
            with self._getHDFS().open(hdfsFile,"rb") as hdfsFile:
                while True:
                    s = file.read(1024)
                    s2 = hdfsFile.read(1024)
                    if not s==s2:
                        return False
                    if not s:
                        break
        #删除本地文件
        os.remove(tmpFile)
        return True
    
    def _downloadDir(self, remotePath, dstPath):
        self._checkConnection()
        if not self.isDir(remotePath):
            return False
        if not os.path.exists(dstPath):
            os.mkdir(dstPath)
        for path,pInfo in self.__ftp.mlsd(remotePath):
            if path=='.':
                continue
            cRemotePath = os.path.join(remotePath,path)
            cDstPath = os.path.join(dstPath,path)
            if pInfo.get('type') == 'file':
                self._downloadFile(cRemotePath,cDstPath)
            else:
                self._downloadDir(cRemotePath,cDstPath)
        return True
            
    def _downloadFile(self, remoteFile, dstFilePath):
        """
        下载文件到本地路径
        注意这里是本地路径
        :param remoteFile:
        :param dstFilePath:
        :return:
        """
        self._checkConnection()
        with open(dstFilePath, 'wb') as f:
            self.__ftp.retrbinary('RETR ' + remoteFile, f.write, 4096)  # 接收服务器上文件并写入本地文件
    
    def _addRootPath(self,path):
        if path[0]=='/':
            path = path[1:]
        return os.path.join(_ftpEnv['dir'],path)
    
    def _addHDFSRootPath(self,hdfspath):
        if hdfspath[0] == '/':
            hdfspath = hdfspath[1:]
        return os.path.join(prepath,hdfspath)
    
    def isDir(self, remotePath):
        """
        判断FTP路径是否为目录
        :param remotePath:
        :return:
        """
        self._checkConnection()
        self.__lines.clear()
        self.__ftp.retrlines('LIST ' + remotePath, lambda line: self.__lines.append(line))
        for line in self.__lines:
            ss = line.lower().split(" ")
            if len(ss) > 0 and "drw" in ss[0]:
                return True
        return False
    
    
    def exist(self, remotePath):
        """
        判断FTP上文件或目录是否存在
        :param remotePath:
        :return:
        """
        self._checkConnection()
        self.__lines.clear()
        self.__ftp.retrlines('LIST ' + remotePath, lambda line: self.__lines.append(line))
        if len(self.__lines) > 0:
            return True
        return False
    
    def isFile(self, remotePath):
        """
        判断FTP路径是否为文件
        :param remotePath:
        :return:
        """
        self._checkConnection()
        self.__lines.clear()
        self.__ftp.retrlines('LIST ' + remotePath, lambda line: self.__lines.append(line))
        (fp, fn) = os.path.split(remotePath)
        if len(self.__lines) == 1 and fn in self.__lines[0].lower().split(" "):
            return True
        return False

pyfileFTP = FTPFile