import urllib
import urllib.request
import math
import datetime
import io
from .setQuantPath import *
from .quantEnum import *
from xquant.utils import statisticLog

## Description 根据输入的时间区间、日期类型查询该时间段内的交易日期列表
## Inputs:
#     startTime：开始日期，格式yyyymmdd,例如: 20100861
#     endTime：  结束日期，格式yyyymmdd,例如: 20100861
#     frequency：数据频率，枚举整数类型，默认值：FrequencyType.DAY。
#       当frequency参数为 FrequencyType.DAY时，平台支持以startTime为起点，前后n日的时间序列查询(abs(n) < 10000)，
#       例如，查询以20150504前10个交易日的序列，可以输入：tradingDay(20120504, -10)，后面20日：tradingDay(20120504, 20)。
#     dayType：日期类型，枚举整数类型，当frequency 参数为FrequencyType.WEEK 时，默认值为DayType.FRIDAY；当frequency 参数为其它值，默认值为DayType.FIRSTDAY。
#     dateType：日历类型，枚举整数类型，默认值为DateType.TRADINGDAYS。
#     market：市场类型，枚举整数类型，默认值：MarketType.SH。暂时指定了两个市场，后续再拓展
## Outputs:
#   tradingDate： 交易日期，double类型列表

global dbPath

def tradingDay(startTime, endTime, frequencyType=FrequencyType.DAY, dayType=DayType.LASTDAY,
               dateType=DateType.TRADINGDAYS, marketType=MarketType.SH):
    """根据输入的时间区间、日期类型查询该时间段内的交易日期列表

    :param startTime: 开始日期，格式yyyymmdd,例如: 20100816
    :param endTime: 结束日期，格式yyyymmdd,例如: 20100816
    :param frequencyType: 数据频率，枚举整数类型，默认值：FrequencyType.DAY。当frequency参数为 FrequencyType.DAY时，平台支持以startTime为起点，前后n日的时间序列查询(abs(n) < 10000)，
    :param dayType: 日期类型，枚举整数类型，当frequency 参数为FrequencyType.WEEK 时，默认值为DayType.FRIDAY；当frequency 参数为其它值，默认值为DayType.FIRSTDAY。
    :param dateType: 日历类型，枚举整数类型，默认值为DateType.TRADINGDAYS。
    :param marketType: 市场类型，枚举整数类型，默认值：MarketType.SH。暂时指定了两个市场，后续再拓展
    :return: 交易日期，double类型列表


    - FrequencyType 数据频率 参数枚举值说明
        ==========  =====   =========
        类型名称     数值    类型说明
        DAY         1       %日
        WEEK        2       %周
        MONTH       3       %月
        QUARTER     4       %季
        HALFYEAR    5       %半年
        YEAR        6       %年
        ==========  =====   =========

    - DayType 日期类型 参数枚举值说明

        ========== ===== ============
        类型名称    数值  类型说明
        MONDAY     1     %周一
        TUESDAY    2     %周二
        WEDNESDAY  3     %周三
        THURSDAY   4     %周四
        FRIDAY     5     %周五
        SATURDAY   6     %周六
        SUNDAY     7     %周日
        FIRSTDAY   8     %第一天
        LASTDAY    9     %最后一天
        ========== ===== ============

    - DateType 日历类型 参数枚举值说明

        ============  =====   ========
        类型名称       数值    类型说明
        ALLDAYS        1      %日历日
        TRADINGDAYS    2      %交易日
        ============  =====   ========

    - MarketType 市场类型 参数枚举值说明

        ========  =====  ==============
        类型名称   数值   类型说明
        SH        1      %上海证券交易所
        SZ        2      %深圳证券交易所
        ========  =====  ==============

    """
    if startTime is None or endTime is None or startTime == [] or endTime == []:
        print('[tradingDay]参数startTime、endTime为空，请重新输入！')
        return
    if list == type(startTime):
        startTime = startTime[0]
    if list == type(endTime):
        endTime = endTime[0]
    if list == type(frequencyType):
        frequencyType = frequencyType[0]
    if list == type(dayType):
        dayType = dayType[0]
    if list == type(dateType):
        dateType = dateType[0]
    if list == type(marketType):
        marketType = marketType[0]

    if not isinstance(startTime, int) or not isinstance(endTime, int):
        print('[tradingDay]参数startTime、endTime非整数型，请重新输入！')
        return
    if frequencyType == FrequencyType.WEEK and dayType == DayType.LASTDAY:
        dayType = DayType.FRIDAY
    if not isinstance(frequencyType, FrequencyType):
        print('[tradingDay]输入参数frequencyType非正确枚举类型，请重新输入！')
        return
    if not isinstance(dayType, DayType):
        print('[tradingDay]输入参数dayType非正确枚举类型，请重新输入！')
        return
    if not isinstance(dateType, DateType):
        print('[tradingDay]输入参数dateType非正确枚举类型，请重新输入！')
        return
    if not isinstance(marketType, MarketType):
        print('[tradingDay]输入参数marketType非正确枚举类型，请重新输入！')
        return

    method = 1
    if frequencyType == FrequencyType.DAY:
        if endTime > 19900000:
            method = 1
        elif abs(endTime) < 10000:  # 前后多少天的查询方式
            method = 2
            tmpTime = endTime
            if dateType == DateType.TRADINGDAYS:
                if endTime >= 0:
                    endTime = int((datetime.datetime.strptime(str(startTime), '%Y%m%d') + datetime.timedelta(
                        tmpTime + 121 * math.ceil(endTime / 365))).strftime('%Y%m%d'))
                else:
                    tmpTime = endTime
                    endTime = startTime
                    startTime = int((datetime.datetime.strptime(str(endTime), '%Y%m%d') + datetime.timedelta(
                        tmpTime + 121 * math.floor(tmpTime / 365))).strftime('%Y%m%d'))
            else:
                if endTime >= 0:
                    endTime = int((datetime.datetime.strptime(str(startTime), '%Y%m%d') + datetime.timedelta(
                        endTime - 1)).strftime('%Y%m%d'))
                else:
                    tmpTime = endTime
                    endTime = startTime
                    startTime = int(
                        (datetime.datetime.strptime(str(endTime), '%Y%m%d') + datetime.timedelta(tmpTime + 1)).strftime(
                            '%Y%m%d'))
        else:
            print('[tradingDay]参数endTime输入值超出有范围，请重新输入!')
            return

    if frequencyType == FrequencyType.WEEK and dayType not in [DayType.MONDAY, DayType.TUESDAY, DayType.WEDNESDAY,
                                                               DayType.THURSDAY, DayType.FRIDAY]:
        print('[tradingDay]当参数frequencyType为WEEK时，dayType只能为[DayType.MONDAY,DayType.FRIDAY]中数值，请重新输入！')
        return

    if frequencyType in [FrequencyType.MONTH, FrequencyType.QUARTER, FrequencyType.HALFYEAR, FrequencyType.YEAR] and (
                    dayType != DayType.FIRSTDAY and dayType != DayType.LASTDAY):
        print(
            '[tradingDay]当参数frequencyType为MONTH,QUARTER, HALF YAER, YEAR时，dayType只能为[DayType.FIRSTDAY,DayType.LASTDAY]中数值，请重新输入！')
        return

    if startTime > endTime:
        print('[tradingDay]参数startTime输入值大于参数endTime输入值，请重新输入!')
        return

    # dbPath = 'http://eip.htsc.com.cn/QuantiveService/DataSetService/'
    urlVersion = '0161'
    url = dbPath + 'getTradingDays'
    userid, session, ipaddr = getQPUserInfo()  # 获取用户登录信息
    # 传递参数获取数据
    parms = urllib.parse.urlencode({'apiparam': urlVersion, 'userid': userid, 'session': session, 'ipaddr': ipaddr,
                                    'startdatetime': str(startTime), 'enddatetime': str(endTime),
                                    'frequencytype': str(frequencyType.value), 'daytype': str(dayType.value),
                                    'datetype': str(dateType.value), 'markettype': str(marketType.value)})
    parms = parms.encode('utf-8')
    data = urllib.request.urlopen(url, parms)
    data = data.read().decode('utf-8')
    beginoffset = data.find(';')
    data = ('[' + data[beginoffset + 1:-1] + ']').replace(';', ',')
    data = eval(data)
    if 2 == method:
        if tmpTime > 0:
            data = data[:tmpTime]
        else:
            data = data[len(data) + tmpTime:]

    return data


## Description 根据输入的板块类型、日期及板块代码查询该板块的成分股信息
## Inputs:
#   plateType：  板块类型，枚举数据，例如： PlateType.INDEX
#   dateTime：  查询日期,数值型，例如：20151231
#   plateID：   板块代码，当plateType为INDEX时，plateID输入为指数代码，枚举整数类型，例如：IndexType.HS300。
#           当plateType为MARKET时，plateID输入为市场代码枚举，例如MarketType.SZA。
#           当参数plateType 为行业板块时，plateID为行业代码，具体需参见CITICS，SW等行业枚举定义，输入例如：CITICS.b106040700
## Outputs:
#   StockList：  股票代码列表，3行List：股票代码，股票名称，股票权重。
@statisticLog('thirdpartydata','QuantAPI')
def hset(plateType=PlateType.INDEX, dateTime=int(datetime.date.today().strftime("%Y%m%d")), plateID=IndexType.HS300):
    """根据输入的板块类型、日期及板块代码查询该板块的成分股信息

    :param plateType: 板块类型，枚举数据，例如： PlateType.INDEX
    :param dateTime: 查询日期,数值型，例如：20151231
    :param plateID: 板块代码，当plateType为INDEX时，plateID输入为指数代码，枚举整数类型，例如：IndexType.HS300。

        | 当plateType为MARKET时，plateID输入为市场代码枚举，例如MarketType.SZA。
        | 当参数plateType 为行业板块时，plateID为行业代码，具体需参见CITICS，SW等行业枚举定义，输入例如：CITICS.b106040700
    :return: 股票代码列表，3行List：股票代码，股票名称，股票权重。

    - PlateType 板块类型 参数枚举值说明

        ==========  =====  =========
        类型名称     数值   类型说明
        SECTOR      1      概念板块
        INDEX       2      指数板块
        MARKET      3      市场板块
        INDUSTRY    4      行业板块
        ==========  =====  =========

    - IndexType 行业代码 参数枚举值说明

        ============  =====  ===========  =============
        类型名称       数值   类型说明      数据开始日期
        HS300         1      沪深300指数   20050411
        ZZ500         2      中证500指数   20100104
        SH50          3      上证50指数    20100104
        ============  =====  ===========  =============

    - IndustryType 行业分类代码 参数枚举值说明

        ========  =====  ==============
        类型名称   数值   类型说明
        CSRC      1      证监会行业分类
        CITICS    2      中信行业分类
        SW        3      申万行业分类
        ========  =====  ==============

    - MarketType 参数枚举值说明

        ========   =====  ========
        类型名称    数值   类型说明
        ALLA       0      全部A股
        SHA        1      上海A股
        SZA        2      深圳A股
        SME        3      中小板
        GEM        5      创业板
        ========   =====  ========
    """
    
    if plateType == []:
        print('[hset函数]参数plateType为空，请重新输入！')
        return
    if list == type(dateTime):
        dateTime = dateTime[0]
    if list == type(plateType):
        plateType = plateType[0]
    if list == type(plateID):
        plateID = plateID[0]

    if not isinstance(plateType, PlateType):
        print('[hset函数]输入参数plateType非正确类型，请重新输入！')
        return

    if plateType == PlateType.INDUSTRY:
        if not (isinstance(plateID, CITICS) or isinstance(plateID, SW) or isinstance(plateID, CSRC)):
            print('[hset]当参数plateType为PlateType.INDUSTRY，plateID需为行业分类CITICS、CSRC或者SW行业代码枚举值，请重新输入！')
            return
    elif plateType == PlateType.INDEX:
        if not isinstance(plateID, IndexType):
            print('[hset]当参数plateType为PlateType.INDEX时，plateID需为指数代码枚举值，请重新输入！')
            return
    elif plateType == PlateType.MARKET:
        if not isinstance(plateID, MarketType):
            print('[hset]当参数plateType为PlateType.MARKET，plateID需为市场代码枚举值，请重新输入！')
            return
    # dbPath = 'http://eip.htsc.com.cn/QuantiveService/DataSetService/'
    urlVersion = '0161'
    userid, session, ipaddr = getQPUserInfo()  # 获取用户登录信息
    if plateType == PlateType.INDUSTRY:
        industrycode = plateID.name
        if plateID.value < 1000:
            industryType = IndustryType.CSRC  # 证监会行业分类
            industrycode = industrycode[1:len(industrycode)]  # 枚举编码的时候多写了一个c在前面，在数据库中查询时需要过滤掉
        elif 1000 <= plateID.value < 2000:
            industryType = IndustryType.CITICS  # 中信行业分类
        elif 2000 <= plateID.value < 3000:
            industryType = IndustryType.SW  # 申万行业分类
            industrycode = industrycode[1:len(industrycode)]  # 枚举编码的时候多写了一个s在前面，在数据库中查询时需要过滤掉

        url = dbPath + 'getStockSetBySector'
        parms = urllib.parse.urlencode(
            {'apiparam': urlVersion, 'userid': userid, 'session': session, 'ipaddr': ipaddr, 'datetime': str(dateTime),
             'sectorid': industrycode, 'industryid': str(industryType.value)})
    elif plateType == PlateType.MARKET:
        url = dbPath + 'getStockSetA'
        parms = urllib.parse.urlencode(
            {'apiparam': urlVersion, 'userid': userid, 'session': session, 'ipaddr': ipaddr, 'datetime': str(dateTime),
             'sectorid': str(plateID.value)})
    elif plateType == PlateType.INDEX:
        url = dbPath + 'getWeightSetByIndex'
        parms = urllib.parse.urlencode(
            {'apiparam': urlVersion, 'userid': userid, 'session': session, 'ipaddr': ipaddr, 'datetime': str(dateTime),
             'indextype': str(plateID.value)})
    else:
        print('[hset]函数暂不支持该模式数据提取，请联系开发人员！')
        return
    # 传递参数获取数据
    parms = parms.encode('utf-8')
    data = urllib.request.urlopen(url, parms)
    data = data.read().decode('utf-8')
    beginoffset = data.find(';')
    if 0 < beginoffset:
        data = ('[[' + data[beginoffset + 1:-1] + ']]').replace(';', '],[')
        data = eval(data)
        data = list(map(list, zip(*data)))
    else:
        data = []
    return data

@statisticLog('thirdpartydata','QuantAPI')
def hsi(stockList=[], dateTime=int(datetime.date.today().strftime("%Y%m%d")), industryType=0, industryLevel=3):
    
    if stockList == []:
        print('[hsi函数]参数stockList为空，请重新输入！')
        return
    if list == type(dateTime):
        dateTime = dateTime[0]
    if list != type(stockList):
        stockList = [stockList]

    if 0 != industryType and not isinstance(industryType, IndustryType):
        print('[hsi函数]输入参数industryType非正确类型，请重新输入！')
        return

    # dbPath = 'http://eip.htsc.com.cn/QuantiveService/DataSetService/'
    urlVersion = '0161'
    userid, session, ipaddr = getQPUserInfo()  # 获取用户登录信息
    url = dbPath + 'getIndustryClassBySymbols'
    jssblst = ','.join(stockList)
    jssblst = '[' + jssblst.replace(',', '],[') + ']'
    jssblst = jssblst.replace('[', '["')
    jssblst = '[' + jssblst.replace(']', '"]') + ']'
    parms = urllib.parse.urlencode(
        {'apiparam': urlVersion, 'userid': userid, 'session': session, 'ipaddr': ipaddr, 'datetime': str(dateTime),
         'jssymbols': jssblst,'nclass': industryLevel})
    # 传递参数获取数据
    parms = parms.encode('utf-8')
    data = urllib.request.urlopen(url, parms)
    data = data.read().decode('utf-8')
    beginoffset = data.find(';')
    if 0 < beginoffset:
        data = ('[[' + data[beginoffset + 1:-1] + ']]').replace(';', '],[')
        data = eval(data)
    else:
        return []

    # 过滤掉第二列日期
    data = [[x[0], x[2], x[3], x[4]] for x in data]
    if 0 == industryType:
        data = [x for x in data if x[3] != 'WIND']
    else:
        # 根据行业类别提取相应的数据
        if IndustryType.SW == industryType:
            data = [x for x in data if x[3] == 'SW']
        elif IndustryType.CSRC == industryType:
            data = [x for x in data if x[3] == 'CSRC']
        else:
            data = [x for x in data if x[3] == 'CITICS']
    return data


## Description 本API用于过滤股票池中不符合条件的股票。一共两层过滤，第一次过滤掉STPT，停牌，开盘涨停等股票，第二层过滤是根据EPS，PE等指标的取值范围过滤。
## Inputs:
#   stockPool：  股票代码列表，例如：{'000001.SZ';'601688.SH'};
#   filterDate： 查询日期,数值型，例如：20151231
#   filterType： 过滤类型，为枚举类型，过滤类型，枚举字段，默认为过滤掉STPT，停牌，开盘涨停的股票，引用格式：StockFilterType.SSO
#   filterFactors：    可选的过滤指标列表，cell类型列向量，因子内容为枚举数据，例如：[Factors.eps_basic;Factors.roe_diluted]
#   factorFloorValue： 过滤因子指标下限值，列向量，顺序须与filterFactors中因子顺序一致，例如：[1;0.6]。
#   factorCeilValue：  过滤因子指标上限值，列向量，顺序须与filterFactors中因子顺序一致，例如：[1;2.6]。
## Outputs:
#   stkcdList       - 股票代码列表，cell数组
def stockFilter(stockPool=[], dateTime=int(datetime.date.today().strftime("%Y%m%d")), filterType=StockFilterType.SSO,
                filterFactors=[], factorFloorValue=[], factorCeilValue=[]):
    """本API用于过滤股票池中不符合条件的股票。一共两层过滤，第一次过滤掉STPT，停牌，开盘涨停等股票，第二层过滤是根据EPS，PE等指标的取值范围过滤。

    :param stockPool: 股票代码列表，例如：{'000001.SZ';'601688.SH'};
    :param dateTime: 查询日期,数值型，例如：20151231
    :param filterType: 过滤类型，为枚举类型，过滤类型，枚举字段，默认为过滤掉STPT，停牌，开盘涨停的股票，引用格式：StockFilterType.SSO
    :param filterFactors: 可选的过滤指标列表，cell类型列向量，因子内容为枚举数据，例如：[Factors.eps_basic;Factors.roe_diluted]
    :param factorFloorValue: 过滤因子指标下限值，列向量，顺序须与filterFactors中因子顺序一致，例如：[1;0.6]。
    :param factorCeilValue: 过滤因子指标上限值，列向量，顺序须与filterFactors中因子顺序一致，例如：[1;2.6]。
    :return: 股票代码列表，cell数组
    """
    if stockPool == []:
        print('[stockFilter函数]参数stockList为空，请重新输入！')
        return
    if list != type(stockPool):
        stockPool = [stockPool]
    if list != type(filterFactors):
        filterFactors = [filterFactors]
    if list != type(factorFloorValue):
        factorFloorValue = [factorFloorValue]
    if list != type(factorCeilValue):
        factorCeilValue = [factorCeilValue]
    if list == type(filterType):
        filterType = filterType[0]
    if list == type(dateTime):
        dateTime = dateTime[0]

    if filterType != [] and not isinstance(filterType, StockFilterType):
        print('[stockFilter函数]输入参数filterType非正确类型，请重新输入！')
        return
    if filterFactors != [] and False in [isinstance(x, Factors) for x in filterFactors]:
        print('[stockFilter函数]输入参数filterFactors非正确类型，请重新输入！')
        return
    if True in [filterFactors == [], factorFloorValue == [], factorCeilValue == []] and True in [filterFactors != [],
                                                                                                 factorFloorValue != [],
                                                                                                 factorCeilValue != []]:
        print('[stockFilter函数]输入参数filterFactors,factorFloorValue,factorCeilValue必须同时为空或同时非空，请重新输入！')
        return
    if filterFactors != [] and (
                    len(filterFactors) != len(factorFloorValue) or len(filterFactors) != len(factorCeilValue)):
        print('[stockFilter函数]输入参数filterFactors,factorFloorValue,factorCeilValue维数不等，请重新输入！')
        return

    # dbPath = 'http://eip.htsc.com.cn/QuantiveService/DataSetService/'
    urlVersion = '0161'
    userid, session, ipaddr = getQPUserInfo()  # 获取用户登录信息
    url = dbPath + 'filterSymbols'
    # 拼代码字符串
    jssblst = ','.join(stockPool)
    jssblst = '[' + jssblst.replace(',', '],[') + ']'
    jssblst = jssblst.replace('[', '["')
    jssblst = '[' + jssblst.replace(']', '"]') + ']'
    # 拼查询条件字符串
    a = ['{"FACTOR":"'] * len(filterFactors)
    b = ['","lstparam":[{"PNAME":"intervaltype","PVALUE":"'] * len(filterFactors)
    c = ['"}]}'] * len(filterFactors)
    d = [a, [x.name for x in filterFactors], b, [str(x) for x in factorFloorValue], [','] * len(filterFactors),
         [str(x) for x in factorCeilValue], c]
    e = list(map(list, zip(*d)))
    jsfactorlist = '[' + ','.join([''.join(x) for x in e]) + ']'
    parms = urllib.parse.urlencode(
        {'apiparam': urlVersion, 'userid': userid, 'session': session, 'ipaddr': ipaddr, 'startdatetime': str(dateTime),
         'enddatetime': str(dateTime), 'filtertype': str(filterType.value), 'jssymbols': jssblst,
         'jsfactors': jsfactorlist})
    # 传递参数获取数据
    parms = parms.encode('utf-8')
    data = urllib.request.urlopen(url, parms)
    data = data.read().decode('utf-8')
    beginoffset = data.find(';')
    if 0 < beginoffset:
        data = ('[[' + data[beginoffset + 1:-1] + ']]').replace(';', '],[')
        data = eval(data)
        # 过滤掉第二列日期
        data = [[x[0], x[2]] for x in data]
        data = list(map(list, zip(*data)))
    else:
        return []
    return data


## Description 根据用户ID和Session查询数据表名
## Inputs:
## Outputs:
#   tableList： 数据表名列表
def queryUserTables():
    # dbPath = 'http://eip.htsc.com.cn/QuantiveService/DataSetService/'
    urlVersion = '0161'
    url = dbPath + 'queryUserTables'
    userid, session, ipaddr = getQPUserInfo()  # 获取用户登录信息
    # 传递参数获取数据
    parms = urllib.parse.urlencode({'apiparam': urlVersion, 'userid': userid, 'session': session, 'ipaddr': ipaddr})
    parms = parms.encode('utf-8')
    data = urllib.request.urlopen(url, parms)
    data = data.read().decode('utf-8')
    data = ('[[' + data[1:-1] + ']]').replace(';', '],[')
    data = eval(data)
    return data


## Description 根据用户ID和Session、数据表名返回数据表字段信息
## Inputs:
#   tablename：      数据表名，例如：QD_INDEX_WEIGHTS
## Outputs:
#   tableInfoList：  数据表信息，3行List，包括字段名称、字段类型、备注信息三列。
def queryUserTableInfo(tablename):
    # dbPath = 'http://eip.htsc.com.cn/QuantiveService/DataSetService/'
    urlVersion = '0161'
    url = dbPath + 'queryUserTableInfo'
    userid, session, ipaddr = getQPUserInfo()  # 获取用户登录信息
    # 传递参数获取数据
    parms = urllib.parse.urlencode(
        {'apiparam': urlVersion, 'userid': userid, 'session': session, 'ipaddr': ipaddr, 'tablename': tablename})
    parms = parms.encode('utf-8')
    data = urllib.request.urlopen(url, parms)
    data = data.read().decode('utf-8')
    data = ('[[' + data[1:-1] + ']]').replace(';', '],[')
    data = eval(data)
    return data


## Description 本API将根据用户传入的SQL语句，返回结果数据集。
## Inputs:
#   sqlStr：     sql语句字符串，例如：select * from app_finance_news_amount where rownum <=10;
#   dataNumber： 数据记录条数 ,0表示不限制，其他数字表示返回的数据条数，不足dataNumber的数目时，返回全部记录，默认返回1000条。
## Outputs:
#   factorData： 查询的结果数据集，多行List，第一行为列名称。
def queryUserTableData(sqlStr='', rownum=1000):
    if sqlStr == '':
        print('[queryUserTableData函数]参数queryUserTableData为空，请重新输入！')
        return
    # dbPath = 'http://eip.htsc.com.cn/QuantiveService/DataSetService/'
    urlVersion = '0161'
    url = dbPath + 'queryUserTableDataset'
    userid, session, ipaddr = getQPUserInfo()  # 获取用户登录信息
    # 传递参数获取数据
    parms = urllib.parse.urlencode(
        {'apiparam': urlVersion, 'userid': userid, 'session': session, 'ipaddr': ipaddr, 'rownum': str(rownum),
         'strsql': sqlStr})
    parms = parms.encode('utf-8')
    data = urllib.request.urlopen(url, parms)
    data = data.read().decode('utf-8')
    NAN = None
    data = ('[[' + data[1:-1] + ']]').replace(';', '],[')
    data = eval(data)
    return data


## Description 读注册表返回用户ID，用户IP，用户Session
## Inputs:
## Outputs:
#   userid： 用户ID字符串
#   ipaddr： 用户IP字符串
#   session： 用户session字符串
def getQPUserInfo(isWindows=False):

    if isWindows == False:
        userid = "linux"
        session = "linux"
        ipaddr = "linux"
        return userid, session, ipaddr

    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\QuantPF")
        userid, type = winreg.QueryValueEx(key, "userid")
        session, type = winreg.QueryValueEx(key, "session")
        ipaddr, type = winreg.QueryValueEx(key, "ipaddr")
    except:
        try:
            key, type = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\QuantPF")
            userid, type = winreg.QueryValueEx(key, "userid")
            session, type = winreg.QueryValueEx(key, "session")
            ipaddr, type = winreg.QueryValueEx(key, "ipaddr")
        except:
            userid = '000000'
            session = 'Invalid session'
            ipaddr = 'Invalid IP'
    return userid, session, ipaddr


## Description:
#   本API用于查询指定股票列表的时间序列因子数据，或者横截面因子数据。通过输入股票列表、因子列表以及起止日期，输出不同因子类型下的因子数值。
## Inputs:
# 	stockList ： 股票代码列表，字符型cell列向量，例如：{‘000001.SZ’;’601688.SH’};
# 	factorList ： 因子名称列表，枚举列向量，例如：[Factors.high;Factors.low]。详情请见因子列表;
#       dateList:	数据日期列表，数值型列向量，格式 yyyymmdd,例如: [20100861;20100921]
#                 对于区间计算的因子，或者N日统计的因子，只需要传入两个时间即可：
#                 1）对于区间计算的因子，传入[开始时间; 结束时间]即可，例如要统计 20120314到20120514之间的日均成交量，则输入[20120314;20120514]即可;
#                 2）对于N日计算的因子，传入[开始时间; N日]即可，例如要统计 20120314后面10天换手率，则输入[20120314;10]即可，当需要查询前面10天的时候，输入[20120314;-10]即可;
#                   注：1）当查询周数据时，请传入6位日期数字，yyyyww，表示第yyyy年第ww周，例如：[201512;201602]，表示2015年第12周和2016年第2周；
#                       2）当查询月数据时，请传入6位日期数字，yyyymm，表示第yyyy年第mm月，例如：[201512;201602]，表示2015年12月和2016年2月；
#                       3）当查询年数据时，请传入4位日期数据，yyyy，表示第几年，例如：[2015;2016]，表示2015年和2016年。
#                 3）对于一致预期衍生因子，传入[报告起始披露日期; 预测年度]即可，例如传入:[20120702;2013]即可查询出20120702以后所有预测的2013年的因子数据；
#                 当要查询预测年度的所有数据时，报告披露日期为nan即可，例如: [nan;2013]；对某些没有预测年度的因子，预测年度值置为nan即可，例如：[20120702;nan]。
#       factorPar： 特殊参数类型，枚举类型列向量，如无特殊需求可不填。
## Outputs:
#       factorData，因子数据，多维List，第一层是查询因子列表，第二层是因子名称及因子数值，第三层是因子数值二维List，其行为股票代码索引，列为日期索引。
#            因子数据矩阵的行索引、列索引请见stkCodeList、resultDateList两个数组。
#       stkCodeList, 股票代码列表，cell类型列向量
#       resultDateList,	查询结果日期列表，数值型列向量，格式 yyyymmdd,例如: [20100861,20100921]
#         温馨提示： 为了加快查询速度，系统对输入的股票代码、日期进行了去除空格、过滤重复项、统一大小写等处理，
#         会导致输出的stockCodeList、resultDateList与输入的stkcdList, dateList数据内容可能不一致，使用因子的索引请以最终输出的stkcdList, dateList为准。
@statisticLog('thirdpartydata','QuantAPI')
def hfactor(stockList=[], factorList=[], dateList=[], factorPar=[]):
    """本API用于查询指定股票列表的时间序列因子数据，或者横截面因子数据。通过输入股票列表、因子列表以及起止日期，输出不同因子类型下的因子数值。

    :param stockList: 股票代码列表，字符型cell列向量，例如：{‘000001.SZ’;’601688.SH’};
    :param factorList: 因子名称列表，枚举列向量，例如：[Factors.high;Factors.low]。详情请见因子列表;
    :param dateList: 数据日期列表，数值型列向量，格式 yyyymmdd,例如: [20100816;20100921]。  对于区间计算的因子，或者N日统计的因子，只需要传入两个时间即可：

        - 1）对于区间计算的因子，传入[开始时间; 结束时间]即可，例如要统计 20120314到20120514之间的日均成交量，则输入[20120314;20120514]即可;

        - 2）对于N日计算的因子，传入[开始时间; N日]即可，例如要统计 20120314后面10天换手率，则输入[20120314;10]即可，当需要查询前面10天的时候，输入[20120314;-10]即可;

        | 注：

            + 1）当查询周数据时，请传入6位日期数字，yyyyww，表示第yyyy年第ww周，例如：[201512;201602]，表示2015年第12周和2016年第2周；

            + 2）当查询月数据时，请传入6位日期数字，yyyymm，表示第yyyy年第mm月，例如：[201512;201602]，表示2015年12月和2016年2月；

            + 3）当查询年数据时，请传入4位日期数据，yyyy，表示第几年，例如：[2015;2016]，表示2015年和2016年。

        - 3）对于一致预期衍生因子，传入[报告起始披露日期; 预测年度]即可，例如传入:[20120702;2013]即可查询出20120702以后所有预测的2013年的因子数据；

        | 当要查询预测年度的所有数据时，报告披露日期为nan即可，例如: [nan;2013]；对某些没有预测年度的因子，预测年度值置为nan即可，例如：[20120702;nan]。

    :param factorPar: 特殊参数类型，枚举类型列向量，如无特殊需求可不填。
    :return: factorData，因子数据，多维List，第一层是查询因子列表，第二层是因子名称及因子数值，第三层是因子数值二维List，其行为股票代码索引，列为日期索引。因子数据矩阵的行索引、列索引请见stkCodeList、resultDateList两个数组。
        stkCodeList, 股票代码列表，cell类型列向量

        | resultDateList,查询结果日期列表，数值型列向量，格式 yyyymmdd,例如: [20100816,20100921]

        :温馨提示： 为了加快查询速度，系统对输入的股票代码、日期进行了去除空格、过滤重复项、统一大小写等处理，会导致输出的stockCodeList、resultDateList与输入的stkcdList, dateList数据内容可能不一致，使用因子的索引请以最终输出的stkcdList, dateList为准。

        - FactorType 因子类型 参数枚举值说明

            ==============  ======  ======================================
            类型名称         数值    类型说明
            UNADJUSTED       1      不复权价格
            FORWARD          2      前复权价格
            BACKWARD         3      后复权价格
            COMBINED         11     合并报表
            COMBINED_SS      12     合并报表(单季度
            COMBINED_SSA     13     合并报表(单季度调整
            COMBINED_A       14     合并报表(调整
            COMBINED_NM      15     合并报表(更正前
            PARENT           16     母公司报表
            PARENT_SS        17     母公司报表(单季度
            PARENT_SSA       18     母公司报表(单季度调整
            PARENT_A         19     母公司报表(调整
            PARENT_NM        20     母公司报表(更正前
            EXDISTDT         31     以除权出息日为基期，数据库中值为1
            DIVDT            32     以派息日为基期，数据库中值为2
            CESTOCK          51     股票
            CEINDEX          52     指数
            CEINDUSTRY       54     行业
            CEHS300          55     沪深300行业
            CESH180          56     上证180行业
            CESH015          57     红利指数行业
            CESH050          58     上证50行业
            CEZZ100          59     中证100行业
            CESZ100          60     深证100行业
            CESZ101          61     中小板综合指数
            CEJC040          62     巨潮40行业
            CEJC300          63     巨潮300行业
            CEJC100          64     巨潮100行业
            CEZB300          65     中标300行业
            CEZB050          66     中标50行业
            CEXF050          67     新富A50行业
            CEDZ088          68     道中88行业
            CESH001          69     上证A股行业
            CESH043          70     超大盘行业
            CEZZ500          71     中证500行业
            CEZZ700          72     中证700行业
            CESZ005          73     中小板指行业
            CESZ006          74     创业板指数行业
            CESH067          75     上证新兴行业
            CEZZ800          76     中证800行业
            CEQ1             81     一致预期一季报
            CEHY             82     一致预期中报
            CEQ3             83     一致预期三季报
            CEAN             84     一致预期年报
            CEM0             90     一致预期:真实财务数据
            CEM1             91     一致预期:加权计算
            CEM2             92     一致预期:手工估算
            CEM3             93     一致预期:数据模拟
            CEM4             94     一致预期:沿用数据
            ==============  ======  ======================================
    """

    if stockList == [] or factorList == [] or dateList == []:
        print('[hfactor函数]参数stockList、factorList或dateList为空，请重新输入！')
        return
    if list != type(stockList):
        stockList = [stockList]
    if list != type(factorList):
        factorList = [factorList]
    if list != type(dateList):
        dateList = [dateList]
    if list != type(factorPar):
        factorPar = [factorPar]
    if factorPar != [] and False in [isinstance(x, FactorType) for x in factorPar]:
        print('[hfactor函数]输入参数factorPar非正确类型，请重新输入！')
        return
    if factorList != [] and False in [isinstance(x, Factors) for x in factorList]:
        print('[hfactor函数]输入参数factorList非正确类型，请重新输入！')
        return
    # 获取数据服务器连接信息
    # dbPath = 'http://eip.htsc.com.cn/QuantiveService/DataSetService/'
    urlVersion = '0161'
    userid, session, ipaddr = getQPUserInfo()  # 获取用户登录信息
    url = dbPath + 'getFactors'
    # 判断查询类型
    factorList = list(set(factorList))
    lenFactor = len(factorList)
    factorValue = [x.value for x in factorList]
    dataExtractType = 0  # 0表示普通查询，1表示区间统计，2表示N日计算，3表示一致预期个股数据查询，4表示一致预期个股或板块的某一年度所有预测数据查询
    if True in [(81 <= x <= 109) or (151 <= x <= 164) or (367 <= x <= 368) for x in factorValue]:  # 区间统计因子，后面只带一个参数
        dataExtractType = 1
    elif True in [(110 <= x <= 123) or (338 <= x <= 355) for x in factorValue]:  # 以某个时间点计算N日指标，后面只带一个参数
        dataExtractType = 2
        if dateList[1] > 10000 or dateList[1] < -10000:
            print('[hfactor]输入的N值太大，超出现有数据时间范围，请重新输入!')
            return
    elif True in [386 <= x <= 416 for x in factorValue]:  # 股票最新信息查询，后面不带参数，日期默认为历史最早日期
        dateList = [19700101, 19700101]
        dataExtractType = 1
    elif True in [2001 <= x <= 2258 for x in factorValue]:
        dataExtractType = 3  # 提取个股或板块某一天的一致预期数据，后面可能有两个参数
        if 9 == len(stockList[0]):
            stockList = [y[0] for y in
                         [x.split('.') for x in stockList]]  # 朝阳永续数据库中的代码长度不规范，而万得数据库中代码后缀是.SZ和.SH，输入标准参考万得代码规范
        if dateList[0] is None:
            dataExtractType = 4  # 提取个股或板块某一年的所有一致预期数据
            dateList = [19800101, dateList[1]]
        if dateList[1] is None:  # 提取个股或板块某一个截止日期的一致预期数据
            dateList = [dateList[0], 19800101]
    # 获取参数类型及数值列表
    stockList = sorted(list(set(stockList)))
    factorPar = list(set(factorPar))
    parValue = [x.value for x in factorPar]
    factorName = [x.name for x in factorList]
    factorList = [factorName]
    # 拼参数列表
    if factorPar != []:
        # 拼因子矩阵，按照与下游的协议，每个因子指标后面给出一列参数字段值，再给出一列具体数值
        if 2 >= dataExtractType:
            if 10 >= parValue[0]:  # 0~10之间是行情数据枚举值，详情可以查阅 PriceType.m
                factorList.append(['priceType'] * lenFactor)
                factorList.append([str(parValue[0])] * lenFactor)
            elif 20 >= parValue[0]:  # 10~20之间是财务报表数据枚举值，详情可以查阅 ReportType.m
                factorList.append(['reportType'] * lenFactor)
                factorList.append([str(parValue[0] - 10)] * lenFactor)
            elif 40 >= parValue[0]:  # 31~40之间是除权出息基准日期枚举值，详情可以查阅 DivdDateType.m
                factorList.append(['divdDateType'] * lenFactor)
                factorList.append([str(parValue[0] - 30)] * lenFactor)
            else:
                if 2 == dataExtractType:  # N日查询或者区间统计
                    factorList.append(['fcount'] * lenFactor)
                    factorList.append([str(dateList[1])] * lenFactor)
        elif 3 <= dataExtractType:  # 一致预期数据
            if 80 >= parValue[0]:  # 51~80之间是一致预期组合枚举值，详情可以查阅 FactorType.m
                codeType = ['stocktype'] * lenFactor
                b = [x for x in range(lenFactor) if 2200 <= factorValue[x] <= 2212]
                if b != []:
                    for x in b:
                        codeType[x] = 'blocktype'
                factorList.append(codeType)
                factorList.append([str(parValue[0] - 50)] * lenFactor)
                factorList.append(['rpttype'] * lenFactor)
                factorList.append(['4'] * lenFactor)
            elif 90 >= parValue[0]:
                factorList.append(['rpttype'] * lenFactor)
                factorList.append([str(parValue[0] - 80)] * lenFactor)
            elif 100 >= parValue[0]:
                factorList.append(['contype'] * lenFactor)
                factorList.append([str(parValue[0] - 90)] * lenFactor)
                factorList.append(['rpttype'] * lenFactor)
                factorList.append(['4'] * lenFactor)

            if 2 == len(factorPar):
                if 80 >= parValue[1]:  # 51~80之间是一致预期组合类型枚举值，详情可以查阅 FactorType.m
                    codeType = ['stocktype'] * lenFactor
                    b = [x for x in range(lenFactor) if 2200 <= factorValue[x] <= 2212]
                    if b != []:
                        for x in b:
                            codeType[x] = 'blocktype'
                    factorList.append(codeType)
                    factorList.append([str(parValue[1] - 50)] * lenFactor)
                elif 90 >= parValue[1]:  # 81~90之间是一致预期报表类型枚举值，详情可以查阅 FactorType.m
                    factorList.append(['rpttype'] * lenFactor)
                    factorList.append([str(parValue[1] - 80)] * lenFactor)
                elif 100 >= parValue[1]:  # 90~100之间是一致预期数据处理方法枚举值，详情可以查阅 FactorType.m
                    factorList.append(['contype'] * lenFactor)
                    factorList.append([str(parValue[1] - 90)] * lenFactor)
    else:
        if 0 == dataExtractType:
            if True in [302 == x for x in factorValue]:  # 针对货币资金/短期债务单独处理
                factorList.append(['reportType'] * lenFactor)
                factorList.append(['1'] * lenFactor)
        elif 2 == dataExtractType:
            factorList.append(['fcount'] * lenFactor)
            factorList.append([str(dateList[1])] * lenFactor)  # 默认当前代码类型是个股代码
            if True in [119 <= x <= 122 for x in factorValue]:  # 针对收盘价分位数单独处理
                factorList.append(['priceType'] * lenFactor)
                factorList.append(['1'] * lenFactor)
        elif 3 <= dataExtractType:
            factorList.append(['stocktype'] * lenFactor)
            factorList.append(['1'] * lenFactor)  # 默认当前代码类型是个股代码
            factorList.append(['rpttype'] * lenFactor)
            factorList.append(['4'] * lenFactor)  # 默认处理报表为年报
            factorList.append(['contype'] * lenFactor)
            factorList.append(['1'] * lenFactor)  # 默认处理方法为加权平均计算法
            factorList.append(['blocktype'] * lenFactor)
            factorList.append(['4'] * lenFactor)  # 默认组合类型为行业组合
    # 拼代码字符串
    jssblst = ','.join(stockList)
    jssblst = '[' + jssblst.replace(',', '],[') + ']'
    jssblst = jssblst.replace('[', '["')
    jssblst = '[' + jssblst.replace(']', '"]') + ']'
    # 拼查询条件字符串
    parNum = len(factorList) - 1
    a = ['{"FACTOR":"'] * lenFactor  # 后面接因子名称
    b = ['","lstparam":['] * lenFactor
    c1 = ['{"PNAME":"'] * lenFactor  # 后面跟因子类型名称
    c2 = ['","PVALUE":"'] * lenFactor  # 后面跟因子类型值
    c3 = ['"}'] * lenFactor
    d = [']}'] * lenFactor
    if 0 < parNum:
        c = []
        i = 0
        while i < lenFactor:
            tc = ''
            j = 0
            while j < parNum:
                tc = tc + ''.join([c1[i], factorList[j + 1][i], c2[i], factorList[j + 2][i], c3[i]]) + ','
                j = j + 2
            tc = tc[0:-1]
            c.append(tc)
            i = i + 1
        e = [a, factorList[0], b, c, d]
        del c, i, j
    else:
        e = [a, factorList[0], b, d]
    f = list(map(list, zip(*e)))
    jsfactorlist = '[' + ','.join([''.join(x) for x in f]) + ']'
    del a, b, d, e, f, c1, c2, c3, parNum
    # 查找开始时间和结束时间
    if 2 > dataExtractType:
        startTime = min(dateList)
        endTime = max(dateList)
    elif 2 == dataExtractType:
        startTime = max(dateList)
        endTime = 19700101
    else:
        startTime = max(dateList)
        endTime = min(dateList)

    # 传递参数获取数据
    parms = urllib.parse.urlencode({'apiparam': urlVersion, 'userid': userid, 'session': session, 'ipaddr': ipaddr,
                                    'startdatetime': str(startTime), 'enddatetime': str(endTime), 'jssymbols': jssblst,
                                    'jsfactors': jsfactorlist})
    parms = parms.encode('utf-8')
    data = urllib.request.urlopen(url, parms)
    data = data.read().decode('utf-8')
    beginoffset = data.find(';')
    if 0 < beginoffset:
        data = ('[[' + data[beginoffset + 1:-1] + ']]').replace(';', '],[')
        data = data.replace('NaN', 'None')
        data = eval(data)
    else:
        return [], dateList, stockList

    dateList = sorted(list(set(dateList)))
    if 0 == dataExtractType:
        # 初始化结果矩阵
        rData = [[None]] * lenFactor
        for i in range(lenFactor):
            rData[i] = [factorName[i]]
            rData[i].append([[None] * len(dateList) for i in range(len(stockList))])
        de = enumerate(dateList)
        for item in data:
            stindex = stockList.index(item[1])
            dtindex = [i for i, a in enumerate(dateList) if a == item[2]]
            if dtindex == []:
                continue
            for i in range(lenFactor):
                if item[0] == factorName[i]:
                    rData[i][1][stindex][dtindex[0]] = item[3]
                    break
    else:
        dateList = sorted(list(set([x[2] for x in data])))
        rData = [[None]] * lenFactor
        for i in range(lenFactor):
            rData[i] = [factorName[i]]
            rData[i].append([[None] * len(dateList) for i in range(len(stockList))])

        for item in data:
            stindex = stockList.index(item[1])
            dtindex = dateList.index(item[2])
            for i in range(lenFactor):
                if item[0] == factorName[i]:
                    rData[i][1][stindex][dtindex] = item[3]
                    break

    return rData, dateList, stockList


## Description:
#   本API用于查询日度财务指标指定股票列表的时间序列因子数据，或者横截面因子数据。通过输入股票列表、因子列表以及起止日期，输出不同因子类型下的因子数值。
## Inputs:
# 	stockList ： 股票代码列表，字符型cell列向量，例如：{‘000001.SZ’;’601688.SH’};
# 	factorList ： 因子名称列表，枚举列向量，例如：[Factors.high;Factors.low]。详情请见因子列表;
#   dateList:	数据日期列表，数值型列向量，格式 yyyymmdd,例如: [20100861;20100921]
#   publishDateType,	匹配日期类型，1：会计报表日期，2：公告披露日期，默认公告披露日期
#   factorPar： 财务报表类型，枚举值，默认为合并报表类型。需要查询特殊类型的指标时请用枚举定义引用，例如：FactorType.PARENT。
## Outputs:
#       factorData，因子数据，多维List，第一层是查询因子列表，第二层是因子名称及因子数值，第三层是因子数值二维List，其行为股票代码索引，列为日期索引。
#            因子数据矩阵的行索引、列索引请见stkCodeList、resultDateList两个数组。
#       stkCodeList, 股票代码列表，cell类型列向量
#       resultDateList,	查询结果日期列表，数值型列向量，格式 yyyymmdd,例如: [20100861,20100921]
def hdf(stockList=[], factorList=[], dateList=[], publishDateType=PublishDateType.PUBLISHDAY,
        factorPar=FactorType.COMBINED):
    """本API用于查询日度财务指标指定股票列表的时间序列因子数据，或者横截面因子数据。通过输入股票列表、因子列表以及起止日期，输出不同因子类型下的因子数值。

    :param stockList: 股票代码列表，字符型cell列向量，例如：{‘000001.SZ’;’601688.SH’};
    :param factorList: 因子名称列表，枚举列向量，例如：[Factors.high;Factors.low]。详情请见因子列表;
    :param dateList: 数据日期列表，数值型列向量，格式 yyyymmdd,例如: [20100816;20100921]
    :param publishDateType: 匹配日期类型，1：会计报表日期，2：公告披露日期，默认公告披露日期
    :param factorPar: 财务报表类型，枚举值，默认为合并报表类型。需要查询特殊类型的指标时请用枚举定义引用，例如：FactorType.PARENT。
    :return: factorData，因子数据，多维List，第一层是查询因子列表，第二层是因子名称及因子数值，第三层是因子数值二维List，其行为股票代码索引，列为日期索引。

        | 因子数据矩阵的行索引、列索引请见stkCodeList、resultDateList两个数组。stkCodeList, 股票代码列表，cell类型列向量

        | resultDateList,查询结果日期列表，数值型列向量，格式 yyyymmdd,例如: [20100816,20100921]

    - PublishDateType 匹配日期类型

        ==============  ======  ==========
        类型名称         数值    类型说明
        ACCOUNTINGDAY   1       不复权价格
        PUBLISHDAY      2       前复权价格
        TTM             3       后复权价格
        ==============  ======  ==========

    - FactorType 财务报表类型 不包含一致预期数据 参数枚举值说明

        ==============  =====  ======================
        类型名称         数值   类型说明
        COMBINED        11     合并报表
        COMBINED_SS     12     合并报表(单季度)
        COMBINED_SSA    13     合并报表(单季度调整)
        COMBINED_A      14     合并报表(调整)
        COMBINED_NM     15     合并报表(更正前)
        PARENT          16     母公司报表
        PARENT_SS       17     母公司报表(单季度)
        PARENT_SSA      18     母公司报表(单季度调整)
        PARENT_A        19     母公司报表(调整)
        PARENT_NM       20     母公司报表(更正前)
        ==============  =====  ======================
    """
    if stockList == [] or factorList == [] or dateList == []:
        print('[hdf函数]参数stockList、factorList或dateList为空，请重新输入！')
        return
    if list != type(stockList):
        stockList = [stockList]
    if list != type(factorList):
        factorList = [factorList]
    if list != type(dateList):
        dateList = [dateList]
    if list != type(factorPar):
        factorPar = [factorPar]
    if factorPar != [] and False in [isinstance(x, FactorType) for x in factorPar]:
        print('[hdf函数]输入参数factorPar非正确类型，请重新输入！')
        return
    if factorList != [] and False in [isinstance(x, Factors) for x in factorList]:
        print('[hdf函数]输入参数factorList非正确类型，请重新输入！')
        return
    # 判断查询类型
    factorList = list(set(factorList))
    lenFactor = len(factorList)
    dateList = sorted(list(set(dateList)))
    stockList = sorted(list(set(stockList)))
    factorName = [x.name for x in factorList]
    rData = [[None]] * lenFactor
    for i in range(lenFactor):
        rData[i] = [factorName[i]]
        rData[i].append([[None] * len(dateList) for i in range(len(stockList))])

    if PublishDateType.ACCOUNTINGDAY == publishDateType:  # 匹配会计期间
        # 根据输入的日期计算相应的会计时间
        quaterDate = getQuarterDay(dateList)
        # 提取因子在每个会计期间数据
        factorData, tdate, stkCodeList = hfactor(stockList, factorList, quaterDate, factorPar)
        if factorData is None or factorData == []:
            return [], dateList, stkCodeList
        for item in range(len(factorData)):
            rData[item][0] = factorData[item][0]
            for s in range(len(stockList)):
                for d in range(len(tdate)):
                    for ritem in range(len(dateList)):
                        if quaterDate[ritem] == tdate[d]:
                            rData[item][1][s][ritem] = factorData[item][1][s][d]
    elif PublishDateType.PUBLISHDAY == publishDateType:  # 匹配财务报表实际披露时间
        # 有些报告披露在周末或节假日，需要用自然日期匹配。减去213天是消除0930到0430之间7个月一直不披露报告的极端情况
        date0 = datetime.datetime.strptime(str(min(dateList)), '%Y%m%d') - datetime.timedelta(213)
        i = datetime.timedelta(1)
        date1 = []
        while i < datetime.timedelta(213):
            date1.append(int((date0 + i).strftime('%Y%m%d')))
            i += datetime.timedelta(1)
        date1 = date1 + dateList
        quaterDate = getQuarterDay(date1)
        # 提取每个会计期间的披露日期
        publishDate, tdate, stkCodeList = hfactor(stockList, Factors.stm_issuingdate, quaterDate)
        if publishDate is None or publishDate == []:
            print('[hdf]财务报告披露日期为空')
            return [], dateList, stkCodeList
        # 有些股票的报告披露日期缺失，只能用会计期间数据弥补
        for s in range(len(stkCodeList)):
            for d in range(len(tdate)):
                if publishDate[0][1][s][d] is None or publishDate[0][1][s][d] == "":
                    publishDate[0][1][s][d] = tdate[d]
                else:
                    publishDate[0][1][s][d] = int(publishDate[0][1][s][d])
        # 提取因子在每个会计期间数据
        factorData, tdate, stkCodeList = hfactor(stockList, factorList, tdate, factorPar)
        if factorData is None or factorData == []:
            print('[hdf]因子数据为空')
            return [], dateList, stkCodeList

        for item in range(len(factorData)):
            rData[item][0] = factorData[item][0]
            for s in range(len(stockList)):
                # 该行若出现编译错误，请删除后重写一遍。（编辑器导致出错）
                predata = None
                for d in range(len(publishDate[0][1][0])):
                    for ritem in range(len(dateList)):
                        if dateList[ritem] >= publishDate[0][1][s][d]:
                            if factorData[item][1][s][d] is not None:
                                rData[item][1][s][ritem] = factorData[item][1][s][d]
                                predata = factorData[item][1][s][d]
                            else:
                                rData[item][1][s][ritem] = predata
                                #      factorData,None,stkCodeList = getPublishdateData(stockCodeList,resultDateList,factorList,factorPar)
    elif PublishDateType.TTM == publishDateType:  # 按照披露日期计算的过去12个月财务数据
        # 有些报告披露在周末或节假日，需要用自然日期匹配。减去213天是消除0930到0430之间7个月一直不披露报告的极端情况
        date0 = datetime.datetime.strptime(str(min(dateList)), '%Y%m%d') - datetime.timedelta(722)
        i = datetime.timedelta(1)
        date1 = []
        while i < datetime.timedelta(722):
            date1.append(int((date0 + i).strftime('%Y%m%d')))
            i += datetime.timedelta(1)
        date1 = date1 + dateList
        quaterDate = getQuarterDay(date1)
        # 提取每个会计期间的披露日期
        publishDate, tdate, stkCodeList = hfactor(stockList, Factors.stm_issuingdate, quaterDate)
        if publishDate is None or publishDate == []:
            print('[hdf]财务报告披露日期为空')
            return [], dateList, stkCodeList
        # 有些股票的报告披露日期缺失，只能用会计期间数据弥补
        for s in range(len(stkCodeList)):
            for d in range(len(tdate)):
                if publishDate[0][1][s][d] is None or publishDate[0][1][s][d]=="":
                    publishDate[0][1][s][d] = tdate[d]
                else:
                    publishDate[0][1][s][d] = int(publishDate[0][1][s][d])
        # 提取因子在每个会计期间数据
        factorData, accdate, stkCodeList = hfactor(stockList, factorList, tdate, factorPar)
        if factorData is None or factorData == []:
            print('[hdf]因子数据为空')
            return [], dateList, stkCodeList
        for item in range(len(factorData)):
            rData[item][0] = factorData[item][0]
            for s in range(len(stockList)):
                for d in range(len(publishDate[0][1][0])):
                    for ritem in range(len(dateList)):
                        if dateList[ritem] >= publishDate[0][1][s][d]:
                            quaterDate = accdate[d] - math.floor(accdate[d] / 10000) * 10000
                            if quaterDate == 1231:
                                rData[item][1][s][ritem] = factorData[item][1][s][d]
                            elif quaterDate == 930:
                                rData[item][1][s][ritem] = factorData[item][1][s][d] + factorData[item][1][s][d - 3] - \
                                                           factorData[item][1][s][d - 4]
                            elif quaterDate == 630:
                                rData[item][1][s][ritem] = factorData[item][1][s][d] + factorData[item][1][s][d - 2] - \
                                                           factorData[item][1][s][d - 4]
                            elif quaterDate == 331:
                                rData[item][1][s][ritem] = factorData[item][1][s][d] + factorData[item][1][s][d - 1] - \
                                                           factorData[item][1][s][d - 4]
    return rData, dateList, stockList


# 计算给定日期列表的会计期间
def getQuarterDay(dateList=[]):
    quaterDate = [None] * len(dateList)
    for i in range(len(dateList)):
        dateyear = math.floor(dateList[i] / 10000)
        datequater = math.ceil(math.floor((dateList[i] - dateyear * 10000) / 100) / 3)
        if datequater == 1:
            quaterDate[i] = (dateyear - 1) * 10000 + 1231
        elif datequater == 2:
            quaterDate[i] = dateyear * 10000 + 331
        elif datequater == 3:
            quaterDate[i] = dateyear * 10000 + 630
        elif datequater == 4:
            quaterDate[i] = dateyear * 10000 + 930
    return quaterDate

