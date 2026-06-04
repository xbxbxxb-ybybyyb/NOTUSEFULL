from .setChannel import *
from .setGrpcPath import *
from .proto.factordata_pb2_grpc import *
from .proto.putFactorValue_pb2_grpc import *
from .proto.stockFilter_pb2_grpc import *
from .proto.tansday_pb2_grpc import *
from .proto.hset_pb2_grpc import *
import pandas
import errno
from xquant.utils import statisticLog
import os
from .FactorEnum import *
from enum import IntEnum
import time
import pickle
from xquant.setXquantEnv import xquantEnv

class insightError(object):
    def __init__(self,resultCode,message):
        self.resultCode = resultCode
        self.message = message
        
class FactorDataQueryError(Exception):
    def __init__(self, insightError):
        self.resultCode = insightError.resultCode
        self.message = insightError.message
    def __str__(self):
        return ("errorCode: {0}    message: {1}".format(self.resultCode, self.message))

class FactorData(object):
    @statisticLog('thirdpartydata','FactorData')
    def __init__(self, user_name : str = None, channel :str = None, api_key : str = None , timeout : int = 180):
        """
        初始始化，这里的参数目前没有使用
        :param user_name:
        :param channel:
        :param api_key:
        """
        self.user_name = user_name
        self.channel = channel
        self.api_key = api_key
        if xquantEnv == 0:
            channel = choose_channel(md_channels)
        elif xquantEnv == 1:
            channel = choose_channel2()
        else:
            raise Exception("factor channel error！")
        self._channel = grpc.insecure_channel(channel)
        self._timeout = timeout
    
    def __del__(self):
        """
        析构时处理
        注：由于测试机和正式机系统的grpc为定制，无法更新为最新版本，所以这里暂时不关闭
            经过测试由于python的vm里PY文件执行完后由对象内部进行析构关闭，不会影响打开句柄和占用端口问题
        :return:
        """
        # self._channel.close()
        pass

    @statisticLog('thirdpartydata', 'FactorData')
    def getSimpleFactorData(self, factors, times,  symbols,factor_param=None):
        """读取单因子数据

        :param factors 因子:
                int / str / list[int / str]  \n
                int 时为actor_id 因子唯一序号  例如：123
                str 时为factor_symbol 因子符号 例如：open   如需要版本号时，使用$.主版本.副版本号  例样 open$$$2.8
                list[int / str]  为列表形式(这里列表中只有一个因子）
        :param times 时间:
                date / (from, to) / [ date ]  \n
                date使用str表示格式（yyyymmdd）例如：20180502
                (from, to)  from为start_time  to为end_time  例如：('20180501','20180504')  表示为2018年5月1日 到 2018年5月4日
                [ date ]  这种是列表形式
        :param symbols 股票:
                int / str / list[int / str] \n
                int 时为symbol_id 证券序号
                str 时为symbol 证券代码
                list[int / str] 为列表形式
        :param factor_param 特殊参数:
        
                - 参数标志
                    +--------------+-------+---------+----------------------------+
                    | 类别         | 序号  | 参数值  |  含义                      |
                    +==============+=======+=========+============================+
                    | 复权标志     |  0    |   0     |  未复权                    |
                    +              +-------+---------+----------------------------+
                    | (bit:0-1)    |  1    |   1     |  前复权                    |
                    +              +-------+---------+----------------------------+
                    |              |  2    |   2     |  后复权                    |
                    +--------------+-------+---------+----------------------------+
                    | 会计准则标志 |  1    |   4     | 旧会计准则（2017版之前）   |
                    |              +-------+---------+----------------------------+
                    | (bit:2-3)    |  0    |   0     |  新会计准则（2017版）      |
                    +--------------+-------+---------+----------------------------+
                    | 合并报表标志 |  1    |   16    |    合并报表                |
                    +              +-------+---------+----------------------------+
                    | (bit:4)      |  0    |   0     |    母公司                  |
                    +--------------+-------+---------+----------------------------+
                    | 报表调整标志 |  0    |   0     |    原始报表                |
                    +              +-------+---------+----------------------------+
                    | (bit:5-6)    |  1    |   32    |    调整                    |
                    +              +-------+---------+----------------------------+
                    |              |  2    |   64    |    更正                    |
                    +--------------+-------+---------+----------------------------+
        
        :return: 数据  行为复合索引（时间，股票），列为因子项

        :注意: 因子为列表时只能传一个值

        :例子:
                #查询==》因子为"pre_close","high","open"  股票为"000001","000002","000004"  时间为 "20180502"到"20180504"  \n
                re = fa.getData(["pre_close","high","open"],("20180501","20180531"),["000001.sz","000002.sz","000004.sz"])
        """
        if type(factors) == list and len(factors) >1:
            raise Exception("[errno:%s ] factors err (%s)" % (errno.EFAULT, str(factors)))
        
        stub = FactorDataServiceStub(self._channel)
        # 参数字典
        r = self.__getDataInPar(factors,symbols,times)

        # 注意这里使用三目操作符，数据为空时传入None
        request = FactorDataRequest(
                                    user_name = self.user_name,
                                    channel = self.channel,
                                    api_key = self.api_key,
                                    factor_id = r.get('factor_id') ,
                                    factor_symbol = r.get('factor_symbol'),
                                    factor_param = factor_param,
                                    start_time = r.get('start_time') ,
                                    end_time = r.get('end_time') ,
                                    time_list = r.get('time_list') ,
                                    symbol_id = r.get('symbol_id') ,
                                    symbol = r.get('symbol')
                                )
        # 请求参数支持流方式，但为了保证接口操作，暂时不支持用户使用
        responses = stub.getData(self.__requestStream([request]), self._timeout)
        desc, data = self._getDataResponse(responses)

        if desc == None:
            return None
        return self.__genPandasData2(desc, data)
        
        
    @statisticLog('thirdpartydata', 'FactorData')
    def getData(self, factors, times, symbols=None,factor_param=None,isShowName=True):
        """读取因子数据

        :param factors 因子:
                int / str / list[int / str] \n
                | int 时为actor_id 因子唯一序号  例如：123
                | str 时为factor_symbol 因子符号 例如：open   如需要版本号时，使用$.主版本.副版本号  例样 open$$$2.8
                | list[int / str]  为列表形式
        :param times 时间:
                date / (from, to) / [ date ] \n
                date使用str表示格式（yyyymmdd）例如：20180502
                (from, to)  from为start_time  to为end_time  例如：('20180501','20180504')  表示为2018年5月1日 到 2018年5月4日
                [ date ]  这种是列表形式
        :param symbols 证券(默认为None，不传即为起始日期的全部A股):
                int / str / list[int / str] \n
                int 时为symbol_id 证券序号
                str 时为symbol 证券代码
                list[int / str] 为列表形式
        :param factor_param 特殊参数:
        
                - 参数标志
                    +--------------+-------+---------+----------------------------+
                    | 类别         | 序号  | 参数值  |  含义                      |
                    +==============+=======+=========+============================+
                    | 复权标志     |  0    |   0     |  未复权                    |
                    +              +-------+---------+----------------------------+
                    | (bit:0-1)    |  1    |   1     |  前复权                    |
                    +              +-------+---------+----------------------------+
                    |              |  2    |   2     |  后复权                    |
                    +--------------+-------+---------+----------------------------+
                    | 会计准则标志 |  1    |   4     | 旧会计准则（2017版之前）   |
                    |              +-------+---------+----------------------------+
                    | (bit:2-3)    |  0    |   0     |  新会计准则（2017版）      |
                    +--------------+-------+---------+----------------------------+
                    | 合并报表标志 |  1    |   16    |    合并报表                |
                    +              +-------+---------+----------------------------+
                    | (bit:4)      |  0    |   0     |    母公司                  |
                    +--------------+-------+---------+----------------------------+
                    | 报表调整标志 |  0    |   0     |    原始报表                |
                    +              +-------+---------+----------------------------+
                    | (bit:5-6)    |  1    |   32    |    调整                    |
                    +              +-------+---------+----------------------------+
                    |              |  2    |   64    |    更正                    |
                    +--------------+-------+---------+----------------------------+
                    | 自然日       |   0   |   0     | 自然日  DAY.NATURAL        |
                    |              +-------+---------+----------------------------+
                    |              |   1   |  128    | A股交易日 DAY.TRADING      |
                    +--------------+-------+---------+----------------------------+
        :param isShowName 是否显示因子简称: True显示因子简称   False显示因子id
        :return: 数据  行为复合索引（时间，股票），列为因子项


        :例子:
            查询==》因子为"pre_close","high","open"  股票为"000001","000002","000004"  时间为 "20180502"到"20180504" \n
            re = fa.getData(["pre_close","high","open"],("20180501","20180531"),["000001.sz","000002.sz","000004.sz"])
        """
        if xquantEnv == 1:
            if not symbols:
                import xquant.quant as xq
                startDate = ""
                if times:
                    if type(times) == list:
                        # 日期列表，列表中使用一天为一个单位
                        int_times = [int(i) for i in times]
                        startDate = str(min(int_times))
                    elif type(times) == tuple:
                        # 元祖形式为时间区间  左为起始，右为终止
                        if not len(times) == 2:
                            pass
                        else:
                            if type(times[0]) == str:
                                startDate = times[0]
                            else:
                                startDate = str(times[0])
                    elif type(times) == str:
                        # 普通单天日期查询
                        startDate = times
                    else:
                        # 日期类型错误直接跳过
                        pass
                if startDate:
                    t = xq.hset(xq.PlateType.MARKET, startDate, xq.MarketType.ALLA)
                    try:
                        symbols = t[0]
                    except:
                        symbols = []

        stub = FactorDataServiceStub(self._channel)

        # 参数字典
        r = self.__getDataInPar(factors,symbols,times)
        
        # 注意这里使用三目操作符，数据为空时传入None
        request = FactorDataRequest(
                                    user_name = self.user_name,
                                    channel = self.channel,
                                    api_key = self.api_key,
                                    factor_id = r.get('factor_id') ,
                                    factor_symbol = r.get('factor_symbol') ,
                                    factor_param = factor_param ,
                                    start_time = r.get('start_time') ,
                                    end_time = r.get('end_time') ,
                                    time_list = r.get('time_list') ,
                                    symbol_id = r.get('symbol_id') ,
                                    symbol = r.get('symbol')
                                    )
        # 请求参数支持流方式，但为了保证接口操作，暂时不支持用户使用
        responses = stub.getData(self.__requestStream([request]),self._timeout)

        desc,data = self._getDataResponse( responses)
        if desc == None:
            return None
        return self.__genPandasData(desc, data, isShowName)

    @statisticLog('thirdpartydata', 'FactorData')
    def putBatch(self,data):
        """
        上传因子数据

        :param 上传数据 data:
            DataFrame(None,columns=['symbol', 'time', 'value']) \n
        :return:
        """
        if os.getenv("factor_id") is None:
            raise FactorDataQueryError(insightError(-1,"factor_id Undefined"))
        factor_id = int(os.getenv("factor_id"))
        stub = PutFactorValueServiceStub(self._channel)
        responses = stub.putBatch(
            self.__requestStream_Progress(
                self._genFactorValueRequest(data,factor_id)
            ),
            self._timeout
        )
        re = []
        for response in responses:
            re.append(response)
        #print(f"[{'='*70}>]  00:00")
        print("["+'='*70+">]  00:00")
        return re


    @statisticLog('thirdpartydata', 'FactorData')
    def stockFilter(self,time,filt_type,symbol=None):
        """
        单日股票池剔除
            
            | 此接口可以剔除单日股票池中涨停、跌停、停盘等类型的股票，返回过滤完后的股票集；
        :param symbol: 股票池(格式000001.SH)  类型(list / str)
        :param time: 单日时间 yyyymmdd  类型(str)
        :param filt_type:  类型(int)
        
            =======  ================
             类型     说明
            -------  ----------------
              1       停牌
              2       涨停
              4       跌停
              8       开盘涨停
              16      开盘跌停
            -------  ----------------
                组合示例
            -------------------------
              1+2     停牌+涨停
              1+4     停牌+跌停
              8+1     开盘涨停+停牌
              16+1    开盘跌停+停牌
            =======  ================
        :return: 股票信息列表  类型:(list)
        
        """
        if type(time)==int :
            time = str(time)
        
        if time==None or \
                filt_type==None:
            raise FactorDataQueryError(insightError(-1, "param not None Errror"))
        
        if not type(filt_type) == int and \
                type(filt_type) == FILT_TYPE:
            filt_type = int(filt_type)
        
        # if not filt_type in FILT_TYPE.__dict__.values():
        #     raise FactorDataQueryError(insightError(-1, f"filt_type:{filt_type} error! Please check FILT_TYPE(Enum)"))
        
        if type(symbol) == str or type(symbol) ==list or symbol==None:
            pass
        else:
            raise FactorDataQueryError(insightError(-1, "symbol type error:"+str(type(symbol))))
        
        if not type(time)==str and not type(time)==tuple:
            raise FactorDataQueryError(insightError(-1, "time type error:" + str(type(time))))
        
        if not type(filt_type)==int:
            raise FactorDataQueryError(insightError(-1, "filt_type type error:" + str(type(filt_type))))

        stub = StockFilterServiceStub(self._channel)
        
        if type(symbol) == list or symbol == None :
            symbol = symbol
        else:
            symbol = [symbol]

        startTime = None
        endTime = None
        if type(time) == tuple:
            if type(time[0]) == int :
                startTime = str(time[0])
            else:
                startTime = time[0]
                
            if type(time[1]) == int :
                endTime = str(time[1])
            else:
                endTime = time[1]
        else:
            startTime = time
            endTime = time
        request = StockDataRequest(
                symbol = symbol ,
                startTime = startTime,
                endTime = endTime,
                filt_type = filt_type
            )
    
        responses = stub.flush(request,self._timeout)
        
        re={}
        for response in responses:
            if not response.resultCode == 0:
                raise FactorDataQueryError(response)
            else:
                re[response.date] = response.symbol
        
        keys = []
        for k in re.keys():
            keys.append(k)
        keys = sorted( keys )
        data = {}
        for k in keys:
            data[k] = re[k]
        return data
        # return {k: re[k] for k in sorted( [k for k in re.keys()] )}
        
    @statisticLog('thirdpartydata', 'FactorData')
    def tradingDay(self,start_time,end_time,date_type = 2,frequency = 1):
        """
        交易日查询
        
        :param start_time:  格式：yyyyMMdd
        :param end_time:  格式：yyyyMMdd
        :param date_type: 日历类型(1:ALLDAYS%日历日/2:TRADINGDAYS%交易日)  TANSDAY_DATE_TYPE(Enum)
        :param frequency: 数据频率(1:DAY/2:WEEK/3:MONTH/4:QUARTER/5:HALFYEAR/6:YEAR)现只支持传1
        :return:
        """
        # 字段检查
        if not type(start_time) in (str,int) :
            raise FactorDataQueryError(
                #insightError(-1, f"start_time:{start_time} type error! Please input yyyymmdd(str|int)"))
                 insightError(-1, "start_time:{start_time} type error! Please input yyyymmdd(str|int)".format(start_time=start_time)))

        if not type(end_time) in (str,int):
            raise FactorDataQueryError(
                #insightError(-1, f"start_time:{end_time} type error! Please input yyyymmdd(str|int)"))
                insightError(-1, "end_time:{end_time} type error! Please input yyyymmdd(str|int)".format(end_time=end_time)))
        
        if type(start_time) == int:
            start_time = str(start_time)
        
        if type(end_time) == int:
            end_time = str(end_time)
        
        if not type(date_type) == int or \
            not date_type in TANSDAY_DATE_TYPE.__dict__.values():
            #raise FactorDataQueryError(insightError(-1, f"date_type:{date_type} error! Please check TANSDAY_DATE_TYPE(Enum)"))
            raise FactorDataQueryError(insightError(-1, "date_type:{date_type} error! Please check TANSDAY_DATE_TYPE(Enum)".format(date_type=date_type, Enum=Enum)))        

        if not type(frequency) ==int or \
            not frequency in FREQUENCY_ENUM.__dict__.values():
            raise FactorDataQueryError(
                #insightError(-1, f"frequency:{frequency} error! Please check FREQUENCY_ENUM(Enum)"))
                insightError(-1, "frequency:{frequency} error! Please check FREQUENCY_ENUM(Enum)".format(frequency=frequency, Enum=Enum)))
            
        stub = TradingDayServiceStub(self._channel)
        request = TradingDayRequest(
            start_time = start_time,
            end_time = end_time,
            frequency = frequency,
            day_type = None ,
            date_type = date_type,
            market_type = None
            )
        
        response = stub.tradingDay(request,self._timeout)
        if not response.resultCode == 0:
            raise FactorDataQueryError(response)
        re = None
        if response.data:
            re = [int(d.day) for d in response.data]
        return re

    
    def hset(self,plateType,plateId,startTime,endTime):
        """
        成份股查询
        :param plateType: 板块类型(1:概念板块;2:指数板块;3:市场板块;4:行业板块)暂时只支持2指数板块
        :param plateId: (当plateType为2指数板块时, 此参数为证券代码，暂且支持000300.SH:沪深300和000905.SH:中证500)
        :param startTime: 开始日期(格式yyyyMMdd)
        :param endTime: 结束日期(格式yyyyMMdd)
        :return:
        """
        if type(plateType) == PLATETYPE:
            plateType = int(plateType)
        if type(startTime) == int :
            startTime = str(startTime)
        if type(endTime) == int :
            endTime = str(endTime)
        
        if not type(plateType)==int or\
            not plateType in PLATETYPE.__dict__.values():
            raise FactorDataQueryError(
                #insightError(-1, f"date_type:{plateType} error! Please check PLATETYPE(IntEnum)"))
                insightError(-1, "date_type:{plateType} error! Please check PLATETYPE(IntEnum)".format(plateType=plateType, IntEnum=IntEnum)))        
    
        stub = HsetServiceStub(self._channel)
        request = HsetRequest(
            plateType = plateType,
            plateId = plateId,
            startTime = startTime,
            endTime = endTime
        )
        responses = stub.hset(request, self._timeout)
        re = []
        for response in responses:
            if not response.resultCode == 0:
                raise FactorDataQueryError(response)
            re.append(response.stockInfo)
        return re
        

    def _getDataResponse(self,responses):
        startTime = time.time()
        printTime = startTime
        data = []
        desc = None
        dataI = 0
        i = 0
        sum = 0
        for response in responses:
            i += 1
            if response.resultCode == 0:
                if (i == 1):
                    sum = int(response.message)
            
                if response.data:
                    dataI += 1
                    if sum > 0 and len(data) > 0 and time.time() - printTime > 3:
                        timeUse = time.time() - startTime  # 当前已经用时
                        remainingTime = int(timeUse / len(data) * (sum - len(data)))  # 预计用时（秒）
                        if remainingTime < 60:  #
                            if remainingTime < 10:  # 秒数小于十的需要补零
                            #    remainingTime = f'0{remainingTime}'
                                remainingTime = '0{remainingTime}'.format(remainingTime=remainingTime)           
                            remainingTime = '00:{remainingTime}'.format(remainingTime=remainingTime)
                        else:  # 大于六十秒，需要记入分钟
                            remainder = remainingTime % 60
                            if remainder < 10:
                                #emainder = f'0{remainder}'
                                remainder = '0{remainder}'.format(remainder=remainder)
                            remainingTime = int(remainingTime / 60)
                            if remainingTime < 10:
                                #emainingTime = f'0{remainingTime}'
                                remainingTime = '0{remainingTime}'.format(remainingTime=remainingTime)
                            #remainingTime = f'{remainingTime}:{remainder}'
                            remainingTime = '{remainingTime}:{remainder}'.format(remainingTime=remainingTime, remainder=remainder)

                        completion = int(len(data) / sum * 70)  # 完成率（七十格率）
                        completionStr = ('=' * completion) + ">" + (' ' * (70 - completion))  # 进度条
                       # print(f"[{completionStr}]  {remainingTime}")
                        print("[{completionStr}]  {remainingTime}".format(completionStr=completionStr, remainingTime=remainingTime))
                        printTime = time.time()
                
                    for d in response.data:
                        data.append(d)
                if response.desc and response.desc.time:
                    desc = response.desc
                    # sum =len(desc.time) * (len(factors) if type(factors)==list else 1)
        
            else:
                raise FactorDataQueryError(response)
        return desc, data
    
    
    def _genFactorValueRequest(self,data,factor_id):
        num = 0
        requestList = []
        fvs = []

        data = data.values
        for d in data:
            
            if type(d[1])==str:
                _time=d[1]
            else:
                _time=str(d[1])
                
            fvs.append(
                FactorValue(
                        symbol = d[0],
                        time = _time,
                        value = d[2]
                    )
            )
            num += 1
            if num >= 500:
                requestList.append(
                    FactorValueRequest(
                        user_name=self.user_name,
                        channel=self.channel,
                        api_key=self.api_key,
                        factor_id=factor_id,
                        factorValue=fvs
                    )
                )
                num = 0
                fvs = []

        if len(fvs) > 0:
            requestList.append(
                FactorValueRequest(
                    user_name=self.user_name,
                    channel=self.channel,
                    api_key=self.api_key,
                    factor_id=factor_id,
                    factorValue=fvs
                )
            )
        return requestList,len(data),500,len(fvs)
    
    def __genPandasData2(self, desc, data):
        """
        生成pandas格式数据，
        数据  索引（时间），列为股票
            首个响应回复包后的其余包中的FactorData集合为Hbase中查出的结果数据，结构为多维数组下标（对应首个描述包中3个数组），
        一条FactorData数据对应Hbase中一行数据。其计算方法为，先依次获取首个包中Desc里FactorInfo的数量为X数组的长度xSize，
        SymbolInfo的数量为Y数组的长度ySize，time的数量为Z数组的长度zSize，再通过FactorData中的uIndex计算出三维数组下标。
        int x = uIndex / (ySize * zSize);	对应因子集合中的下标	计算顺序1
        int y = (uIndex - (x * ySize * zSize)) / zSize;	对应证券集合中的下标	计算顺序2
        int z = uIndex - (x * ySize * zSize) - (y * zSize);	对应时间集合中的下标	计算顺序3

        :param desc:
        :param data:
        :return:
        """
        columns = []
        for symbol in desc.symbol:
            # 因子名称加入版本号
            columns.append(symbol.symbol_code)
        xSize = 1
        ySize = len(desc.symbol)
        zSize = len(desc.time)
        dates = []
        for t in desc.time:
            dates.append(t)
        symbols = []
        for s in desc.symbol:
            symbols.append(s.symbol_code)
        index = []
        for d in dates:
            index.append(d)
        index = pandas.Index(index, names=['date'])
        datas = []
        datamap = {}
        for i in range(0, ySize):
            x = [float('nan')] * (xSize * zSize)
            datas.append(x)
            datamap[columns[i]] = x
        for d in data:
            uIndex = d.index
            value = d.value
            x = int(uIndex / (ySize * zSize))
            y = int((uIndex - (x * ySize * zSize)) / zSize)
            z = int(uIndex - (x * ySize * zSize) - (y * zSize))
            datas[y][z] = value
        results = pandas.DataFrame(index=index, data=datamap)
  
        #print(f"[{'='*70}>]  00:00") 
        print("["+'='*70+">]  00:00")
        return results
    
    
    def __genPandasData(self,desc,data,isShowName=True):
        """
        生成pandas格式数据
        数据  行为复合索引（时间，股票），列为因子项
            首个响应回复包后的其余包中的FactorData集合为Hbase中查出的结果数据，结构为多维数组下标（对应首个描述包中3个数组），
        一条FactorData数据对应Hbase中一行数据。其计算方法为，先依次获取首个包中Desc里FactorInfo的数量为X数组的长度xSize，
        SymbolInfo的数量为Y数组的长度ySize，time的数量为Z数组的长度zSize，再通过FactorData中的uIndex计算出三维数组下标。
        int x = uIndex / (ySize * zSize);	对应因子集合中的下标	计算顺序1
        int y = (uIndex - (x * ySize * zSize)) / zSize;	对应证券集合中的下标	计算顺序2
        int z = uIndex - (x * ySize * zSize) - (y * zSize);	对应时间集合中的下标	计算顺序3
    
        :param desc:
        :param data:
        :return:
        """
        columns = []
        for factor in desc.factor:
            # 因子名称加入版本号
            # if not factor.major == None:
            #     columns.append(
            #                 factor.factor_symbol + "$" + str(factor.major) + "."
            #                    + (str(factor.minor) if factor.minor>9 else "0" + str(factor.minor))
            #                    )
            # else:# 如果无版本号，不加$
            if isShowName:
                columns.append(factor.factor_symbol)
            else:
                columns.append(factor.factor_id)
                
        xSize = len(desc.factor)
        ySize = len(desc.symbol)
        zSize = len(desc.time)
        dates = []
        for t in desc.time:
            dates.append(t)
        symbols = []
        for s in desc.symbol:
            symbols.append(s.symbol_code)
        index = []
        for d in dates:
            for s in symbols:
                index.append((d, s))
        index = pandas.Index(index, names=['date', 'symbol'])
        datas = []
        datamap = {}
        for i in range(0, xSize):
            x = [float('nan')]*(ySize * zSize)
            datas.append(x)
            datamap[columns[i]] = x
        for d in data:
            uIndex = d.index
            value = d.value
            x = int(uIndex / (ySize * zSize))
            y = int((uIndex - (x * ySize * zSize)) / zSize)
            z = int(uIndex - (x * ySize * zSize) - (y * zSize))
            datas[x][z * ySize + y] = value
        results = pandas.DataFrame(index=index, data=datamap)
        
        #print(f"[{'='*70}>]  00:00")
        print("["+'='*70+">]  00:00")
        return results
    
    def __getDataInPar(self,factors,symbols=None,times=None):
        """
        对getData代入参数分离判断并放了正确字典中返回
        :param factors:
        :param symbols:
        :param times:
        :return:
        """
        r = {}
        r['factor_id'] = None
        r['factor_symbol'] = None

        r['symbol_id'] = None
        r['symbol'] = None

        r['time_list'] = None
        r['start_time'] = None
        r['end_time'] = None
        
        if not type(factors) in (int,str,list) and issubclass(factors.__class__,IntEnum):
            factors = int(factors)
        
        if type(times) == int:
            times = str(times)

        if factors:
            if type(factors) == list:
                # 因子列表处理
                if type(factors[0]) == int:
                    r['factor_id'] = factors
                elif type(factors[0]) == str:
                    r['factor_symbol'] = factors
                elif issubclass(factors[0].__class__,IntEnum):
                    r['factor_id'] = [int(f) for f in factors]
                else:
                    # 因子列表中数据类型错误
                    raise Exception("[errno:%s ] factors type err (%s)" % (errno.EFAULT, str(type(factors[0]))))
            else:
                # 因子参数处理
                if type(factors) == int:
                    r['factor_id'] = [factors]
                elif type(factors) == str:
                    r['factor_symbol'] = [factors]
                else:
                    # 类型错误是抛错
                    raise Exception("[errno:%s ] factors type err (%s)" % (errno.EFAULT, str(type(factors))))
    
        if symbols:
            if type(symbols) == list:
                # 股票列表处理
                if type(symbols[0]) == int:
                    r['symbol_id'] = symbols
                elif type(symbols[0]) == str:
                    r['symbol'] = symbols
                else:
                    # 股票列表中类型错误
                    raise Exception("[errno:%s ] factors type err (%s)" % (errno.EFAULT, str(type(symbols[0]))))
            else:
                # 股票处理
                if type(symbols) == int:
                    r['symbol_id'] = [factors]
                elif type(symbols) == str:
                    r['symbol'] = [symbols]
                else:
                    # 股票类型错误
                    raise Exception("[errno:%s ] symbols type err (%s)" % (errno.EFAULT, str(type(symbols))))
    
        if times:
            if type(times) == list:
                # 日期列表，列表中使用一天为一个单位
                if type(times[0])==int:
                    times = [str(t) for t in times]
                r['time_list'] = times
            elif type(times) == tuple:
                # 元祖形式为时间区间  左为起始，右为终止
                if not len(times) == 2:
                    raise Exception("[errno:%s ] times (tuple)len err (%s)" % (errno.EFAULT, str(len(times))))
                
                if type(times[0]) == str:
                    r['start_time'] = times[0]
                else:
                    r['start_time'] = str(times[0])
                    
                if type(times[1]) == str:
                    r['end_time'] = times[1]
                else:
                    r['end_time'] = str(times[1])
                    
            elif type(times) == str:
                # 普通单天日期查询
                r['time_list'] = [times]
            else:
                # 日期类型错误是抛错
                raise Exception("[errno:%s ] times type err (%s)" % (errno.EFAULT, str(type(times))))
        return r
    
    def __filterPoint(self,str):
        if not str.find('.') == -1:
            return str[:str.find('.')]
        return str
    
    def __filterPointList(self,strs):
        re=[]
        for str in strs:
            re.append(self.__filterPoint(str))
        return re
    
    def __requestStream(self,requestList):
        """
        请求流操作处理
        :param requestList:
        :return:
        """
        for request in requestList:
            yield request
    
    def __requestStream_Progress(self,input):
        """
        请求流操作处理(带进度条式print)
        :param requestList:
        :return:
        """
        sum = 0 # 总记录数
        fixed = 0 # 批定数量
        tail = 0 # 尾部数量
        if type(input)==tuple: # 元祖时才处理
            requestList=input[0]
            sum = input[1]
            fixed = input[2]
            tail = input[3]
        else:
            requestList=input

        start_time = time.time()  # 开始时间
        printTime = start_time # 记录打印时间
        maxlen = len(requestList)
        i = 0 # 用户迭代记录
        for request in requestList:
            if sum>0 and i>0:
                if time.time()-printTime>3: # 大于三秒才输出进度
                    currentSum = i * fixed # 当前完成记录数
                    timeUse = time.time() - start_time # 当前已经用时
                    remainingTime = int(timeUse /currentSum * (sum-currentSum) ) # 预计用时（秒）
                    if remainingTime<60: #
                        if remainingTime<10: # 秒数小于十的需要补零
                            #remainingTime = f'0{remainingTime}'
                            remainingTime = '0{remainingTime}'.format(remainingTime=remainingTime)
                        #remainingTime = f'00:{remainingTime}'
                        remainingTime = '0{remainingTime}'.format(remainingTime=remainingTime)
                    else: # 大于六十秒，需要记入分钟
                        remainder = remainingTime%60
                        if remainder<10:
                           # remainder = f'0{remainder}'
                            remainder = '0{remainder}'.format(remainder=remainder)
                        remainingTime = int(remainingTime/60)
                        if remainingTime<10:
                            #remainingTime = f'0{remainingTime}'
                            remainingTime = '0{remainingTime}'.format(remainingTime=remainingTime)
                        #remainingTime = f'{remainingTime}:{remainder}'
                        remainingTime = '{remainingTime}:{remainder}'.format(remainingTime=remainingTime, remainder=remainder)                       
 
                    completion = int(currentSum/sum*70) # 完成率（七十格率）
                    completionStr = ('=' * completion) +">"+ (' '* (70-completion)) # 进度条
                    #print(f"[{completionStr}]  {remainingTime}")
                    print("[{completionStr}]  {remainingTime}".format(completionStr=completionStr, remainingTime=remainingTime))
                    printTime = time.time()
            i +=1
            
            yield request
            

def wss(symbols, indicators):
    actions = dict()
    actions['ipo_limitupopendate'] = _wss_ipo_limitupopendate

    if type(symbols) is str:
        symbols = symbols.split(',')
    elif type(symbols) is list:
        pass
    else:
        raise TypeError('symbols must be None, str or list, not ' + str(type(symbols)))
    if len(symbols) == 0:
        raise ValueError('symbols must be empty')

    if type(indicators) is str:
        indicators = indicators.split(',')
    elif type(indicators) is list:
        pass
    else:
        raise TypeError('indicators must be str or list, not ' + str(type(symbols)))
    if len(indicators) == 0:
        raise ValueError('indicators must be empty')

    values = []
    for indicator in indicators:
        if indicator not in actions:
            raise ValueError('indicator \'' + indicator + '\' is unknown')
        values.append(actions[indicator](symbols))
    return values

@statisticLog('thirdpartydata', 'FactorData')
def _wss_ipo_limitupopendate(symbols):
    values = []
    data = dict()
    with open('/app/data/wdb_h5/vip/ipo_limitupopendate.pickle', 'rb') as f:
        data = pickle.load(f)
    for symbol in symbols:
        if symbol in data:
            values.append(data[symbol])
        else:
            values.append(None)
    return values



