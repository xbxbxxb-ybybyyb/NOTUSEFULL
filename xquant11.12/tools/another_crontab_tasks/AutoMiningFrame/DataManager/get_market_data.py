import dolphindb as ddb
import pandas as pd
from AutoMiningFrame.DataCaculation.utils.common_utils import check_date
from AutoMiningFrame.configs.local_connect import parse_connect

import configparser
import os


class FactorProvider:
    def __init__(self):
        host, port, userid, password = parse_connect()
        self.__host = host
        self.__port = port
        self.__userid = userid
        self.__password = password
        self.s = ddb.session()
        self.s.connect(host=self.__host, port=self.__port, userid=self.__userid, password=self.__password)


    def __get_market_data(self, stock, startTime, endTime, tableName):
        """
        :param stock: list类型，单标的支持string
        :param startTime: str类型，格式YYYYMMDD，如20220601
        :param endTime: str类型，格式YYYYMMDD，如20220601
        :param tableName: string类型。可查询表如下
        :return:
        """
        if isinstance(startTime, int):
            startTime = str(startTime)
        if isinstance(endTime, int):
            endTime = str(endTime)
        check_date(startTime)
        check_date(endTime)
        startTime = startTime[:4] + '.' + startTime[4:6] + '.' + startTime[6:]
        endTime = endTime[:4] + '.' + endTime[4:6] + '.' + endTime[6:]
        if isinstance(stock, str):
            stock = [stock]
        self.s.run("use DolphinFrame::DataManager")
        self.s.run(f"""data = getMarketData_Remote(stock={stock}, startTime={startTime}, endTime={endTime}, tableName=`{tableName})""")


        arrayVector_columns = self.s.run("select name from data.schema().colDefs where typeString like '%[]'")
        for col in arrayVector_columns.name:
            self.s.run(f"data.replaceColumn!(`{col}, string(data.{col}))")
        data = self.s.run("data")
        time_columns = self.s.run("select name from data.schema().colDefs where typeString=`TIME")
        for col in time_columns.name:
            data[col] = data[col].apply(lambda x: x.time())
        return data

    def get_market_data(self, stock, startTime, endTime, tableName=None, exchange=None, securityType=None, marketType=None):
        """
        原始行情、扩充行情取数接口
        表名入参有两种方式：
        1.直接入参tableName，无需入参exchange、securityType、marketType
        2.不入参tableName，需入参exchange、securityType、marketType
        :param stock: list类型，单标的支持string
        :param startTime: str类型，格式YYYYMMDD，如20220601
        :param endTime: str类型，格式YYYYMMDD，如20220601
        :param tableName: string类型。可查询表如下
        :param exchange: str，交易所。可选项'sh','sz'
        :param securityType: str，证券类型。可选项'stock','bond'
        :param marketType: str，数据类型。可选项'order'-逐笔委托；'trade'-逐笔成交，'trade_order'-还原逐笔；'tick'-3stick，'tick_enhanced'-增强3stick；'trade_enhanced'-增强trade；'tick_persec'-秒级tick
        :return:
        可查询表：
        深交所股票逐笔成交数据	sz_stock_trade
        深交所股票逐笔委托数据	sz_stock_order
        深交所股票还原逐笔数据	sz_stock_trade_order
        上交所股票逐笔成交数据	sh_stock_trade
        上交所股票逐笔委托数据	sh_stock_order
        深交所转债逐笔成交数据	sz_bond_trade
        深交所转债逐笔委托数据	sz_bond_order
        深交所转债还原逐笔数据	sz_bond_trade_order
        上交所转债逐笔委托数据	sh_bond_order
        上交所转债逐笔成交数据	sh_bond_trade
        上交所转债还原逐笔数据	sh_bond_trade_order
        深交所股票秒级tick数据	sz_stock_tick_persec
        深交所转债秒级tick数据	sz_bond_tick_persec
        上交所股票增强tick数据	sh_stock_tick_enhanced
        深交所股票增强trade数据	sz_stock_tick_enhanced
        上交所股票增强trade数据	sh_stock_trade_enhanced
        上交所股票原始tick数据	sh_stock_tick
        """
        if tableName:
            data = self.__get_market_data(stock, startTime, endTime, tableName)
        elif exchange and securityType and marketType:
            tableName = exchange + '_' + securityType + '_' + marketType
            data = self.__get_market_data(stock, startTime, endTime, tableName)
        else:
            raise Exception("""表入参支持两种形式：
                                1.只传表名tableName；
                                2.表名组合，即exchange、securityType、marketType""")
        return data


if __name__ == "__main__":
    import pandas as pd
    pd.set_option('display.max_columns', 50)
    pd.set_option('display.max_rows', 300)
    # 调整显示宽度，以便整行显示
    pd.set_option('display.width', 1000)

    fd = FactorProvider()


    # 原始行情、扩充行情取数接口
    data = fd.get_market_data(stock=["688599.SH"], startTime="20220601", endTime="20220605", tableName="sh_stock_tick")  # 原始tick
    # data = fd.get_market_data(stock=["688599.SH"], startTime="20220601", endTime="20220605", tableName="sh_stock_trade")  # 原始trade
    # data = fd.get_market_data(stock=["688029.SH"], startTime="20220601", endTime="20220605", tableName="sh_stock_tick_enhanced")  # 增强tick

    # data = fd.get_market_data(stock=["688599.SH"], startTime="20220601", endTime="20220605", exchange='sh', securityType='stock', marketType='tick')  # 原始tick
    # data = fd.get_market_data(stock=["688599.SH"], startTime="20220601", endTime="20220605", exchange='sh', securityType='stock', marketType='trade')  # 原始trade
    # data = fd.get_market_data(stock=["688599.SH"], startTime="20220601", endTime="20220605", exchange='sh', securityType='stock', marketType='tick_enhanced') # 增强tick
    print(data)
