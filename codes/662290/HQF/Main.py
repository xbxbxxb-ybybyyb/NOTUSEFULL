import time
import os
import pandas as pd
from System.StrategyManagement import StrategyManagement
from System.Strategy import Strategy
from System.Func import execute
from AlgoConfig_Apple_48 import config,start_date,end_date



def createStrategyManagement():
    strategyManagement = StrategyManagement()
    # 输出文件夹路径, 该路径为HDFS中的路径, 且事先必须不存在, here is the default value 
    userdir = getUserDir()
    if len(userdir) > 0:
        strategyManagement.setDstDir(userdir + '/output/' + 'test{}_test{}'.format(start_date,end_date))
    else:
        strategyManagement.setDstDir(
            '/analysis/xquant/666888/output/' + time.strftime("%Y%m%d%H%M%S", time.localtime()))
    # Func.execute是默认值，可以不用设置, 后期如果要使用其他自定义函数, 则在这设置
    strategyManagement.setFunc(execute)
    # 默认按1天切分任务, 如果要加粗切分粒度, 则在这设置
    strategyManagement.setDaysInterval(1)
    return strategyManagement


def addFactor(para):
    factorName = []
    tagName = []
    factorSet = para["FactorSet"]
    tagSet = para["TagNames"]

    for factor in factorSet:
        factorName.append(factor['name'])

    for tag in tagSet:
        tagName.append(tag)

    from xquant.factordata import FactorData
    fd = FactorData()

    try:
        fd.create_factor_library(para['LibraryName'], 'T+0')
    except:
        pass

    try:
        for fn in factorName:
            try:
                fd.add_factor(para['LibraryName'], [fn])
            except Exception as e:
                print(e)
                pass
        for tn in tagName:
            try:
                fd.add_factor(para['LibraryName'], [tn])
            except Exception as e:
                print(e)
                pass
    except:
        pass


def createStrategy(para):
    # 不用加StrategyManagement参数
    strategy = Strategy()
    strategy.setStrategyName(para["StrategyName"])
    if para["UseConfigTradingUnderlyingCode"] == "true":
        strategy.setTradingUnderlyingCode(para["TradingUnderlyingCode"])
    else:
        stocks = get_complete_stock_list(end_date)
        strategy.setTradingUnderlyingCode(stocks)
    strategy.setFactorUnderlyingCode(para["FactorUnderlyingCode"])
    strategy.setParaFactor(para["FactorSet"])
    strategy.setParaTag(para["Tag"])
    strategy.setStartDateTime(para["StartDateTime"])
    strategy.setEndDateTime(para["EndDateTime"])
    return strategy


def DataPrepare(para:dict):
    addFactor(para)
    strategyManagement = createStrategyManagement()
    strategy1 = createStrategy(para)
    # 单击版本中是在构造Strategy的init函数中进行register的, 这里必须额外调用registerStrategy方法
    strategyManagement.setLibraryName(para['LibraryName'])
    strategyManagement.registerStrategy(strategy1)
    strategyManagement.start()
    dataPath = strategyManagement.getDstDir()
    print("Factors and Tags output: " + dataPath)
    return dataPath


def getUserDir():
    # for i in range(1, len(sys.argv)):
    # if(str(sys.argv[i])=="--user" and i < len(sys.argv)):
    # return '/analysis/xquant/'+str(sys.argv[i+1])
    return '/analysis/xquant/' + '015618'


def get_complete_stock_list(end_date=None, drop_delisted_stocks=False):
    # revised on 2019/7/11-12 fixed the bug of delisting dates
    # 输入end_date, 则; 如drop_delisted_stocks为True, 则删去所有退市的股票
    complete_stock_list_path = "/data/user/666889/Apollo/AlphaDataBase/CompleteStockList.csv"
    complete_stock_list = []
    if os.path.exists(complete_stock_list_path):
        df = pd.read_csv(complete_stock_list_path)
        df = df.fillna(0)
        if drop_delisted_stocks:
            df = df[df.Delisting_date < 1]
        if end_date is None:
            complete_stock_list = df['Stock_code'].tolist()
        else:
            # 上市日期早于end_date的股票都要列出来
            df = df[df.Listing_date <= end_date]
            complete_stock_list = df['Stock_code'].tolist()
    else:
        print("Error: cannot find the CompleteStockList file")
    return [[stock] for stock in complete_stock_list]


def main():
    if start_date == end_date:
        touch_path = '/data/user/015618/HQF_Update_Log/{}'.format(end_date)
        if not os.path.exists(touch_path):
            os.mkdir(touch_path)
        with open(touch_path+'/{}_HFF.start'.format(end_date),'w') as f:
            pass
    print("start generating tags")
    DataPrepare(config)
    print("end")


if __name__ == "__main__":
    main()