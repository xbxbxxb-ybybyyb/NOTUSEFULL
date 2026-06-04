from tquant import StockData
import unittest


class TestGetStockPriceDaily(unittest.TestCase):

    def setUp(self):
        self.sd = StockData()

    def test_get_stock_price_daily_1(self):
        # 多支 股票 日期 因子 fill_na = True
        df2_1 = self.sd.get_factor_price_daily(
            ['300707.SZ', '300726.SZ', '300705.SZ', '601658.SH'],
            ['20200506', '20200507'], ['pre_close', 'open', 'high'],
            fill_na=True)
        self.assertTrue(len(df2_1) == 8)

    def test_get_stock_price_daily_2(self):
        #  单个日期，fill_na默认False
        df2_2 = self.sd.get_factor_price_daily(
            ['300707.SZ', '300726.SZ', '000809.SZ'], '20200506',
            ['pre_close', 'open', 'high'])
        self.assertTrue(len(df2_2) == 3)

    def test_get_stock_price_daily_3(self):
        # 单个股票、日期、因子的字符串
        df2_3 = self.sd.get_factor_price_daily('300707.SZ', '20200506', 'high')
        self.assertFalse(df2_3.empty)

    def test_get_stock_price_daily_4(self):
        # 列表中只有一个股票、日期、因子
        df2_4 = self.sd.get_factor_price_daily(['300707.SZ'], ['20200506'],
                                              ['high'])
        self.assertFalse(df2_4.empty)

    def tearDown(self):
        pass


unittest.main(argv=['first-arg-is-ignored'], exit=False)
