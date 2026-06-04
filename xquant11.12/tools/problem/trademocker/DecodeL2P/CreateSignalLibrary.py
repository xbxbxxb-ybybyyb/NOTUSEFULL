#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/4/11 23:10
from xquant.factordata import FactorData
from DecodeL2P.Config import LOG_TICK_HBASE_COLUMNS


def createLibrary(libraryName, factorList):
    fd = FactorData()

    try:
        fd.create_factor_library(libraryName, "T+0")
    except Exception as e:
        print(e)

    for factor in factorList:
        try:
            fd.add_factor(libraryName, [factor])
        except Exception as e:
            print(e)

if __name__ == "__main__":

    level2plus = False

    if level2plus:
        signalLibraryList = ["ZGLevel2PlusTicks"]
        factorNames = LOG_TICK_HBASE_COLUMNS
        for signalLibrary in signalLibraryList:
            createLibrary(signalLibrary, factorNames)
    else:
        from DataInterface.Config import TICK_STOCK_HBASE_COLUMNS

        marketDataLibrary = "ZGLevel2PlusDataLib"
        factorNames = TICK_STOCK_HBASE_COLUMNS
        createLibrary(marketDataLibrary, factorNames)
