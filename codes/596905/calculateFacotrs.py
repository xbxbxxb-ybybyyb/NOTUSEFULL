import ray
from STOCK_LIST import STOCK_LIST
from Constants.CBOND_LIST import CBOND_LIST, CBOND_TEST_LIST
from NONFACTOR_CONFIG import NONFACTOR_CONFIG
from FACTOR_CONFIG import FACTOR_CONFIG
from System.CalculationScheduler import CalculationScheduler
from xquant.factordata import FactorData


def addFactors(libraryName, factorNames):
    fd = FactorData()

    for factorName in factorNames:
        try:
            fd.add_factor(libraryName, [factorName])
        except Exception as e:
            print(e)


def main(mdLibrary, factorLibrary, assetType, factorConfig, sDate, eDate, stockList, mode, dayUnit, stockUnit,
         maxExecutorNum, stockGroupNum, AIMRNum, sparkLogFilePath):
    factorNameList = [config["FactorName"] for config in factorConfig if "FactorName" in config] + ["timestamp"]
    addFactors(factorLibrary, factorNameList)

    calculationScheduler = CalculationScheduler()

    calculationScheduler.setMarketDataLibrary(mdLibrary)
    calculationScheduler.setFactorLibrary(factorLibrary)
    calculationScheduler.setAssetType(assetType)
    calculationScheduler.setFactorConfig(factorConfig)
    calculationScheduler.setStartDate(sDate)
    calculationScheduler.setEndDate(eDate)
    calculationScheduler.setStockListToBeCalculated(stockList)
    calculationScheduler.setMode(mode)
    calculationScheduler.setUnit(dayUnit=dayUnit, stockUnit=stockUnit)
    calculationScheduler.setMaxExecutorNum(maxExecutorNum)
    calculationScheduler.setStockGroupNum(stockGroupNum)
    calculationScheduler.setAIMRNum(AIMRNum)
    calculationScheduler.setSparkLogFilePath(sparkLogFilePath)

    calculationScheduler.startCalculation()


if __name__ == "__main__":
    # TODO
    marketDataLibrary = "XHFDataLib"
    outputLibrary = "FactorDevLib"
    # outputLibrary = "CBFactorDevLib"

    mode = "Spark"
    # For Local, Spark & Ray
    dayUnit = 1
    # For Local & Spark
    stockUnit = 1
    # For Spark
    maxExecutorNum = 600
    sparkLogFilePath = "015629/CalculationLog/log20191231/"
    # For Ray
    stockGroupNum = 1
    AIMRNum = 0

    startDate = 20190401
    endDate = 20191231
    # startDate = 20180102
    # endDate = 20191231

    assetType = "Stock"
    # assetType = "CB"

    stockList = STOCK_LIST
    # stockList = CBOND_TEST_LIST
    factorConfig = FACTOR_CONFIG #+ NONFACTOR_CONFIG

    # factorConfig = [
    #     {
    #         "FactorName": "factorWeightedReturns",
    #         "ClassName": "FactorWeightedReturns"
    #     },
    # ]

    main(marketDataLibrary, outputLibrary, assetType, factorConfig, startDate, endDate, stockList, mode, dayUnit,
         stockUnit, maxExecutorNum, stockGroupNum, AIMRNum, sparkLogFilePath)
