import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
import time
import json
from System.StrategyManagement import StrategyManagement
from System.Strategy import Strategy
from System.Func import execute
from xquant.pyfile import Pyfile


def DataPrepare(factorSetJsonFile, StartDateTime, EndDateTime, output_dir, stock_list):
    # print(factorSetJsonFile, StartDateTime, EndDateTime, output_dir, stock_list)

    def createStrategyManagement(output_dir):
        strategyManagement = StrategyManagement()
        # 输出文件夹路径, 该路径为HDFS中的路径, 且事先必须不存在, here is the default value
        userdir = getUserDir()
        if len(userdir) > 0:
            # strategyManagement.setDstDir(userdir+'/output/' + 'zhentou_20170624_20180824_remove_5_23')
            strategyManagement.setDstDir("{}/{}".format(userdir, output_dir))
            # strategyManagement.setTmpEnvDir(userdir)
        else:
            strategyManagement.setDstDir(
                '/analysis/xquant/666888/output/' + time.strftime("%Y%m%d%H%M%S", time.localtime()))
            # strategyManagement.setTmpEnvDir('/analysis/xquant/666888/')
        # Func.execute是默认值，可以不用设置, 后期如果要使用其他自定义函数, 则在这设置
        strategyManagement.setFunc(execute)
        # 默认按1天切分任务, 如果要加粗切分粒度, 则在这设置
        strategyManagement.setDaysInterval(1)
        return strategyManagement

    def createStrategy(para):
        # 不用加StrategyManagement参数
        strategy = Strategy()
        strategy.setStrategyName(para["StrategyName"])
        strategy.setTradingUnderlyingCode(para["TradingUnderlyingCode"])
        strategy.setFactorUnderlyingCode(para["FactorUnderlyingCode"])
        strategy.setParaFactor(para["FactorSet"])
        strategy.setParaTag(para["Tag"])
        strategy.setStartDateTime(para["StartDateTime"])
        strategy.setEndDateTime(para["EndDateTime"])
        return strategy

    with open(factorSetJsonFile, 'r') as file:
        para = json.load(file)
        para["StartDateTime"] = int(StartDateTime)
        para["EndDateTime"] = int(EndDateTime)
        para["TradingUnderlyingCode"] = stock_list

        strategyManagement = createStrategyManagement(output_dir)
        strategy1 = createStrategy(para)
        # 单击版本中是在构造Strategy的init函数中进行register的, 这里必须额外调用registerStrategy方法
        strategyManagement.registerStrategy(strategy1)
        strategyManagement.start()
        dataPath = strategyManagement.getDstDir()
        print("Factors and Tags output: " + dataPath)
        return dataPath


def getUserDir():
    # for i in range(1, len(sys.argv)):
        # if(str(sys.argv[i])=="--user" and i < len(sys.argv)):
            # return '/analysis/xquant/'+str(sys.argv[i+1])
    return '/analysis/xquant/'+'666888'


def main():
    import BT_NEW.BT_SMALL.CONFIG_SMALL as bt_config_small
    import BT_NEW.BT_BIG.CONFIG_BIG as bt_config_big
    config_small = bt_config_small.BacktestConfig()
    config_big = bt_config_big.BacktestConfig()
    output_dir = config_small.factor_pickle_output_dir
    StartDateTime = config_small.StartDateTime
    EndDateTime = config_small.EndDateTime
    # StartDateTime = '20190912093015'
    # EndDateTime = '20190916145659'
    factor_config = config_small.factor_config

    stock_codes = list(set(config_small.codes).union(set(config_big.codes)))
    py = Pyfile()

    if py.exists(output_dir):
        print('Removing old pickle factors from {}'.format(output_dir))
        py.delete(output_dir, recursive=True)

    configJsonfile = factor_config
    father_path = os.path.abspath(os.path.realpath(__file__) + os.path.sep + "../")
    paramPath = father_path + "/" + configJsonfile
    stock_list = [[stock] for stock in stock_codes]
    print("------Calculating factors for {} stocks using Spark------".format(len(stock_codes)))

    DataPrepare(paramPath, StartDateTime, EndDateTime, output_dir, stock_list)


if __name__ == '__main__':
    main()
