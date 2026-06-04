from tquant import BasicData
import unittest
import datetime as dt


class TestBasicData(unittest.TestCase):

    def setUp(self):
        self.bd = BasicData()

    def test_get_trading_day(self):
        # 默认取交易日
        date_list1 = self.bd.get_trading_day('20190102', '20190110')
        self.assertTrue(len(date_list1) == 7)

        # day_type默认FRIDAY
        date_list2 = self.bd.get_trading_day('20190102', '20190210', frequency='WEEK')
        self.assertTrue(all([dt.datetime.strptime(date, '%Y%m%d').weekday() + 1 == 5 for date in date_list2]))

        # 取每周一的日期
        date_list3 = self.bd.get_trading_day('20190102', '20190210', frequency='WEEK', day_type='MONDAY')
        self.assertTrue(all([dt.datetime.strptime(date, '%Y%m%d').weekday() + 1 == 1 for date in date_list3]))

        # 取日历日日期
        date_list4 = self.bd.get_trading_day('20190102', '20190110', date_type='ALLDAYS')
        self.assertTrue(len(date_list4) == 9)

        # 以某个日期为起点查询后面的n个交易日期
        date_list5 = self.bd.get_trading_day('20190102', 5)
        self.assertTrue(len(date_list5) == 5)

        # 以某个日期为起点查询前面的n个交易日期
        date_list6 = self.bd.get_trading_day('20190202', -5)
        self.assertTrue(len(date_list5) == 5)

    def test_get_industry(self):
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

    def test_get_conception(self):
        df3_1 = self.bd.get_conception('603766.SH')
        self.assertFalse(df3_1.empty)

    def tearDown(self):
        pass
