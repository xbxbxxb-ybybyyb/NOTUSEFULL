from tquant import StockData
import unittest


class TestGetMdQuotes(unittest.TestCase):

    def setUp(self):
        self.sd = StockData()

    def test_get_md_transaction(self):
        df10_1 = self.sd.get_md_transaction('900957.SH', '20190709 090000000',
                                            '20190710 080000000')
        self.assertFalse(df10_1.empty)

    def test_get_md_order(self):
        df11_1 = self.sd.get_md_order('000001.SZ', '20190709 090000000',
                                      '20190710 080000000')
        self.assertFalse(df11_1.empty)

    def test_get_md_kline(self):
        df12_1 = self.sd.get_md_kline('000001.SZ', '20190709 090000000',
                                      '20190710 080000000')
        self.assertFalse(df12_1.empty)

    def test_get_md_tick(self):
        df13_1 = self.sd.get_md_tick('000001.SZ', '20190709 090000000',
                                     '20190710 080000000')
        self.assertFalse(df13_1.empty)

    def tearDown(self):
        pass
