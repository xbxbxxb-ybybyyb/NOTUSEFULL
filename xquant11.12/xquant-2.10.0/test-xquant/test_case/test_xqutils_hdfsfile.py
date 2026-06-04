import unittest

from version_control import version_number



class TestHdfsfile(unittest.TestCase):

    def test_demo(self):
        if version_number == 0:
            from xquant.pyfile import Pyfile
            hf = Pyfile()
        else:
            from xquant.xqutils.xqfile import HDFSFile
            hf = HDFSFile()

        print(hf.listdir(""))
        print(hf.getdirtree(""))

        print(hf.exists("hy/aa.txt"))
        print(hf.getAbsolutePath(""))
