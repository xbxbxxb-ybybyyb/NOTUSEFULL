from tquant import StockData
import unittest


class TestGetStockIndustry(unittest.TestCase):

    def setUp(self):
        self.sd = StockData()
        self.trading_codes = ['600000.SH', '600004.SH', '600006.SH', '600007.SH',
                         '600008.SH']

    def test_get_stock_industry_1(self):
        # CSRC 证监会行业只有两级所以不能用industry_level的默认值3，需要指定值
        df15_1 = self.sd.get_stock_industry(self.trading_codes, '20190308', 'CSRC',
                                            industry_level=2)

        self.assertFalse(df15_1.empty)
        self.assertTrue(len(df15_1.columns) == 4)

    def test_get_stock_industry_2(self):
        # CITICS 中信行业 industry_level默认3级行业分类
        df15_2 = self.sd.get_stock_industry(self.trading_codes, '20190308',
                                            'CITICS')
        self.assertFalse(df15_2.empty)
        self.assertTrue(len(df15_2.columns) == 4)

    def test_get_stock_industry_3(self):
        # SW 申万行业
        df15_3 = self.sd.get_stock_industry(self.trading_codes, '20190516',
                                            'SW', industry_level=2)
        self.assertFalse(df15_3.empty)
        self.assertTrue(len(df15_3.columns) == 4)

    def test_get_stock_industry_4(self):
        # industry_type不指定行业时 返回全部3个行业的信息
        df15_4 = self.sd.get_stock_industry(self.trading_codes, '20190308',
                                            industry_level=2)
        self.assertTrue(len(df15_4.columns) == 4)
        self.assertTrue(len(df15_4) == len(self.trading_codes) * 3)

    def tearDown(self):
        pass


unittest.main(argv=['first-arg-is-ignored'],exit=False)