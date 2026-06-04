import unittest

from version_control import version_number

if version_number == 0:
    from xquant.pyfile.ftp import pyfileFTP
    ftp = pyfileFTP()
else:
    from xquant.xqutils.xqfile import FTPFile
    ftp = FTPFile()



class TestFtp(unittest.TestCase):

    def test_demo(self):
        print("============================>进行本地文件测试")
        print("测试文件上传")
        print("exist %s " % str(ftp.exist("factor-1.3.5.tar.gz")))
        print("isFile %s " % str(ftp.isFile("factor-1.3.5.tar.gz")))
        print("isDir %s " % str(ftp.isDir("factor-1.3.5.tar.gz")))
