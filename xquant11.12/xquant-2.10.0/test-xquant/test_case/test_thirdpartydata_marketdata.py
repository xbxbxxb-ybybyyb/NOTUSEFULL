import unittest
import os
from version_control import version_number
if version_number==0:
    if not os.environ.get('ENV_VERSION',False):
        from xquant.marketdata import MarketData
    else:
        from xquant.thirdpartydata.marketdata import MarketData
else:
    from xquant.thirdpartydata.marketdata import MarketData



class TestThirdpartydataMarketData(unittest.TestCase):

    def test_demo(self):
        ma = MarketData()

        # 证券委托数据查询服务： 逐笔委托查询
        df = ma.getMDOrderDataFrame("000001.SZ", "20181201090000", "20181201100000")
        print(df.head())

        # getMDOrder(htscSecurityID, startDateTime, endDateTime)
        # 证券委托数据查询服务： 逐笔委托查询
        # datas = ma.getMDOrder("000001.SZ","20181201090000","20181201100000")
        # for data in datas:
        #     print("MDDate is:{0},and OrderPrice is {1}".format(data.MDDate,data.OrderPrice))
        #     break

        # getMDTransactionDataFrame(htscSecurityID, startTime, stopTime)
        # 证券逐笔成交查询,直接返回DataFrame对象
        # df = ma.getMDTransactionDataFrame("601688.SH","20181201090000","20181201100000")
        # print(df.head())

        # getMDTransaction(htscSecurityID, startTime, stopTime)
        # 证券逐笔成交查询,返回MDTransaction的生成器
        datas = ma.getMDTransaction("601688.SH", "20181201090000", "20181201100000")
        for data in datas:
            print("TradeBuyNo is:{0},and TradePrice is {1}".format(data.TradeBuyNo, data.TradePrice))
            break

        # # 查询tick数据

        # getMDSecurityTickDataFrame(htscSecurityID, startDateTime, endDateTime, QueryType=0)
        # 证券Tick查询服务: 根据证券ID查询一段时间范围内的Tick数据，返回DataFrame对象
        # 一般tick数据
        df = ma.getMDSecurityTickDataFrame("601688.SH", "20181201090000", "20181201100000", 0)
        print(df.head())

        # 含买卖盘的tick数据
        df = ma.getMDSecurityTickDataFrame("601688.SH", "20181201090000", "20181201100000", 1)
        print(df.head())

        # getMDSecurityTick(htscSecurityID, startDateTime, endDateTime, QueryType=0)
        # 证券Tick查询服务: 根据证券ID查询一段时间范围内的Tick数据，返回返回类 MDTickRecord 的生成器
        try:
            datas = ma.getMDSecurityTick("601688.SH", "20190107090000", "20170107100000", 1)
            for data in datas:
                print("NumTrades is:{0},and TotalVolumeTrade is {1}".format(data.NumTrades, data.TotalVolumeTrade))
                break
        except Exception as e:
            print(e)

        # queryMDMaxPriceAndMinPrice(htscSecurityID, startDateTime, endDateTime)
        # 证券Tick查询服务: 根据证券ID查询其在指定范围内的最高价、最低价和成交量总和
        try:
            data = ma.queryMDMaxPriceAndMinPrice("601688.SH", "20181201090000", "20181201100000")
            for k in data:
                print("{0}: {1}".format(k, data[k]))
        except Exception as e:
            print(e)

        # queryMDTickFor1Time(htscSecurityID, queryTime)
        # 证券Tick查询服务:根据证券ID查询距离指定时间点最近的一条Tick数据
        try:
            df = ma.queryMDTickFor1Time("000001.SZ", "20181229140000")
            print(df)
        except Exception as e:
            print(e)

        # # 查询K线

        # getMDSecurityKLineDataFrame(htscSecurityID, startDateTime, endDateTime, ePlaybackExrightsType, eMarketDataType)
        # 证券K线查询服务:根据证券ID查询一段时间范围内的K线数据, 返回DataFrame对象
        df = ma.getMDSecurityKLineDataFrame("601688.SH", "20181101090000", "20181101100000", 10, 20)
        print(df.head())

        # getMDSecurityKLine(htscSecurityID, startDateTime, endDateTime, ePlaybackExrightsType, eMarketDataType)
        # 证券K线查询服务:根据证券ID查询一段时间范围内的K线数据, 返回MDKLine的生成器
        datas = ma.getMDSecurityKLine("601688.SH", "20181201090000", "20181201100000", 10, 20)
        for data in datas:
            print("OpenPx is:{0},and HighPx is {1}".format(data.OpenPx, data.HighPx))
            break

        # getMDSecurityClosePrice(htscSecurityID, startDateTime, endDateTime, ePlaybackExrightsType)
        # 证券K线查询服务:根据证券ID查询一段时间范围内的收盘价, 返回一个字典
        data = ma.getMDSecurityClosePrice("601688.SH", "20181201090000", "20181205100000", 10)
        for k, v in data.items():
            print("{0}: {1}".format(k, data[k]))

        # # 委托队列

        # getMDSecurityOrderDetailDataFrame(htscSecurityID, startDateTime, endDateTime)
        # 委托队列查询，返回DataFrame对象
        try:
            df = ma.getMDSecurityOrderDetailDataFrame("601688.SH", "20181201090000", "20181201100000")
            print(df.head())
        except Exception as e:
            print(e)

        # getMDSecurityOrderDetail(htscSecurityID, startDateTime, endDateTime)
        # 委托队列查询，返回类 MDOrder的生成器
        try:
            datas = ma.getMDSecurityOrderDetail("601688.SH", "20181201090000", "20181201100000")
            for data in datas:
                print("TotalVolumeTrade is:{0},and Buy1NumOrders is {1}".format(data.TotalVolumeTrade,
                                                                                data.Buy1NumOrders))
                break
        except Exception as e:
            print(e)

        df1 = ma.getMDSecurityRecordBySourceTypes(securityIDSource=101, securityType=2)
        df2 = ma.getMDSecurityRecordBySourceTypes(securityIDSource=102, securityType=2)
        df = df1.append(df2)
        df = df.reset_index(drop=True)
        print(df.head())

        spot_gold_HTSCSecurityID_list = ["AU99.99.SGE", "AU99.95.SGE", "AU(T+D).SGE", "MAU(T+D).SGE"]
        for i in spot_gold_HTSCSecurityID_list:
            df = ma.getMDSecurityKLineDataFrame(i, "20190903090000", "20190903100000", 10, 20)
            print(df.head())
            df = ma.getMDSecurityTickDataFrame(i, "20190903090000", "20190903100000", 0)
            print(df.head())

        df = ma.getMDSecurityTickDataFrame("510050.SH", "20171201090000", "20171201100000", 0)
        print(df.head())

        df = ma.getMDSecurityKLineDataFrame("510050.SH", "20171101090000", "20171101100000", 10, 25)
        print(df.head())