import unittest

from xquant.futuredata import FutureData


class TestFutureData(unittest.TestCase):
    def setUp(self):
        self.fd = FutureData()

    def test_instrument_info_1(self):
        df = self.fd.get_instrument_info('IF')
        df_len = len(df)
        self.assertTrue(df_len > 0)

    def test_instrument_info_2(self):
        with self.assertRaises(Exception):
            df = self.fd.get_instrument_info('IFFF')

    def test_get_change_date(self):
        result = self.fd.get_change_date('IF', '20170309', 'ZL00')
        res_len = len(result)
        self.assertTrue(res_len == 3)

    def test_instrument_all(self):
        result = self.fd.get_instrument_all('IF', 20170101, 20190720)
        res_len = len(result)
        self.assertTrue(res_len > 0)

    def test_future_data_1(self):
        result = self.fd.get_future_data("ICZL", "20190101000000000", "20190701000000000", 'K_DAY')
        res_len = len(result)
        self.assertTrue(res_len > 0)

    def test_future_data_2(self):
        df1 = self.fd.get_future_data("ICZL", "20190101000000000", "20190701000000000", 'K_DAY')
        df2 = self.fd.get_future_data("ICZL", "20190101000000000", "20190701000000000", 'K_DAY', method=True)
        col1 = len(df1.columns)
        col2 = len(df2.columns)
        self.assertTrue(col1 == col2)
        self.assertTrue(len(df1) == len(df2))
        self.assertTrue(len(df1) > 0)

    def test_future_data_3(self):
        df = self.fd.get_future_data("IC1808", "20180101000000000", "20181001000000000", 'K_DAY')
        self.assertTrue(len(df) > 0)

    def test_future_data_4(self):
        df = self.fd.get_future_data("ICZL", "20190102000000000", "20190903173000000", 'K_1MIN')
        col_num = len(df.columns)
        self.assertTrue(col_num == 12)

    def test_future_data_5(self):
        df = self.fd.get_future_data("ICZL", "20190101000000000", "20190201000000000", 'K_DAY')
        col_num = len(df.columns)
        self.assertTrue(col_num == 12)

    def test_future_data_6(self):
        df = self.fd.get_future_data("IFZL", "20190102000000000", "20190103173000000", 'TICK')
        col_num = len(df.columns)
        self.assertTrue(col_num == 20)

    def test_future_data_7(self):
        df = self.fd.get_future_data("IC1808", "20180101000000000", "20180201000000000", 'K_1MIN')
        col_num = len(df.columns)
        self.assertTrue(col_num == 10)

    def test_future_data_8(self):
        df = self.fd.get_future_data("IC1808", "20180701000000000", "20180801000000000", 'TICK')
        col_num = len(df.columns)
        self.assertTrue(col_num == 42)

    def tearDown(self):
        pass