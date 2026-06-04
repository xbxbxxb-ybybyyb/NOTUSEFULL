from tquant import StockData
import unittest


class TestGetStockRiskAnalysis(unittest.TestCase):

    def setUp(self):
        self.sd = StockData()

    def test_get_stock_risk_analysis_1(self):
        # 多支 股票 日期 因子 fill_na = True
        df4_1 = self.sd.get_factor_risk_analysis(
            ['600373.SH', '600395.SH', '600318.SH', '601658.SH'],
            ['20200506', '20200507'],
            ['annualyeild_100w', 'beta_100w', 'beta_60m'], fill_na=True)
        self.assertTrue(len(df4_1) == 8)

    def test_get_stock_risk_analysis_2(self):
        #  单个日期，fill_na默认False
        df4_2 = self.sd.get_factor_risk_analysis(
            ['600373.SH', '600395.SH', '601658.SH'], '20200506',
            ['annualyeild_100w', 'beta_100w', 'beta_60m'])
        self.assertTrue(len(df4_2) == 2)

    def test_get_stock_risk_analysis_3(self):
        # 单个股票、日期、因子的字符串
        df4_3 = self.sd.get_factor_risk_analysis('600373.SH', '20200506',
                                                'annualyeild_100w')
        self.assertFalse(df4_3.empty)

    def test_get_stock_risk_analysis_4(self):
        # 列表中只有一个股票、日期、因子
        df4_4 = self.sd.get_factor_risk_analysis(['600373.SH'], ['20200506'],
                                                ['beta_100w'])
        self.assertFalse(df4_4.empty)

    def tearDown(self):
        pass


unittest.main(argv=['first-arg-is-ignored'], exit=False)
