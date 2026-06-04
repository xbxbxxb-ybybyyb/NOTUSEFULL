import unittest

from version_control import version_number

if version_number == 0:
    from xquant.pyfilelib import Pyfile
else:
    from xquant.xqutils.pyfilelib import Pyfile



class TestPyfilelib(unittest.TestCase):

    def test_demo(self):
        py = Pyfile()
        # HDFS
        print(py.exists("$/example/"))
        print(py.abspath("$/example/"))
        print(py.getShareFoldersConf())
        print(py.getShareFolders("team"))
        print(py.getTeamInfo())
