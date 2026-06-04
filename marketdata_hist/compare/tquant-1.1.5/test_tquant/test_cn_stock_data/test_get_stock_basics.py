from tquant import StockData
import unittest


class TestGetStockBasics(unittest.TestCase):

    def setUp(self):
        self.sd = StockData()

    def test_get_stock_basics_1(self):
        # 查询单个股票的基本信息
        df1_1 = self.sd.get_stock_basics('000990.SZ')
        self.assertFalse(df1_1.empty)
        self.assertTrue(len(df1_1.columns) == 17)

    def test_get_stock_basics_2(self):
        # 查询列表中只有一个股票的基本信息
        df1_2 = self.sd.get_stock_basics(['000990.SZ'])
        self.assertFalse(df1_2.empty)
        self.assertTrue(len(df1_2.columns) == 17)

    def test_get_stock_basics_3(self):
        # 查询列表中多支股票的基本信息
        df1_3 = self.sd.get_stock_basics(
            ['000990.SZ', '900936.SH', '002160.SZ'])
        self.assertTrue(len(df1_3) == 3)
        self.assertTrue(len(df1_3.columns) == 17)

    def tearDown(self):
        pass


unittest.main(argv=['first-arg-is-ignored'], exit=False)
