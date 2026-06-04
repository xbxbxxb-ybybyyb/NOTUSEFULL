import re
import grpc
import pandas
import numpy as np
from .proto import IMDTransactionService_pb2
from .proto import IMDTransactionService_pb2_grpc
from .proto import MDTransactionRecord_pb2
from .proto import IMDTickService_pb2
from .proto import IMDTickService_pb2_grpc
from .proto import IMDKLineService_pb2
from .proto import IMDKLineService_pb2_grpc
from .proto import IMDOrderService_pb2
from .proto import IMDOrderService_pb2_grpc
from .proto import IMDConstantService_pb2_grpc
from .proto import IMDConstantService_pb2
from .proto import IMDRealTimeService_pb2
from .proto import IMDRealTimeService_pb2_grpc
from enum import Enum 
from .attrNames import SecurityTypeName
from .mdRecord import *
from .setGrpcPath import *
from .setChannel import *
from xquant1.utils import statisticLog


# global md_channels


#返回行情中心查询时的错误信息。
class MarketDataQueryError(Exception):
    def __init__(self,insightError):
        self.errorCode = insightError.errorCode
        self.message = insightError.message
    
    def __str__(self):
        return ("errorCode: {0}    message: {1}".format(self.errorCode,self.message))



class MarketData(object):
    """获取行情数据

    | 实现了以下服务：证券逐笔成交查询、证券Tick查询服务、证券k线查询服务

    :注意: 行情数据时间范围限制如下

        - 1. 分钟K线最长查询时间为7天；
        - 2. 日K线最长查询时间为365天；
        - 3. 逐笔成交最长查询时间为1天；
        - 4. 逐笔委托最长查询时间为1天；
        - 5. Tick数据最长查询时间为1天
        - 6. 委托队列最长查询时间为1天

    """
    
    @statisticLog('marketdata')
    def __init__ (self):
        channel = choose_channel(md_channels)                          #采用官方的grpc服务
        self._channel = grpc.insecure_channel(channel)
        #target = "zookeeper:///com.htsc.mdc.hawkeye.model.gservice.IMDTickService"  #采用zk服务治理
        #self._channel = grpc.insecure_channel(target)
        self._timeout = 180

    #查询证券逐笔成交当前的接口为   
    #查询请求包含三个参数：华泰证券ID（由证券ID和其所在市场组成，示例："601688.SH"）、开始时间、结束时间，其中时间格式为yyyyMMddHHmmss。
    @statisticLog('marketdata')
    def getMDTransaction(self,htscSecurityID,startTime,stopTime):
        """ 证券逐笔成交查询,返回MDTransaction的生成器

        :param htscSecurityID: 华泰证券ID，如："601688.SH"
        :type htscSecurityID: string
        :param startTime: 开始时间，格式为yyyyMMddHHmmss
        :type startTime: string
        :param stopTime: 结束时间，格式为yyyyMMddHHmmss
        :type stopTime: string
        :returns: MDTransactionRecord 类的实例
        :rtype: generator

        :注意:查询最长时间跨度为一天

        """
        
        IMDTS_stub = IMDTransactionService_pb2_grpc.IMDTransactionServiceStub(self._channel)
        MDRequsst = IMDTransactionService_pb2.MDTransactionTimeOrderRpcRequest(
            htscSecurityID=htscSecurityID, startTime=startTime, stopTime=stopTime, ascOrder=True)
        IMDTSresponses = IMDTS_stub.getMDTransactionByTimeOrder(MDRequsst,self._timeout)
        for response in IMDTSresponses:
            if response.isSuccess :
                if response.result is not None and response.result.marketDataType == 2 :
                    m = response.result.mdTransaction
                    #return m
                    yield MDTransactionRecord(m)
            else :
                if response.insightErrorContext.errorCode != 3 :
                    raise MarketDataQueryError(response.insightErrorContext)

    @statisticLog('marketdata')
    def getMDTransactionDataFrame(self,htscSecurityID,startTime,stopTime):
        """证券逐笔成交查询,直接返回DataFrame对象

        :param htscSecurityID: 华泰证券ID，如："601688.SH"
        :type htscSecurityID: string
        :param startTime: 开始时间，格式为yyyyMMddHHmmss
        :type startTime: string
        :param stopTime: 结束时间，格式为yyyyMMddHHmmss
        :type stopTime: string
        :returns: pandas.DataFrame

        :注意:查询最长时间跨度为一天

        """
        
        IMDTS_stub = IMDTransactionService_pb2_grpc.IMDTransactionServiceStub(self._channel)
        MDRequsst = IMDTransactionService_pb2.MDTransactionTimeOrderRpcRequest(
            htscSecurityID=htscSecurityID, startTime=startTime,stopTime=stopTime,ascOrder=True)
        IMDTSresponses = IMDTS_stub.getMDTransactionByTimeOrder(MDRequsst,self._timeout)
        AttributeNames = SecurityTypeName.MDTransactionAttrNames.copy()
        results = []
        for response in IMDTSresponses:
            if response.isSuccess :
                if response.result is not None and response.result.marketDataType == 2 :
                    m = response.result.mdTransaction
                    result = []
                    for attr in AttributeNames:
                        if hasattr(m,attr):
                            result.append(getattr(m,attr))
                    results.append(result)
            else :
                if response.insightErrorContext.errorCode != 3 :
                    raise MarketDataQueryError(response.insightErrorContext) #response.insightErrorContext
        df = pandas.DataFrame(results,columns=AttributeNames)
        return df
    
    
    
    #根据证券ID查询其在指定范围内的最高价、最低价和成交量总和
    @statisticLog('MarketData')
    def queryMDMaxPriceAndMinPrice(self,htscSecurityID,startDateTime,endDateTime):
        """证券Tick查询服务: 根据证券ID查询其在指定范围内的最高价、最低价和成交量总和

        :param htscSecurityID: 华泰证券ID，如："601688.SH"
        :type htscSecurityID: string
        :param startDateTime: 开始时间，格式为yyyyMMddHHmmss，示例：20170311090000
        :type startDateTime: string
        :param endDateTime: 结束时间，格式为yyyyMMddHHmmss，示例：20170321113000
        :type endDateTime: string
        :returns: 返回一个字典，keys为：isSuccess(请求是否成功) ,insightErrorContext(错误信息), maxPrice(最高价)，minPrice(最低价),totalVolumeTrade( 成交总量（手数）)
            如果无数据，则返回None
        :rtype: dict

        """
        
        IMDTS_stub = IMDTickService_pb2_grpc.IMDTickServiceStub(self._channel)
        MDRequsst = IMDTickService_pb2.MDTickMaxPriceAndMinPriceRequest(htscSecurityID=htscSecurityID, startDateTime=startDateTime,endDateTime=endDateTime)
        response = IMDTS_stub.queryMDMaxPriceAndMinPrice(MDRequsst,self._timeout)
        
        if response.isSuccess:
            results = {"maxPrice":response.maxPrice,"minPrice":response.minPrice,"totalVolumeTrade":response.totalVolumeTrade} 
            return results
        else:
            if response.insightErrorContext.errorCode != 3 :
                raise MarketDataQueryError(response.insightErrorContext)    
            else :
                return None

    @statisticLog('thirdpartydata', 'MarketData')
    def getMDSecurityKLine(self,htscSecurityID,startDateTime,endDateTime,ePlaybackExrightsType,eMarketDataType):
        """证券K线查询服务:根据证券ID查询一段时间范围内的K线数据, 返回MDKLine的生成器

        :param htscSecurityID: 华泰证券ID，如："601688.SH"
        :type htscSecurityID: string
        :param startDateTime: 开始时间，格式为yyyyMMddHHmmss，示例：20170911090000
        :type startDateTime: string
        :param endDateTime: 结束时间，格式为yyyyMMddHHmmss，示例：20170911100000
        :type endDateTime: string
        :param ePlaybackExrightsType: 除权类型
        :type ePlaybackExrightsType: int
        :param eMarketDataType: k线时间间隔类型
        :type eMarketDataType: int
        :returns: 类 MDKLine 的generator

        :注意:

            - 分钟K线最长查询时间为7天；
            - 日K线最长查询时间为365天；
            - 除权类型有三种： 10 - 不复权;  11 - 向前复权;  12 - 向后复权
            - k线时间间隔类型有六种：20 - 1分钟K线;  21 - 5分钟K线;  22 - 15分钟K线;  23 - 30分钟K线;  24 - 60分钟K线;  25 - 日K线;
            - 目前提供了1分钟K线和日K线

        """
        
        IMDTS_stub = IMDKLineService_pb2_grpc.IMDKLineServiceStub(self._channel)
        MDRequsst = IMDKLineService_pb2.MDKLineTimeOrderRpcRequest(htscSecurityID=htscSecurityID, startDateTime=startDateTime,endDateTime=endDateTime,
                                                  ePlaybackExrightsType =ePlaybackExrightsType,eMarketDataType=eMarketDataType,ascOrder=True)
        response = IMDTS_stub.getMDSecurityKLineByTimeOrder(MDRequsst,self._timeout)
        if response.isSuccess :
            for re in response.result:
                yield MDKLine(re.mdKLine)
        else:
            if response.insightErrorContext.errorCode != 3 :
                raise MarketDataQueryError(response.insightErrorContext)

    @statisticLog('thirdpartydata', 'MarketData')
    def getMDSecurityKLineDataFrame(self,htscSecurityID,startDateTime,endDateTime,ePlaybackExrightsType,eMarketDataType):
        """证券K线查询服务:根据证券ID查询一段时间范围内的K线数据, 返回MDKLine的生成器

        :param htscSecurityID: 华泰证券ID，如："601688.SH"
        :type htscSecurityID: string
        :param startDateTime: 开始时间，格式为yyyyMMddHHmmss，示例：20170911090000
        :type startDateTime: string
        :param endDateTime: 结束时间，格式为yyyyMMddHHmmss，示例：20170911100000
        :type endDateTime: string
        :param ePlaybackExrightsType: 除权类型
        :type ePlaybackExrightsType: int
        :param eMarketDataType: k线时间间隔类型
        :type eMarketDataType: int
        :returns: pandas.DataFrame

        :注意:
        
            - 分钟K线最长查询时间为7天；
            - 日K线最长查询时间为365天；
            
        :除权类型有三种:

            - 10 - 不复权
            - 11 - 向前复权
            - 12 - 向后复权

        :k线时间间隔类型有六种:

            - 20 1分钟K线
            - 21 5分钟K线
            - 22  15分钟K线
            - 23  30分钟K线
            - 24  60分钟K线
            - 25  日K线

        | 目前提供了1分钟K线和日K线

        """
        import re
        IMDTS_stub = IMDKLineService_pb2_grpc.IMDKLineServiceStub(self._channel)
        MDRequsst = IMDKLineService_pb2.MDKLineTimeOrderRpcRequest(htscSecurityID=htscSecurityID, startDateTime=startDateTime,endDateTime=endDateTime,
                                                  ePlaybackExrightsType =ePlaybackExrightsType,eMarketDataType=eMarketDataType,ascOrder=True)
        response = IMDTS_stub.getMDSecurityKLineByTimeOrder(MDRequsst,self._timeout)
        if response.isSuccess == False and response.insightErrorContext.errorCode != 3:
            raise MarketDataQueryError(response.insightErrorContext)
        
        clo_name = SecurityTypeName.MDKLineAttrNames.copy()
        results = []
        spot_gold_HTSCSecurityID_list = ["AU99.99.SGE","AU99.95.SGE","AU(T+D).SGE","MAU(T+D).SGE"]
        if htscSecurityID in spot_gold_HTSCSecurityID_list:
            clo_name = SecurityTypeName.MDSpotAttNames.copy()
        if re.findall("^51\S{4}.SH$",htscSecurityID) or re.findall("^15\S{4}.SZ$",htscSecurityID):
            clo_name = SecurityTypeName.MDFundAttNames.copy()
        if response.isSuccess == True:
            for re in response.result:
                result = []
                for attr in clo_name:
                    mdrecord = re.mdKLine
                    if hasattr(mdrecord,attr):
                        result.append(getattr(mdrecord,attr))
                    else:
                        result.append(None)
                results.append(result)
        df = pandas.DataFrame(results,columns=clo_name)
        return df

    @statisticLog('thirdpartydata', 'MarketData')
    def getMDSecurityClosePrice(self,htscSecurityID,startDateTime,endDateTime,ePlaybackExrightsType):
        """证券K线查询服务:根据证券ID查询一段时间范围内的收盘价, 返回一个字典

        :param htscSecurityID: 华泰证券ID，如："601688.SH"
        :type htscSecurityID: string
        :param startDateTime: 开始时间，格式为yyyyMMddHHmmss，示例：20170911090000
        :type startDateTime: string
        :param endDateTime: 结束时间，格式为yyyyMMddHHmmss，示例：20170911100000
        :type endDateTime: string
        :param ePlaybackExrightsType: 除权类型
        :type ePlaybackExrightsType: int
        :returns: 一个字典, 如果无数据,则返回None

        :除权类型有三种:

            - 10  不复权
            - 11  向前复权
            - 12  向后复权

        """
        
        IMDTS_stub = IMDKLineService_pb2_grpc.IMDKLineServiceStub(self._channel)
        MDRequsst = IMDKLineService_pb2.MDKLineRpcRequest(htscSecurityID=htscSecurityID, startDateTime=startDateTime,endDateTime=endDateTime,
                                                  ePlaybackExrightsType =ePlaybackExrightsType)
        response = IMDTS_stub.getMDSecurityClosePrice(MDRequsst,self._timeout)
        if response.isSuccess == False:
            if response.insightErrorContext.errorCode != 3 :
                raise MarketDataQueryError(response.insightErrorContext)
            else:
                return None
        re = response.result
        results = {}
        for k,v in re.items():
            results[k] = v
        return results

    @statisticLog('thirdpartydata', 'MarketData')
    def getMDSecurityTickDataFrame(self,htscSecurityID,startDateTime,endDateTime,QueryType=0):
        """证券Tick查询服务: 根据证券ID查询一段时间范围内的Tick数据

        :param htscSecurityID: 华泰证券ID，如："601688.SH"
        :type htscSecurityID: string
        :param startDateTime: 开始时间，格式为yyyyMMddHHmmss，示例：20170311090000
        :type startDateTime: string
        :param endDateTime: 结束时间，格式为yyyyMMddHHmmss，示例：20170321113000
        :type endDateTime: string
        :param QueryType: 查询类型，0表示一般Tick数据，1表示包含买卖盘的tick数据，默认值为0
        :type QueryType: int
        :returns: pandas.DataFrame

        :注意:    查询最长时间跨度为一天

        """
        #Tick级别有五档， 1 - 第一级别Tick，最为精简； 2 - 第二级别Tick； 3 - 第三级别Tick， 4 - 第四级别Tick， 5 - 第五级别Tick，全量Tick
        
        if QueryType == 0:
            eMDTickLevel = 1
        else:
            eMDTickLevel = 5

        IMDTS_stub_tick = IMDTickService_pb2_grpc.IMDTickServiceStub(self._channel)
        MDRequsst = IMDTickService_pb2.MDTickTimeOrderRpcRequest(htscSecurityID=htscSecurityID,
                                                                 startDateTime=startDateTime, endDateTime=endDateTime,
                                                                 eMDTickLevel=eMDTickLevel, ascOrder=True)
        responses = IMDTS_stub_tick.getMDSecurityTickByTimeOrder(MDRequsst,self._timeout)
        results = []
        AttributeNames = SecurityTypeName.MDTickAttrNames.copy()
#         for re in responses:
#             return re
        i = 0
        spot_gold_HTSCSecurityID_list = ["AU99.99.SGE", "AU99.95.SGE", "AU(T+D).SGE", "MAU(T+D).SGE"]
        if htscSecurityID in spot_gold_HTSCSecurityID_list:
            for response in responses:
                if response.isSuccess:
                    mdrecord = response.result.ListFields()[4][1]
                    # print(mdrecord)
                    if i == 0:
                        name = response.result.ListFields()[4][0].name
                        if name != "mdSpot":
                            raise Exception("错误的返回类型:%s!"%name)
                        AttributeNames = SecurityTypeName.MDSpotAttNames.copy()
                    result = []
                    for attr in AttributeNames:
                        if hasattr(mdrecord, attr):
                            result.append(getattr(mdrecord, attr))
                        else:
                            result.append(None)
                    i = i + 1
                    results.append(result)
                else:
                    if response.insightErrorContext.errorCode != 2 : #No tick record found
                        raise MarketDataQueryError(response.insightErrorContext)
        elif re.findall("^51\S{4}.SH$",htscSecurityID) or re.findall("^15\S{4}.SZ$",htscSecurityID):
            for response in responses:
                if response.isSuccess:
                    mdrecord = response.result.ListFields()[4][1]
                    # print(mdrecord)
                    if i == 0:
                        name = response.result.ListFields()[4][0].name
                        if name != "mdFund":
                            raise Exception("错误的返回类型:%s!"%name)
                        if QueryType == 0:  # 一般的基金数据
                            AttributeNames = SecurityTypeName.MDFundAttNames.copy()
                        else:  # 含买基金的期货数据
                            AttributeNames = SecurityTypeName.getMDTickFundAttrNames().copy()
                    result = []
                    for attr in AttributeNames:
                        if hasattr(mdrecord, attr):
                            result.append(getattr(mdrecord, attr))
                        else:
                            result.append(None)
                    i = i + 1
                    results.append(result)
                else:
                    if response.insightErrorContext.errorCode != 2 : #No tick record found
                        raise MarketDataQueryError(response.insightErrorContext)
        else:
            for response in responses:
                if response.isSuccess:
                    mdrecord = response.result.ListFields()[4][1]  ##注意此处默认取出的是第五个
                    if i == 0:
                        name = response.result.ListFields()[4][0].name
                        if name == "mdFuture":  #类型是期货
                            if QueryType == 0:   #一般的期货数据
                                 AttributeNames = SecurityTypeName.MDTickFuturesAttrNames.copy()
                            else:               #含买卖盘的期货数据
                                AttributeNames = SecurityTypeName.geMDTickABFuturesAttrNames().copy()
                        elif name == "mdIndex":  #类型是指数，则没有买卖盘的区别
                            AttributeNames = SecurityTypeName.MDTickAttrNames.copy()
                        else:                    #类型是股票、债券、基金、权证、期权
                            if QueryType == 0:   #一般tick数据
                                AttributeNames = SecurityTypeName.MDTickAttrNames.copy()
                            else:              #含买卖盘的tick数据
                                AttributeNames = SecurityTypeName.getMDTickABAttrNames().copy()

                    result = []
                    for attr in AttributeNames:
                        if hasattr(mdrecord,attr):
                            result.append(getattr(mdrecord,attr))
                        else:
                            result.append(None)
                    i = i+1
                    results.append(result)
                    #return(response.result)
                else:
                    if response.insightErrorContext.errorCode != 2 : #No tick record found
                        raise MarketDataQueryError(response.insightErrorContext)
        df = pandas.DataFrame(results,columns=AttributeNames)
        return df

    @statisticLog('thirdpartydata', 'MarketData')
    def getMDSecurityTick(self,htscSecurityID,startDateTime,endDateTime,QueryType=0):
        """证券Tick查询服务: 根据证券ID查询一段时间范围内的Tick数据

        :param htscSecurityID: 华泰证券ID，如："601688.SH"
        :type htscSecurityID: string
        :param startDateTime: 开始时间，格式为yyyyMMddHHmmss，示例：20170311090000
        :type startDateTime: string
        :param endDateTime: 结束时间，格式为yyyyMMddHHmmss，示例：20170321113000
        :type endDateTime: string
        :param QueryType: 查询类型，0表示一般Tick数据，1表示包含买卖盘的tick数据，默认值为0
        :type QueryType: int
        :returns: 类 MDTickRecord 的generator

        :注意:    查询最长时间跨度为一天

        """
        #Tick级别有五档， 1 - 第一级别Tick，最为精简； 2 - 第二级别Tick； 3 - 第三级别Tick， 4 - 第四级别Tick， 5 - 第五级别Tick，全量Tick
        
        if QueryType == 0:
            eMDTickLevel = 1
        else:
            eMDTickLevel = 5
            
        IMDTS_stub = IMDTickService_pb2_grpc.IMDTickServiceStub(self._channel)
        MDRequsst = IMDTickService_pb2.MDTickTimeOrderRpcRequest (htscSecurityID=htscSecurityID, startDateTime=startDateTime,endDateTime=endDateTime,eMDTickLevel=eMDTickLevel,ascOrder=True)
        responses = IMDTS_stub.getMDSecurityTickByTimeOrder(MDRequsst,self._timeout)
        results = []
        AttributeNames = SecurityTypeName.MDTickAttrNames.copy()
#         for re in responses:
#             return re
        i = 0
        for response in responses:
            if response.isSuccess:
                mdrecord = response.result.ListFields()[4][1]  ##注意此处默认取出的是第五个
                if i == 0:
                    name = response.result.ListFields()[4][0].name 
                    i = i+1
                    if name == "mdFuture":  #类型是期货
                        typeid = 1
                    elif name == "mdIndex":  #类型是指数，则没有买卖盘的区别
                        typeid = 2
                    else:                    #类型是股票、债券、基金、权证、期权
                        typeid = 0
                        
                yield(MDTickRecord(mdrecord,typeid,QueryType))
            else:
                if response.insightErrorContext.errorCode != 3 :
                    raise MarketDataQueryError(response.insightErrorContext)

    @statisticLog('thirdpartydata', 'MarketData')
    def queryMDTickFor1Time(self,htscSecurityID,queryTime):
        """证券Tick查询服务:根据证券ID查询距离指定时间点最近的一条Tick数据

        :param htscSecurityID: 华泰证券ID，如："601688.SH"
        :type htscSecurityID: string
        :param queryTime: 查询时间，格式为yyyyMMddHHmmss，示例：20170911090000
        :type queryTime: string
        :returns: pandas.DataFrame

        """
        
        IMDTS_stub = IMDTickService_pb2_grpc.IMDTickServiceStub(self._channel)
        MDRequsst = IMDTickService_pb2.MDTickFor1TimeRequest(htscSecurityID=htscSecurityID,queryTime=queryTime)
        response = IMDTS_stub.queryMDTickFor1Time(MDRequsst,self._timeout)
        if response.isSuccess == False:
            if response.insightErrorContext.errorCode != 3 :
                raise MarketDataQueryError(response.insightErrorContext)
            
        clo_name = SecurityTypeName.MDKLineAttrNames.copy()
        results = []
        if response.isSuccess == True:
            result = []
            mdrecord = mdrecord = response.result.ListFields()[4][1]  ##注意此处默认取出的是第五个
            if response.result.ListFields()[4][0].name == "mdFuture":
                clo_name = SecurityTypeName.MDTickFuturesAttrNames.copy()
            for attr in clo_name:           
                if hasattr(mdrecord,attr):
                    result.append(getattr(mdrecord,attr))
                else:
                    result.append(None)
            results.append(result)
        df = pandas.DataFrame(results,columns=clo_name)
        return df

    @statisticLog('thirdpartydata', 'MarketData')
    def getMDOrderDataFrame(self,htscSecurityID,startDateTime,endDateTime):
        """证券委托数据查询服务： 逐笔委托查询

        :param htscSecurityID: 华泰证券ID，如："000001.SZ"
        :type htscSecurityID: string
        :param startDateTime: 开始时间，格式为yyyyMMddHHmmss
        :type startDateTime: string
        :param endDateTime: 结束时间，格式为yyyyMMddHHmmss
        :type endDateTime: string
        :returns: pandas.DataFrame

        :注意:

            - 查询最长时间跨度为一天
            - 目前只提供了深交所的数据

        """
        
        IMDTS_stub = IMDOrderService_pb2_grpc.IMDOrderServiceStub(self._channel)
        MDRequsst = IMDOrderService_pb2.MDOrderTimeOrderRpcRequest(htscSecurityID=htscSecurityID,startTime=startDateTime,stopTime=endDateTime,ascOrder=True )
        IMDTSresponses = IMDTS_stub.getMDOrderByTimeOrder(MDRequsst,self._timeout)
        AttributeNames = SecurityTypeName.MDOrderAttrNames.copy()
        results = []
        for response in IMDTSresponses:
            if response.isSuccess :
                if response.result :
                    m = response.result.mdOrder
                    result = []
                    for attr in AttributeNames:
                        if hasattr(m,attr):
                            result.append(getattr(m,attr))
                            #print(m)
                    results.append(result)
            else :
                if response.insightErrorContext.errorCode != 3 :
                    raise MarketDataQueryError(response.insightErrorContext)
        df = pandas.DataFrame(results,columns=AttributeNames)
        return df

    @statisticLog('thirdpartydata', 'MarketData')
    def getMDOrder(self,htscSecurityID,startDateTime,endDateTime):
        """证券委托数据查询服务： 逐笔委托查询

        :param htscSecurityID: 华泰证券ID，如："000001.SZ"
        :type htscSecurityID: string
        :param startDateTime: 开始时间，格式为yyyyMMddHHmmss
        :type startDateTime: string
        :param endDateTime: 结束时间，格式为yyyyMMddHHmmss
        :type endDateTime: string
        :returns: 类 MDOrder 的generator

        :注意:

            - 查询最长时间跨度为一天
            - 目前只提供了深交所的数据

        """
        
        IMDTS_stub = IMDOrderService_pb2_grpc.IMDOrderServiceStub(self._channel)
        MDRequsst = IMDOrderService_pb2.MDOrderTimeOrderRpcRequest(htscSecurityID=htscSecurityID,startTime=startDateTime,stopTime=endDateTime,ascOrder=True )
        IMDTSresponses = IMDTS_stub.getMDOrderByTimeOrder(MDRequsst,self._timeout)
        AttributeNames = SecurityTypeName.MDOrderAttrNames.copy()
        results = []
        for response in IMDTSresponses:
            if response.isSuccess :
                if response.result :
                    m = response.result.mdOrder
                    yield MDOrder(m)
            else :
                if response.insightErrorContext.errorCode != 3 :
                    raise MarketDataQueryError(response.insightErrorContext)

    @statisticLog('thirdpartydata', 'MarketData')
    def getMDSecurityOrderDetail(self,htscSecurityID,startDateTime,endDateTime):
        """委托队列查询


        :param htscSecurityID: 华泰证券ID，如："601688.SH"
        :type htscSecurityID: string
        :param startDateTime: 开始时间，格式为yyyyMMddHHmmss
        :type startDateTime: string
        :param endDateTime: 结束时间，格式为yyyyMMddHHmmss
        :type endDateTime: string
        :returns: 类 MDOrder 的generator

        :注意:    查询最长时间跨度为一天

        """
        
        IMDTS_stub = IMDTickService_pb2_grpc.IMDTickServiceStub(self._channel)
        MDRequsst = IMDTickService_pb2.MDTickOrderDetailTimeOrderRpcRequest (htscSecurityID=htscSecurityID, startDateTime=startDateTime,endDateTime=endDateTime,ascOrder=True)
        responses = IMDTS_stub.getMDSecurityOrderDetailByTimeOrder(MDRequsst,self._timeout)
        results = []
        AttributeNames = SecurityTypeName.MDTickAttrNames.copy()
        for response in responses:
            if response.isSuccess:
                mdrecord = response.result.ListFields()[4][1]
                yield(MDOrderDetail(mdrecord))
            else:
                if response.insightErrorContext.errorCode != 3 :
                    raise MarketDataQueryError(response.insightErrorContext)

    @statisticLog('thirdpartydata', 'MarketData')
    def getMDSecurityOrderDetailDataFrame(self,htscSecurityID,startDateTime,endDateTime):
        """委托队列查询

        :param htscSecurityID: 华泰证券ID，如："601688.SH"
        :type htscSecurityID: string
        :param startDateTime: 开始时间，格式为yyyyMMddHHmmss
        :type startDateTime: string
        :param endDateTime: 结束时间，格式为yyyyMMddHHmmss
        :type endDateTime: string
        :returns: pandas.DataFrame

        :注意:    查询最长时间跨度为一天

        """
        
        IMDTS_stub = IMDTickService_pb2_grpc.IMDTickServiceStub(self._channel)
        MDRequsst = IMDTickService_pb2.MDTickOrderDetailTimeOrderRpcRequest (htscSecurityID=htscSecurityID, startDateTime=startDateTime,endDateTime=endDateTime,ascOrder=True)
        responses = IMDTS_stub.getMDSecurityOrderDetailByTimeOrder(MDRequsst,self._timeout)
        results = []
        AttributeNames = SecurityTypeName.MDOrderListAttrNames.copy()
#         for response in responses:
#             if response.isSuccess == False:
#                 print(response.isSuccess)
        for response in responses:
            if response.isSuccess:
                mdrecord = response.result.ListFields()[4][1]
                result = []
                for attr in AttributeNames:
                    if hasattr(mdrecord,attr):
                        result.append(getattr(mdrecord,attr))
                    else:
                        result.append(None)
                if hasattr(mdrecord,"Buy1OrderDetail"):
                    Buy = list(mdrecord.Buy1OrderDetail)
                    Buy.extend([None]*(50-len(Buy)))  
                else:
                    Buy.extend([None]*50)
                if hasattr(mdrecord,"Sell1OrderDetail"):
                    Sell = list(mdrecord.Sell1OrderDetail)
                    Sell.extend([None]*(50-len(Sell)))
                else:
                    Sell1 = [None]*50
                result.extend(Buy)
                result.extend(Sell)
                results.append(result)
                #print("hello")
            else:
                if response.insightErrorContext.errorCode != 3 :
                    raise MarketDataQueryError(response.insightErrorContext)
                
        buyAttr = []
        sellAttr = []
        for i in range(1,51):
            buyAttr.append("Buy1OrderDetail_"+str(i))
            sellAttr.append("Sell1OrderDetail_"+str(i))
        AttributeNames.extend(buyAttr)
        AttributeNames.extend(sellAttr)
        df = pandas.DataFrame(results,columns=AttributeNames)           
        return df


    #新增需求getKLine4ZT
    @statisticLog('thirdpartydata', 'MarketData')
    def getKLine4ZTDataFrame(self,htscSecurityID,startDateTime,endDateTime,ePlaybackExrightsType,eMarketDataType,ascOrder=True):
        IMDTS_stub = IMDKLineService_pb2_grpc.IMDKLineServiceStub(self._channel)
        MDRequsst = IMDKLineService_pb2.MDKLine4ZTRpcRequest(htscSecurityID=htscSecurityID,startDateTime=startDateTime, endDateTime=endDateTime,ePlaybackExrightsType=ePlaybackExrightsType,eMarketDataType=eMarketDataType,ascOrder=ascOrder)
        response = IMDTS_stub.getKLine4ZT(MDRequsst, self._timeout)

        if response.isSuccess == False and response.insightErrorContext.errorCode != 3 and response.insightErrorContext.errorCode != 2:
            raise MarketDataQueryError(response.insightErrorContext)

        clo_name = SecurityTypeName.MDKLineAttrNames.copy()
        results = []
        if response.isSuccess == True:
            for re in response.result:
                result = []
                for attr in clo_name:
                    mdrecord = re.mdKLine
                    if hasattr(mdrecord, attr):
                        result.append(getattr(mdrecord, attr))
                    else:
                        result.append(None)
                results.append(result)
        df = pandas.DataFrame(results, columns=clo_name)
        import copy
        df1 = copy.copy(df)
        for row_idx,row in df1.iterrows():
            if row.loc["KLineCategory"]!=0:
                row.loc[["OpenPx","ClosePx","HighPx","LowPx","NumTrades","TotalVolumeTrade","TotalValueTrade"]] = np.nan
                df.loc[row_idx] = row
        return df.iloc[:,:-1]

    @statisticLog('thirdpartydata', 'MarketData')
    def getOptionHistoryConstant(self,securityIDSource,securityType,queryDate):
        """
        查询当日可交易的期权代码

        | 参数                 | 类型      | 注释                                                                  |
        |----------------------|---------|---------------------------------------------------|
        | securityIDSource     | int  | 市场类型                                              |
        | securityType        | int  | 证券类型                                              |
        | queryDate          | string  | 查询日期                                              |

        **注意**：
            securityIDSource目前只支持101（上交所）
            securityType目前只支持7（期权）

        - **返回**

            list

        - **范例**

                from xquant.thirdpartydata.marketdata import MarketData
                ma = MarketData()
                r = ma.getOptionHistoryConstant(101,7,"20190606")
                print(r)
                # 返回结果：
                ['10001808.SH', 01739.SH', '10001603.SH', ...... '10001686.SH']
        """
        obj_HistoryConstantRpcRequest = IMDConstantService_pb2.HistoryConstantRpcRequest()
        obj_securitySourceType = obj_HistoryConstantRpcRequest.securitySourceType
        obj_securitySourceType.securityIDSource = securityIDSource
        obj_securitySourceType.securityType = securityType

        IMDTS_stub = IMDConstantService_pb2_grpc.IMDConstantServiceStub(self._channel)
        MDRequsst = IMDConstantService_pb2.HistoryConstantRpcRequest(securitySourceType=obj_securitySourceType,queryDate=queryDate)
        response = IMDTS_stub.getHistoryConstantBySourceType(MDRequsst, self._timeout)
        stock_list = []
        if response.isSuccess:
            for r in response.result:
                stock_list.append(r.htscSecurityID)
        else:
            if response.insightErrorContext.errorCode != 2 : #No tick record found
                raise MarketDataQueryError(response.insightErrorContext)
        return stock_list


    @statisticLog('thirdpartydata', 'MarketData')
    def getMDConstantData(self,underlyingSecurityID, callOrPut,expireMonth, exercisePrice, adjustFlag = "M"):
        """ 查询期货行情静态信息
        :param underlyingSecurityID: 合约基础标的，示例： "510050"
        :type underlyingSecurityID: string
        :param callOrPut: 期权类型，示例：看涨为True，看跌为False
        :type callOrPut: bool
        :param expireMonth: 到期日，示例："1901"
        :type expireMonth: string
        :param adjustFlag: 期权调整标志位，默认为M，首次调整后由M变为A，第二次调整由A变为B，以此类推
        :type adjustFlag: string
        :param exercisePrice: 行权价，50ETF期权行权价格式为02450，原始行权价为2.45
        :type exercisePrice: string
        :returns: pandas.DataFrame

        :注意:
            - 查询最长时间跨度为一天
            - 目前只提供了深交所的数据

        underlyingSecurityID, callOrPut,expireMonth, adjustFlag, exercisePrice
        """
        if type(callOrPut) != bool:
            raise Exception("callOrPut 请传入bool值，True or False！")
        exercisePrice = "%05d" % (float(exercisePrice)*1000)

        obj_MDOptionRpcRequest = IMDConstantService_pb2.MDOptionRpcRequest()
        obj_optionInfo = obj_MDOptionRpcRequest.optionInfo.add()
        obj_optionInfo.underlyingSecurityID = underlyingSecurityID
        obj_optionInfo.callOrPut = callOrPut
        obj_optionInfo.expireMonth = expireMonth
        obj_optionInfo.exercisePrice = exercisePrice
        obj_optionInfo.adjustFlag = adjustFlag
        # print(obj_optionInfo)

        IMDTS_stub = IMDConstantService_pb2_grpc.IMDConstantServiceStub(self._channel)
        MDRequsst = IMDConstantService_pb2.MDOptionRpcRequest(optionInfo = [obj_optionInfo])
        response = IMDTS_stub.getMDOptionBasicInfo(MDRequsst,self._timeout)
        AttributeNames = SecurityTypeName.MDOrderAttrNames.copy()
        if response.isSuccess:
            # print(response.result[0])
            return response.result[0].htscSecurityID
        else:
            print("Error:fail to fetch Option Contract Code by Option underlyingSecurityID.")



    @statisticLog('thirdpartydata', 'MarketData')
    def getOptTickData(self,underlyingSecurityID, startDateTime, endDateTime, callOrPut, expireMonth, exercisePrice, adjustFlag = "M", QueryType = 0):
        """ 查询期货行情
        :param underlyingSecurityID: 合约基础标的，示例： "510050"
        :type underlyingSecurityID: string
        :param startDateTime: 开始时间，格式为yyyyMMddHHmmss
        :type startDateTime: string
        :param endDateTime: 结束时间，格式为yyyyMMddHHmmss
        :type endDateTime: string
        :param adjustFlag: 期权调整标志位，默认为M，首次调整后由M变为A，第二次调整由A变为B，以此类推
        :type adjustFlag: string
        :param callOrPut: 期权类型，示例：看涨为True，看跌为False
        :type callOrPut: bool
        :param expireMonth: 期权到期年月，示例："1901"
        :type expireMonth: string
        :param exercisePrice: 行权价，示例：50ETF期权原始行权价为2.45
        :type exercisePrice: float
        :param QueryType: 查询类型，0表示一般Tick数据，1表示包含买卖盘的tick数据，默认值为0
        :type QueryType: int
        :returns: pandas.DataFrame

        df2 = ma.getOptTickData(underlyingSecurityID = "510050", startDateTime = "20190114090000", endDateTime="20190114100000",callOrPut = 0, expireMonth = "1901", adjustFlag="M", exercisePrice="02450"
        :注意:
            - 查询最长时间跨度为一天
            - 目前只提供了深交所的数据

        underlyingSecurityID, callOrPut,expireMonth, adjustFlag, exercisePrice
        """
        if type(callOrPut) != bool:
            raise Exception("callOrPut 请传入bool值，True or False！")
        # exercisePrice = "%05d" % (float(exercisePrice)*1000)
        htscSecurityID = self.getMDConstantData(underlyingSecurityID, callOrPut,expireMonth, exercisePrice, adjustFlag)
        if QueryType == 0:
            eMDTickLevel = 1
        else:
            eMDTickLevel = 5
        IMDTS_stub_tick = IMDTickService_pb2_grpc.IMDTickServiceStub(self._channel)
        MDRequsst = IMDTickService_pb2.MDTickTimeOrderRpcRequest(htscSecurityID=htscSecurityID,
                                                             startDateTime=startDateTime, endDateTime=endDateTime,
                                                             eMDTickLevel=eMDTickLevel, ascOrder=True)
        responses = IMDTS_stub_tick.getMDSecurityTickByTimeOrder(MDRequsst,self._timeout)

        results = []
        AttributeNames = SecurityTypeName.MDTickAttrNames.copy()
        i = 0
        for response in responses:
            if response.isSuccess:
                mdrecord = response.result.ListFields()[4][1]  ##注意此处默认取出的是第五个
                if i == 0:
                    name = response.result.ListFields()[4][0].name
                    if name == "mdFuture":  #类型是期货
                        if QueryType == 0:   #一般的期货数据
                            AttributeNames = SecurityTypeName.MDTickFuturesAttrNames.copy()
                        else:               #含买卖盘的期货数据
                            AttributeNames = SecurityTypeName.geMDTickABFuturesAttrNames().copy()
                    elif name == "mdIndex":  #类型是指数，则没有买卖盘的区别
                        AttributeNames = SecurityTypeName.MDTickAttrNames.copy()
                    elif name == "mdOption": #类型是期权
                        if QueryType == 0:   #一般的期货数据
                            AttributeNames = SecurityTypeName.MDTickOptionsAttrNames.copy()
                        else:               #含买卖盘的期货数据
                            AttributeNames = SecurityTypeName.geMDTickABOptionsAttrNames().copy()
                    else:                    #类型是股票、债券、基金、权证、期权
                        if QueryType == 0:   #一般tick数据
                            AttributeNames = SecurityTypeName.MDTickAttrNames.copy()
                        else:              #含买卖盘的tick数据
                            AttributeNames = SecurityTypeName.getMDTickABAttrNames().copy()

                result = []
                for attr in AttributeNames:
                    if hasattr(mdrecord,attr):
                        result.append(getattr(mdrecord,attr))
                    else:
                        result.append(None)
                i = i+1
                results.append(result)
                #return(response.result)
            else:
                if response.insightErrorContext.errorCode != 2 : #No tick record found
                    raise MarketDataQueryError(response.insightErrorContext)
        df = pandas.DataFrame(results,columns=AttributeNames)
        return df

    @statisticLog('thirdpartydata', 'MarketData')
    def getMDSecurityRecordBySourceTypes(self, securityIDSource=101, securityType=2):
        IMDTS_stub_tick = IMDRealTimeService_pb2_grpc.IMDRealTimeServiceStub(self._channel)
        MDRequsst = IMDRealTimeService_pb2.MDSecurityBySourceTypeRpcRequest()
        param = MDRequsst.securitySourceType
        param.securityIDSource = securityIDSource
        param.securityType = securityType

        requests = IMDRealTimeService_pb2.MDSecurityBySourceTypeRpcRequest(securitySourceType=param)
        responses = IMDTS_stub_tick.getMDSecurityRecordBySourceTypes(requests, self._timeout)

        if securityType!=2 and securityType!=1:
            raise Exception("securityType错误！证券类型只支持传入1或者2！")
        
        results = []
        if responses.isSuccess:
            for record in responses.result:
                result = []
                if securityType==2:
                    #股票数据
                    columns = SecurityTypeName.RealTimeStockTickAttNames
                    mdrecord = record.mdStock
                if securityType==1:
                    #指数数据
                    columns = SecurityTypeName.RealTimeIndexTickAttNames
                    mdrecord = record.mdIndex

                    
                for col in columns:
                    if hasattr(mdrecord,col):
                        result.append(getattr(mdrecord,col))
                    else:
                        result.append(None)
                results.append(result)
        else:
            if responses.insightErrorContext.errorCode != 2:
                raise MarketDataQueryError(responses.insightErrorContext)
        import pandas as pd
        return pd.DataFrame(results, columns=columns)