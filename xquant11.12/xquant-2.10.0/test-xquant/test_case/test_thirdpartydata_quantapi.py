import unittest

from version_control import version_number

if version_number == 0:
    import xquant.quant as xq
else:
    import xquant.thirdpartydata.quant as xq



class TestQuantapi(unittest.TestCase):

    def test_demo(self):
        t = xq.tradingDay(20160816, 20160820)
        t1 = xq.tradingDay(20150504, 20150610, xq.FrequencyType.DAY)
        t2 = xq.tradingDay(20150504, 20160610, xq.FrequencyType.DAY, xq.DayType.MONDAY, xq.DateType.TRADINGDAYS,
                           xq.MarketType.SZ)
        t3 = xq.tradingDay(20160504, -10)
        print(t)
        print(t1)
        print(t2)
        print(t3)
        t = xq.hset(xq.PlateType.INDEX, 20160816, xq.IndexType.HS300)
        t1 = xq.hset(xq.PlateType.MARKET, 20160816, xq.MarketType.SHA)
        t2 = xq.hset(xq.PlateType.INDUSTRY, 20160916, xq.CITICS.b10101)
        print(t[0][0])
        print(t1[0][0])
        print(t2[0][0])
        stockPool = xq.hset(xq.PlateType.INDEX, 20160816, xq.IndexType.HS300)
        t = xq.stockFilter(stockPool[0][1], 20160816)
        t1 = xq.stockFilter(stockPool[0][1], 20160816, xq.StockFilterType.OPENDOWNLIMIT)
        print(t)
        print(t1)

        t = xq.hfactor(["000001.SZ", "601688.SH"], [xq.Factors.high], [20160816])
        [factorData, dateList, stkcdList] = xq.hfactor(['000001.SZ', '601988.SH'],
                                                       [xq.Factors.eps_basic, xq.Factors.equitytodebt],
                                                       [20151231, 20160331, 20160816, 20161231])
        print(t)
        print(stkcdList)

        dateList = xq.tradingDay(20161201, 20161231, xq.FrequencyType.DAY)
        t1 = xq.hfactor(['601688.SH'], xq.Factors.close, dateList)
        [factorData1, dateList1, stkcdList1] = xq.hfactor(['600000.SH', '601688.SH'],
                                                          [xq.Factors.high_min, xq.Factors.close_min],
                                                          [20160818090000, 20160818094000]);
        print(t1)
        print(stkcdList1)

        t = xq.hdf(['000001.SZ', '601688.SH'], xq.Factors.grps, [20160504, 20160703, 20161024], xq.PublishDateType.TTM)
        [factorData, dateList, stkCodeList] = xq.hdf(['000001.SZ', '601688.SH'],
                                                     [xq.Factors.grps, xq.Factors.optogr_ttm], [20160504, 20160504],
                                                     xq.PublishDateType.ACCOUNTINGDAY)
        print(t)
        print(dateList)
