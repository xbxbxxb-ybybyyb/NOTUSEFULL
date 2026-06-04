import unittest

from sample_spark import sparkmrDemo

from version_control import version_number



class TestSpark(unittest.TestCase):

    def test_spark(self):
       demo = sparkmrDemo()
       demo.start()
