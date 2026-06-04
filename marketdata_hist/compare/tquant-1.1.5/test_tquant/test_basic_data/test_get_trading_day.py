from tquant import BasicData
import unittest
import datetime as dt


class TestGetTradingDay(unittest.TestCase):

    def setUp(self):
        self.bd = BasicData()

    def test_get_trading_day_1(self):
        # 默认取交易日
        date_list1 = self.bd.get_trading_day('20190102', '20190110')
        self.assertTrue(len(date_list1) == 7)

    def test_get_trading_day_2(self):
        # day_type默认FRIDAY
        date_list2 = self.bd.get_trading_day('20190102', '20190210',
                                             frequency='WEEK')
        self.assertTrue(all(
            [dt.datetime.strptime(date, '%Y%m%d').weekday() + 1 == 5 for date
             in date_list2]))

    def test_get_trading_day_3(self):
        # 取每周一的日期
        date_list3 = self.bd.get_trading_day('20190102', '20190210',
                                             frequency='WEEK',
                                             day_type='MONDAY')
        self.assertTrue(all(
            [dt.datetime.strptime(date, '%Y%m%d').weekday() + 1 == 1 for date
             in date_list3]))

    def test_get_trading_day_4(self):
        # 取日历日日期
        date_list4 = self.bd.get_trading_day('20190102', '20190110',
                                             date_type='ALLDAYS')
        self.assertTrue(len(date_list4) == 9)

    def test_get_trading_day_5(self):
        # 以某个日期为起点查询后面的n个交易日期
        date_list5 = self.bd.get_trading_day('20190102', 5)
        self.assertTrue(len(date_list5) == 5)

    def test_get_trading_day_6(self):
        # 以某个日期为起点查询前面的n个交易日期
        date_list6 = self.bd.get_trading_day('20190202', -5)
        self.assertTrue(len(date_list6) == 5)

    def tearDown(self):
        pass


unittest.main(argv=['first-arg-is-ignored'], exit=False)
