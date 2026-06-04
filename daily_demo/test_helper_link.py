import unittest

from xquant.xqutils.helper import link
from xquant.setXquantEnv import xquantEnv, testEnv

lm = link.LinkMessage()

class TestLink(unittest.TestCase):

    def test_demo(self):
        if xquantEnv==1:
            lm.sendMessage("XQuant SDK messages!")
