from os import path
import pandas as pd
import numpy as np

from version_control import version_number

if version_number == 0:
    from QuantFramework import Job
    from QuantFramework import Configuration
    from QuantFramework import HDFSFileHandler
    from MDCDataProvider import DataProvider as MarketData
    from QuantFramework import remote_print 
    from QuantFramework import trading_day
else:
    from xquant.compute.sparkmr import Job
    from xquant.compute.sparkmr import remote_print
    from xquant.compute.sparkmr import Configuration
    from xquant.compute.sparkmr import trading_day
    from xquant.marketdata import MarketData



class TaskMeta:
    def __init__(self, stock, date):
        self.__stock = str(stock)
        self.__date = str(date)

    def get_stock(self):
        return self.__stock

    def get_date(self):
        return self.__date



def important_hdfsfile():
    if version_number == 0:
        from xquant.pyfile import Pyfile
        hf = Pyfile()
    else:
        from xquant.xqutils.xqfile import HDFSFile
        hf = HDFSFile()

    remote_print(hf.listdir(""))
    remote_print(hf.getAbsolutePath(""))
    
    remote_print("============================读写csv文件============================")
    df1 = pd.DataFrame(
        np.arange(16).reshape((4, 4)),
        index=['a', 'b', 'c', 'd'], columns=['one', 'two', 'three', 'four'])
    remote_print(df1.head())
    # hf.create("hy/t.csv")
    hf.write_csvfile("hy/t.csv", df1)

    df2 = hf.read_csvfile("hy/t.csv")
    remote_print(df2.head())
    remote_print("*"*30+"spark hdfsfile ok!"+"*"*30)
    assert hf.getAbsolutePath("test")=="/analysis/xquant/test"

    
def important_marketdata():
    from xquant.marketdata import MarketData
    mdp = MarketData()
    
    df = mdp.get_data_by_year_month("Stock", "000001.SZ", "201804", ["3"], sort_by_receive_time=True)
    remote_print(df.head())
    df2 = mdp.get_data_by_date("Stock", "000001.SZ", "20180301", ["2", "3"])
    remote_print(df2.head())
    df3 = mdp.get_data_by_time_frame("Order", "000001.SZ", "20180301 093000000", "20180305 150000250")
    remote_print(df3.head())
    df4 = mdp.get_data_by_year_month("Kline1M4ZT", "000001.SZ", "201804")
    remote_print(df4.head())
    remote_print("*"*30+"spark mdp ok!"+"*"*30)
    
    
def important_quantapi():
    from version_control import version_number
    if version_number == 0:
        import xquant.quant.QuantAPI as xq
    else:
        import xquant.thirdpartydata.quant as xq

    t = xq.tradingDay(20160816, 20160820)
    t1 = xq.tradingDay(20150504, 20150610, xq.FrequencyType.DAY)
    t2 = xq.tradingDay(20150504, 20160610, xq.FrequencyType.DAY, xq.DayType.MONDAY, xq.DateType.TRADINGDAYS,
                       xq.MarketType.SZ)
    t3 = xq.tradingDay(20160504, -10)
    remote_print(t)
    remote_print(t1)
    remote_print(t2)
    remote_print(t3)
    t = xq.hset(xq.PlateType.INDEX, 20160816, xq.IndexType.HS300)
    t1 = xq.hset(xq.PlateType.MARKET, 20160816, xq.MarketType.SHA)
    t2 = xq.hset(xq.PlateType.INDUSTRY, 20160916, xq.CITICS.b10101)
    remote_print(t[0][0])
    remote_print(t1[0][0])
    remote_print(t2[0][0])
    stockPool = xq.hset(xq.PlateType.INDEX, 20160816, xq.IndexType.HS300)
    t = xq.stockFilter(stockPool[0][1], 20160816)
    t1 = xq.stockFilter(stockPool[0][1], 20160816, xq.StockFilterType.OPENDOWNLIMIT)
    remote_print(t)
    remote_print(t1)

    t = xq.hfactor(["000001.SZ", "601688.SH"], [xq.Factors.high], [20160816])
    [factorData, dateList, stkcdList] = xq.hfactor(['000001.SZ', '601988.SH'],
                                                   [xq.Factors.eps_basic, xq.Factors.equitytodebt],
                                                   [20151231, 20160331, 20160816, 20161231])
    remote_print(t)
    remote_print(stkcdList)

    dateList = xq.tradingDay(20161201, 20161231, xq.FrequencyType.DAY)
    t1 = xq.hfactor(['601688.SH'], xq.Factors.close, dateList)
    [factorData1, dateList1, stkcdList1] = xq.hfactor(['600000.SH', '601688.SH'],
                                                      [xq.Factors.high_min, xq.Factors.close_min],
                                                      [20160818090000, 20160818094000]);
    remote_print(t1)
    remote_print(stkcdList1)

    t = xq.hdf(['000001.SZ', '601688.SH'], xq.Factors.grps, [20160504, 20160703, 20161024], xq.PublishDateType.TTM)
    [factorData, dateList, stkCodeList] = xq.hdf(['000001.SZ', '601688.SH'],
                                                 [xq.Factors.grps, xq.Factors.optogr_ttm], [20160504, 20160504],
                                                 xq.PublishDateType.ACCOUNTINGDAY)
    remote_print(t)
    remote_print(dateList)
    remote_print("*"*30+"spark quantapi ok!"+"*"*30)
     
def important_io():    

    from version_control import version_number
    if version_number == 0:
        from xquant.multifactor.IO.IO import str_date_parser,read_data
    else:
        from xquant.thirdpartydata.multifactor.IO import str_date_parser,read_data
    
    remote_print(str_date_parser('20190115'))
            
    alt = "universe_complete"
    df = read_data([20131115,20131118],alt=alt)
    remote_print(df.head())
    
    remote_print("*"*30+"spark IO ok!"+"*"*30)


def important_factordata():
    from xquant.factordata import FactorData
    remote_print("============================更新因子============================")
    s = FactorData()
    high_list = []
    for i in range(1, 10):
        high_list.append("high" + str(i))
    d1 = {
        "time": ["20190325"],
    }
    for i in high_list:
        d1[i] = [9895]
    df1 = pd.DataFrame(d1)
    df1.set_index("time", inplace=True)
    remote_print(s.update_factor_value("xx_high117", df1, "SH001", "20190325"))
    # s.remove_factor_value("xx_high117", "SH001", "20190325", ["high1", "high2"])

    remote_print("============================获取个人、行情、财务分析因子（2018年）============================")
    high_df = s.get_factor_value("xx_high117", "SH001", "20190325", high_list)
    remote_print(high_df.head())

    remote_print("============================查询因子元数据============================")
    date_list = s.search_by_date("xx_high117", "20190325", ["SH001", "SH002"])
    remote_print(date_list)
    date_list = s.search_by_stock("xx_high117", "SH001", ["20190326", "20190327", "20190328", "20190325"])
    remote_print(date_list)
    factor_list = s.search_by_stock_date("xx_high117", "SH001", "20190325", ["high2"])
    remote_print(factor_list)
    tdate_two = s.search_by_stock_factor("xx_high117", "SH001", "high3", ["20190325"])
    remote_print(tdate_two)
    
    remote_print("============================更新因子============================")
    high_list = []
    for i in range(1, 10):
        high_list.append("high" + str(i))
    d1 = {
        "time": ["20190325"],
    }
    for i in high_list:
        d1[i] = [9895]
    df1 = pd.DataFrame(d1)
    df1.set_index("time", inplace=True)
    remote_print(s.update_factor_value("xx_high117", df1, "SH001", "20190325"))
    # s.remove_factor_value("xx_high117", "SH001", "20190325", ["high1", "high2"])

    

class sparkmrDemo:
    def __init__(self):
        # 并行化作业的名称
        self.__app_name = "sparkmrDemo"
        # 并行化作业的输出结果目录，该目录是HDFS上的目录，013150是用户工号
        self.__dst_dir = "013150/sparkmrDemo_Output"
        # 设置工程代码目录，工程代码目录指的是该程序代码的目录
        self.__env_dir = path.dirname(path.abspath(__file__))

    def start(self):
        stock_list = ['600587.SH', '600588.SH']
        date_list = trading_day(20181201, 20181231)
        taskmeta_list = []
        for stock in stock_list:
            for date in date_list:
                taskmeta_list.append(TaskMeta(stock, date))
        config = Configuration()
        config.set_app_name(self.__app_name)
        config.set_dst_dir(self.__dst_dir)
        config.set_env_dir(self.__env_dir)
        config.set_executor_instances("10")
        job = Job(config, mode="OverWrite")
        job.add_tasks(taskmeta_list)
        job.set_func(self.func)
        job.start()

    def func(self, context, taskmeta):
        stock = taskmeta.get_stock()
        date = taskmeta.get_date()
        mdp = MarketData(context.get_hdfs())
        df = mdp.get_data_by_date('Stock', stock, date)
        context.save_as_pickle(df, '{}.pickle'.format(stock))
        
        important_hdfsfile()
        important_marketdata()
#        important_quantapi()
        # important_io()
        #important_factordata()
