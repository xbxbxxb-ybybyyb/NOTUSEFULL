from tquant import StockData
import unittest


class TestGetPlateInfo(unittest.TestCase):

    def setUp(self):
        self.sd = StockData()

    def test_get_plate_info_1(self):
        # 中信行业全部
        df14_1 = self.sd.get_plate_info('INDUSTRY', '20191202', 'CITICS.b1')
        self.assertFalse(df14_1.empty)
        self.assertTrue(len(df14_1.columns) == 4)

    def test_get_plate_info_2(self):
        # 中信一级行业
        df14_2 = self.sd.get_plate_info('INDUSTRY', '20190108', 'CITICS.b101')
        self.assertFalse(df14_2.empty)
        self.assertTrue(len(df14_2.columns) == 4)

    def test_get_plate_info_3(self):
        # 中信二级行业
        df14_3 = self.sd.get_plate_info('INDUSTRY', '20190101',
                                        'CITICS.b10102')
        self.assertFalse(df14_3.empty)
        self.assertTrue(len(df14_3.columns) == 4)

    def test_get_plate_info_4(self):
        # 中信三级行业
        df14_4 = self.sd.get_plate_info('INDUSTRY', '20190101',
                                        'CITICS.b1010201')
        self.assertFalse(df14_4.empty)
        self.assertTrue(len(df14_4.columns) == 4)

    def test_get_plate_info_5(self):
        # 申万行业全部
        df14_5 = self.sd.get_plate_info('INDUSTRY', '20190702', 'SW.61')
        self.assertFalse(df14_5.empty)
        self.assertTrue(len(df14_5.columns) == 4)

    def test_get_plate_info_6(self):
        # 申万一级行业
        df14_6 = self.sd.get_plate_info('INDUSTRY', '20190702', 'SW.6102')
        self.assertFalse(df14_6.empty)
        self.assertTrue(len(df14_6.columns) == 4)

    def test_get_plate_info_7(self):
        # 申万二级行业
        df14_7 = self.sd.get_plate_info('INDUSTRY', '20190702', 'SW.610102')
        self.assertFalse(df14_7.empty)
        self.assertTrue(len(df14_7.columns) == 4)

    def test_get_plate_info_8(self):
        # 申万三级行业
        df14_8 = self.sd.get_plate_info('INDUSTRY', '20190702', 'SW.61010201')
        self.assertFalse(df14_8.empty)
        self.assertTrue(len(df14_8.columns) == 4)

    def test_get_plate_info_9(self):
        # 证监会行业全部
        df14_9 = self.sd.get_plate_info('INDUSTRY', '20191231', 'CSRC.12')
        self.assertFalse(df14_9.empty)
        self.assertTrue(len(df14_9.columns) == 4)

    def test_get_plate_info_10(self):
        # 证监会一级行业
        df14_10 = self.sd.get_plate_info('INDUSTRY', '20191231', 'CSRC.1202')
        self.assertFalse(df14_10.empty)
        self.assertTrue(len(df14_10.columns) == 4)

    def test_get_plate_info_11(self):
        # 证监会二级行业
        df14_11 = self.sd.get_plate_info('INDUSTRY', '20191231', 'CSRC.120102')
        self.assertFalse(df14_11.empty)
        self.assertTrue(len(df14_11.columns) == 4)

    def test_get_plate_info_12(self):
        # 市场板块 全部A股
        df14_12 = self.sd.get_plate_info('MARKET', '20190308', 'ALLA')
        self.assertFalse(df14_12.empty)
        self.assertTrue(len(df14_12.columns) == 2)

    def test_get_plate_info_13(self):
        # 市场板块 上海A股
        df14_13 = self.sd.get_plate_info('MARKET', '20190308', 'SHA')
        self.assertFalse(df14_13.empty)
        self.assertTrue(len(df14_13.columns) == 2)

    def test_get_plate_info_14(self):
        # 市场板块 上海A股 use_prev_name=False为最新的股票名称，默认True为指定日期时的股票名称
        df14_14 = self.sd.get_plate_info('MARKET', '20190308', 'SHA',
                                         use_prev_name=False)
        self.assertFalse(df14_14.empty)
        self.assertTrue(len(df14_14.columns) == 2)

    def test_get_plate_info_15(self):
        # 市场板块 深圳A股
        df14_15 = self.sd.get_plate_info('MARKET', '20190308', 'SZA')
        self.assertFalse(df14_15.empty)
        self.assertTrue(len(df14_15.columns) == 2)

    def test_get_plate_info_16(self):
        # 市场板块 中小板
        df14_16 = self.sd.get_plate_info('MARKET', '20190308', 'SME')
        self.assertFalse(df14_16.empty)
        self.assertTrue(len(df14_16.columns) == 2)

    def test_get_plate_info_17(self):
        # 市场板块 创业板
        df14_17 = self.sd.get_plate_info('MARKET', '20190308', 'GEM')
        self.assertFalse(df14_17.empty)
        self.assertTrue(len(df14_17.columns) == 2)

    def tearDown(self):
        pass


unittest.main(argv=['first-arg-is-ignored'], exit=False)
