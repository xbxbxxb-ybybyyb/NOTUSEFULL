import os
import unittest

from version_control import version_number

if version_number == 0:
    from xquant.log.log import Log
else:
    from xquant.xqutils.xqlog import XqLog as Log



class TestLog(unittest.TestCase):
    
    def setUp(self):
        if 'IS_JUPYTER' not in os.environ.keys():
            self.has_jupyter_env = False
            os.environ['IS_JUPYTER'] = 'True'
        else:
            self.has_jupyter_env = True
            self.jupter_env_orig = os.environ['IS_JUPTER']


    def test_demo(self):
        logger = Log("test")
        logger.info("This is logging info!")
        logger.debug("This is logging debug!")
        logger.error("This is logging error!")
        logger.warning("This is logging warning!")
        try:
            1/0
        except Exception as e:
            logger.log_except(e)


    def tearDown(self):
        if not self.has_jupyter_env:
            del os.environ['IS_JUPYTER']
        else:
            os.environ['IS_JUPYTER'] = self.jupyter_env_orig

