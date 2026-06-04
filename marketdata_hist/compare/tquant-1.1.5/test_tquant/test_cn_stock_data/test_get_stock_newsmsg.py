from tquant import StockData
import unittest


class TestGetStockNewsmsg(unittest.TestCase):

    def setUp(self):
        self.sd = StockData()

    def test_get_stock_newsmsg_1(self):
        # 多支股票 因子
        df8_1 = self.sd.get_factor_newsmsg(
            ['600077.SH', '002236.SZ', '600373.SH', '688016.SH'],
            ['short_name', 'con_sector', 'listing_place'])
        self.assertFalse(df8_1.empty)

    def test_get_stock_newsmsg_2(self):
        # 单支股票、因子
        df8_2 = self.sd.get_factor_newsmsg(['600077.SH'], ['con_sector'])
        self.assertFalse(df8_2.empty)

    def test_get_stock_newsmsg_3(self):
        # 单支股票、因子的列表
        df8_3 = self.sd.get_factor_newsmsg('600077.SH', 'con_sector')
        self.assertFalse(df8_3.empty)

    def tearDown(self):
        pass


unittest.main(argv=['first-arg-is-ignored'], exit=False)
