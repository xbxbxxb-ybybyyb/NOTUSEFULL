import unittest
from version_control import version_number

if version_number==1:
    from xquant.marketdata import MarketData
else:
    from MDCDataProvider import DataProvider as MarketData



class TestMarketData(unittest.TestCase):

    def test_demo(self):
        mdp = MarketData()
        df = mdp.get_data_by_year_month("Stock", "000001.SZ", "201804", ["3"], sort_by_receive_time=True)
        print(df.head())
        df2 = mdp.get_data_by_date("Stock", "000001.SZ", "20180301", ["2", "3"])
        print(df2.head())
        df3 = mdp.get_data_by_time_frame("Order", "000001.SZ", "20180301 093000000", "20180305 150000250")
        print(df3.head())
        df4 = mdp.get_data_by_year_month("Kline1M4ZT", "000001.SZ", "201804")
        print(df4.head())
