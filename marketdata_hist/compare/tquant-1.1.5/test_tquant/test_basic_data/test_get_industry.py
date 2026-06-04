from tquant import BasicData
import unittest


class TestGetIndustry(unittest.TestCase):

    def setUp(self):
        self.bd = BasicData()

    def test_get_industry_1(self):
        # 证监会行业只有2级分类
        df2_1 = self.bd.get_industry('CSRC', 0)
        self.assertFalse(df2_1.empty)
        self.assertTrue(len(df2_1.columns) == 2)

        df2_2 = self.bd.get_industry('CSRC', 1)
        self.assertFalse(df2_2.empty)
        self.assertTrue(len(df2_2.columns) == 2)

        df2_3 = self.bd.get_industry('CSRC', 2)
        self.assertFalse(df2_3.empty)
        self.assertTrue(len(df2_3.columns) == 2)

    def test_get_industry_2(self):
        # 中信行业分类
        df2_4 = self.bd.get_industry('CITICS', 0)
        self.assertFalse(df2_4.empty)
        self.assertTrue(len(df2_4.columns) == 2)

        df2_5 = self.bd.get_industry('CITICS', 1)
        self.assertFalse(df2_5.empty)
        self.assertTrue(len(df2_5.columns) == 2)

        df2_6 = self.bd.get_industry('CITICS', 2)
        self.assertFalse(df2_6.empty)
        self.assertTrue(len(df2_6.columns) == 2)

        df2_7 = self.bd.get_industry('CITICS', 3)
        self.assertFalse(df2_7.empty)
        self.assertTrue(len(df2_7.columns) == 2)

    def test_get_industry3(self):
        # 申万行业
        df2_8 = self.bd.get_industry('SW', 0)
        self.assertFalse(df2_8.empty)
        self.assertTrue(len(df2_8.columns) == 2)

        df2_9 = self.bd.get_industry('SW', 1)
        self.assertFalse(df2_9.empty)
        self.assertTrue(len(df2_9.columns) == 2)

        df2_10 = self.bd.get_industry('SW', 2)
        self.assertFalse(df2_10.empty)
        self.assertTrue(len(df2_10.columns) == 2)

        df2_11 = self.bd.get_industry('SW', 3)
        self.assertFalse(df2_11.empty)
        self.assertTrue(len(df2_11.columns) == 2)

    def tearDown(self):
        pass


unittest.main(argv=['first-arg-is-ignored'], exit=False)
