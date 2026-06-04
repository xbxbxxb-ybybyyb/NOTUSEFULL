# from xquant.marketdata import MarketData
# mdp = MarketData()
# y = mdp.get_data_by_time_frame("Stock", "000950.SZ", "20170101 000001000", "20170131 235959000")
# print(y)
# y = mdp.get_data_by_time_frame("Stock", "000511.SZ", "20170201 000001000", "20170228 235959000")
# print(y)
# y = mdp.get_data_by_time_frame("Stock", "000629.SZ", "20170301 000001000", "20170331 235959000")
# print(y)
# y = mdp.get_data_by_time_frame("Stock", "601360.SH", "20180101 000001000", "20180131 235959000")
# print(y)
# y = mdp.get_data_by_time_frame("Stock", "000950.SZ", "20170101 094001000", "20170131 142800000")
# print(y)
# y = mdp.get_data_by_time_frame("Stock", "601313.SH", "20170101 000001000", "20170131 235959000")
# print(y)
from xquant.pyfile import Pyfile

py = Pyfile()

with py.open("aa/1.csv", "wb") as f:
    pass