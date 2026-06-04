from tquant import IndexData
import unittest


class TestIndexData(unittest.TestCase):
    def setUp(self):
        self.ind = IndexData()

    def test_get_index_info_1(self):
        # weight_type=0取当日权重
        df1_1 = self.ind.get_index_info('20191112', 'HS300', 0)
        self.assertTrue(len(df1_1.columns) == 3)

    def test_get_index_info_2(self):
        # weight_type=1取次日权重
        df1_2 = self.ind.get_index_info('20191112', 'SH50', 1)
        self.assertTrue(len(df1_2.columns) == 3)

    def tearDown(self):
        pass
