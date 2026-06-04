from tquant import StockData
import unittest


class TestGetStockIssuingDate(unittest.TestCase):

    def setUp(self):
        self.sd = StockData()

    def test_get_stock_issuingdate_1(self):
        # 多支 股票 日期 只有一个因子 fill_na = True
        df1 = self.sd.get_factor_issuingdate(
            ['300715.SZ', '300079.SZ', '600053.SH'],
            ['20191231', '20200331'], ['s_div_preanndt'],
            fill_na=True)
        self.assertTrue(len(df1) == 6)

    def test_get_stock_issuingdate_2(self):
        #  单个日期，fill_na默认False
        df2 = self.sd.get_factor_issuingdate(
            ['300715.SZ', '300079.SZ', '600053.SH'], '20191231', ['s_div_preanndt'])
        self.assertFalse(df2.empty)
        self.assertTrue(len(df2) == 3)

    def tearDown(self):
        pass


unittest.main(argv=['first-arg-is-ignored'], exit=False)
