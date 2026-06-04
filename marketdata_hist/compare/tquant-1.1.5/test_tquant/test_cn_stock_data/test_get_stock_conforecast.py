from tquant import StockData
import unittest


class TestGetStockConforecast(unittest.TestCase):

    def setUp(self):
        self.sd = StockData()

    def test_get_stock_conforecast(self):
        # stock_type block_type取值详见参数说明
        df9_1 = self.sd.get_factor_conforecast(['603506', '601828', '600775'],
                                              ['20180102', '20180103'],
                                              ['rating_up_number7',
                                               'report_number30'],
                                              stock_type=1, block_type=2)
        self.assertFalse(df9_1.empty)

    def tearDown(self):
        pass


unittest.main(argv=['first-arg-is-ignored'], exit=False)
