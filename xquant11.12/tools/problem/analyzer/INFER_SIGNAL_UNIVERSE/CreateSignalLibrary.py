#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/4/11 23:10
import pandas as pd
from xquant.factordata import FactorData


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

    signalLibraryList = ["BigAlgo20191101_1029"]
    signalColumns =   {
                            "Timestamp": "timestamp",
                            "Ticktime": "ticktime",
                            "1minLong": "prediction1minLong",
                            "1minShort": "prediction1minShort",
                            "2minLong": "prediction2minLong",
                            "2minShort": "prediction2minShort",
                            "5minLong": "prediction5minLong",
                            "5minShort": "prediction5minShort",
                            "1minLongTag": "tag1minLong",
                            "1minShortTag": "tag1minShort",
                            "2minLongTag": "tag2minLong",
                            "2minShortTag": "tag2minShort",
                            "5minLongTag": "tag5minLong",
                            "5minShortTag": "tag5minShort"
                        }

    factorNames = list(signalColumns.values())
    for signalLibrary in signalLibraryList:
        createLibrary(signalLibrary, factorNames)