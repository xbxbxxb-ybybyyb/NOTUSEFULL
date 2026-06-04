from tquant import StockData
import unittest
import pandas as pd


class TestGetStockDividend(unittest.TestCase):

    def setUp(self):
        self.sd = StockData()
        # 分红因子由多个主键来确定一条数据，所以把所有列打印出来
        pd.set_option('display.max_columns', None)

    def test_get_factor_dividend_1(self):
        # 多支股票 日期 因子 fill_na=True
        df7_1 = self.sd.get_factor_dividend(
            ['600728.SH', '600340.SH', '002016.SZ'], ['20190630', '20190930'],
            ['per_div_trans', 'per_cashpaidbeforetax', 'ex_dt',
             'dvd_payout_dt'], fill_na=True)
        self.assertFalse(df7_1.empty)

    def test_get_factor_dividend_2(self):
        # 列表只有一个元素
        df7_2 = self.sd.get_factor_dividend(['600728.SH'], ['20190630'],
                                           ['per_div_trans'])
        self.assertFalse(df7_2.empty)

    def test_get_factor_dividend_3(self):
        # 单支股票 日期 因子的字符串
        df7_3 = self.sd.get_factor_dividend('600728.SH', '20190630',
                                           'per_div_trans')
        self.assertFalse(df7_3.empty)

    def tearDown(self):
        pass
