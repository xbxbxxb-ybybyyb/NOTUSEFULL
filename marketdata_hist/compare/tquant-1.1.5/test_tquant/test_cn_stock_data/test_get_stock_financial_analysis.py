from tquant import StockData
import unittest


class TestGetStockFinancialAnalysis(unittest.TestCase):

    def setUp(self):
        self.sd = StockData()

    def test_get_stock_financial_analysis_1(self):
        # 多支 股票 日期 因子 fill_na = True
        df5_1 = self.sd.get_factor_financial_analysis(
            ['002314.SZ', '600422.SH', '603369.SH', '601658.SH'],
            ['20191231', '20200331'], ['eps_basic', 'gctogr_ttm', 'tltota_ttm', 'yoy_tr', 'ocftointerest'],
            fill_na=True)
        self.assertTrue(len(df5_1) == 8)

    def test_get_stock_financial_analysis_2(self):
        #  单个日期，fill_na默认False
        df5_2 = self.sd.get_factor_financial_analysis(
            ['002314.SZ', '600422.SH', '000755.SZ'], '20200331',
            ['eps_basic', 'gctogr_ttm', 'tltota_ttm', 'yoy_tr', 'ocftointerest'])
        self.assertFalse(df5_2.empty)
        self.assertTrue(len(df5_2) == 3)

    def test_get_stock_financial_analysis_3(self):
        # 单个股票、日期、因子的字符串
        df5_3 = self.sd.get_factor_financial_analysis('600422.SH', '20200331',
                                                     'roe_ttm')
        self.assertFalse(df5_3.empty)

    def test_get_stock_financial_analysis_4(self):
        # 列表中只有一个股票、日期、因子
        df5_4 = self.sd.get_factor_financial_analysis(['600422.SH'],
                                                     ['20200331'], ['roe_ttm'])
        self.assertFalse(df5_4.empty)

    def tearDown(self):
        pass


unittest.main(argv=['first-arg-is-ignored'], exit=False)
