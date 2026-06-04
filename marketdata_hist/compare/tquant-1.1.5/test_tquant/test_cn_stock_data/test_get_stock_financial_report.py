from tquant import StockData
import unittest


class TestGetStockFinancialReport(unittest.TestCase):

    def setUp(self):
        self.sd = StockData()

    def test_get_stock_financial_report_1(self):
        # 多支 股票 日期 因子 fill_na = True statement_type默认102(合并报表)
        df6_1 = self.sd.get_factor_financial_report(
            ['300397.SZ', '002594.SZ', '600533.SH', '601658.SH'],
            ['20200331', '20191231'], ['monetary_cap', 'notes_rcv', 'dvd_rcv'], statement_type='102',
            fill_na=True)
        print(df6_1)
        self.assertTrue(len(df6_1) == 8)

    def test_get_stock_financial_report_2(self):
        #  单个日期，fill_na默认False
        df6_2 = self.sd.get_factor_financial_report(
            ['300397.SZ', '002594.SZ', '000755.SZ'], '20200331',
            ['settle_rsrv', 'prem_rcv', 'tot_oper_rev'],
            statement_type='108')
        print(df6_2)
        self.assertFalse(df6_2.empty)
        self.assertTrue(len(df6_2) == 3)

    def test_get_stock_financial_report_3(self):
        # 单个股票、日期、因子的字符串
        df6_3 = self.sd.get_factor_financial_report('000999.SZ', '20200331',
                                                   'tot_oper_rev', statement_type='102', )
        print(df6_3)

        self.assertFalse(df6_3.empty)

    def test_get_stock_financial_report_4(self):
        # 列表中只有一个股票、日期、因子
        df6_4 = self.sd.get_factor_financial_report(['300397.SZ'], ['20200331'],
                                                   ['tot_oper_rev'],
                                                   statement_type='108')
        self.assertFalse(df6_4.empty)

    def tearDown(self):
        pass


unittest.main(argv=['first-arg-is-ignored'], exit=False)
