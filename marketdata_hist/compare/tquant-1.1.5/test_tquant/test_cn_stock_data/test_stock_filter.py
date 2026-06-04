from tquant import StockData
import unittest


class TestStockFilter(unittest.TestCase):

    def setUp(self):
        self.sd = StockData()

    def test_stock_filter_1(self):
        # filter_type默认'SSO',过滤过滤掉STPT+停牌+开盘涨停的股票
        stock_pool1 = self.sd.get_plate_info('MARKET', '20190409', 'SHA').loc[:, 'stock'].tolist()
        df16_1 = self.sd.stock_filter(stock_pool1, '20190409')
        self.assertTrue(len(df16_1) < len(stock_pool1))

    def test_stock_filter_2(self):
        # 过滤开盘跌停
        stock_pool2 = self.sd.get_plate_info('MARKET', '20190308', 'SHA').loc[:, 'stock'].tolist()
        df16_2 = self.sd.stock_filter(stock_pool2, '20190308', filter_type='OPENDOWNLIMIT')
        self.assertTrue(len(df16_2) < len(stock_pool2))

    def tearDown(self):
        pass


unittest.main(argv=['first-arg-is-ignored'], exit=False)
