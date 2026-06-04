import unittest
import time

from version_control import version_number

if version_number == 1:
    from xquant.textdata import NewsData
    from xquant.textdata import ComOpenData

    class TestNewsData(unittest.TestCase):

        def test_demo(self):
            nd = NewsData()
            data = nd.getNewsInfoByEntryTime("20180904","01:20","22:20")
            print(data)
            print(nd.getNewsInfoByStockCode('603766'))
            print(nd.getNewsInfoByStockCode('603766', ['2019', '2018']))

            data.reset_index(inplace=True)
            newsinfo = data["id"].apply(str)
            L = newsinfo.tolist()
            t1 = time.time()
            newsinfo = nd.getNewsBody(L[:10])
            print(time.time() - t1)
            print(newsinfo)
            df = nd.getNegNewsByStock('000100', ["2017", "2018"])
            print(df.head())
            df = nd.getNegNewsByStock('000100')
            print(df.head())
            df = nd.getNegNewsByTime("20190101", "20190901")
            print(df.head())


        def test_comopendata(self):
            cd = ComOpenData()
            stockcode = '000100'
            yearlist = ["2017", "2018"]
            beginTime = "20190101"
            endTime = "20190901"

            df = cd.getLawsuitByStock(stockcode)
            print(df.head())
            df = cd.getLawsuitByStock(stockcode,yearlist)
            print(df.head())

            df = cd.getLawsuitByTime(beginTime,endTime)
            print(df.head())

            df = cd.getDisHonestyRecordByStock(stockcode)
            print(df.head())
            df = cd.getDisHonestyRecordByStock(stockcode,yearlist)
            print(df.head())

            df = cd.getDisHonestyRecordByTime(beginTime, endTime)
            print(df.head())



else:
    pass
