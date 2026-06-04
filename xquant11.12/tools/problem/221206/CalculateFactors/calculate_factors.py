import os
import json
import time
import datetime
from System.StrategyManagement import StrategyManagement
from System.Strategy import Strategy
from System.Func import execute
from System.GetTradingDay import getNDaysOff
from DataAPI.DataToolkit import get_complete_stock_list


def createStrategyManagement():
    strategyManagement = StrategyManagement()
    # 输出文件夹路径, 该路径为HDFS中的路径, 且事先必须不存在, here is the default value 
    userdir = getUserDir()
    if len(userdir) > 0:
        strategyManagement.setDstDir(userdir + '/output/' + 'ApolloFactor')
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
        strategy.setTradingUnderlyingCode([[stock] for stock in get_complete_stock_list(drop_delisted_stocks=True)])
    strategy.setFactorUnderlyingCode(para["FactorUnderlyingCode"])
    strategy.setParaFactor(para["FactorSet"])
    strategy.setParaTag(para["Tag"])
    strategy.setStartDateTime(para["StartDateTime"])
    strategy.setEndDateTime(para["EndDateTime"])
    return strategy


def DataPrepare(factorSetJsonFile, start_date, end_date):
    with open(factorSetJsonFile, 'r') as file:
        para = json.load(file)
        para["StartDateTime"] = int(start_date)
        para["EndDateTime"] = int(end_date)

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
    return '/analysis/xquant/' + '666888'


def main():
    today = datetime.datetime.now().strftime("%Y%m%d")
    # today = "20191206"
    start_date = str(getNDaysOff(int(today), 2)[0]) + "093015"
    end_date = today + "145659"

    configJsonfile = "FACTOR_CONFIG.py"
    father_path = os.path.abspath(os.path.realpath(__file__) + os.path.sep + "../")
    paramPath = father_path + "/" + configJsonfile
    print("Start generating factors and tags")
    print(start_date, end_date)
    DataPrepare(paramPath, start_date, end_date)
    print("End")


if __name__ == "__main__":
    main()
