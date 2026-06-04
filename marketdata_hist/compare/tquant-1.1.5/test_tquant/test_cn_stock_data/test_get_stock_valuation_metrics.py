from tquant import StockData
import unittest


class TestGetStockValuationMetrics(unittest.TestCase):

    def setUp(self):
        self.sd = StockData()

    def test_get_stock_valuation_metrics_1(self):
        # 多支 股票 日期 因子 fill_na = True
        df3_1 = self.sd.get_factor_valuation_metrics(
            ['002302.SZ', '002372.SZ', '300240.SZ', '601658.SH'],
            ['20200506', '20200507'], ['ev', 'mkt_cap_ard', 'pe_ttm'],
            fill_na=True)
        self.assertTrue(len(df3_1) == 8)

    def test_get_stock_valuation_metrics_2(self):
        #  单个日期，fill_na默认False
        df3_2 = self.sd.get_factor_valuation_metrics(
            ['002302.SZ', '002372.SZ', '601658.SH'], '20200506',
            ['ev', 'mkt_cap_ard', 'pe_ttm'])
        self.assertTrue(len(df3_2) == 2)

    def test_get_stock_valuation_metrics_3(self):
        # 单个股票、日期、因子的字符串
        df3_3 = self.sd.get_factor_valuation_metrics('002302.SZ', '20200506',
                                                    'mkt_cap_ard')
        self.assertFalse(df3_3.empty)

    def test_get_stock_valuation_metrics_4(self):
        # 列表中只有一个股票、日期、因子
        df3_4 = self.sd.get_factor_valuation_metrics(['002302.SZ'],
                                                    ['20200506'],
                                                    ['mkt_cap_ard'])
        self.assertFalse(df3_4.empty)

    def tearDown(self):
        pass


unittest.main(argv=['first-arg-is-ignored'], exit=False)
