# -*- coding: utf-8 -*-
"""
Created on 2017/9/14 14:20

@author: 006547
"""
import pickle
import datetime as dt
from System import Codec


def dumpOutput(strategy):
    startTimeStamp = dt.datetime.timestamp(dt.datetime.now())
    with open(strategy.getStrategyName() + '.pickle') as f:
        subTag = []
        for i in range(strategy.getOutputTag().__len__()):
            subTag.append([])
            for j in range(strategy.getOutputTag()[i].__len__()):
                subTag[i].append(strategy.getOutputTag()[i][j].subTag)
        pickle.dump((strategy.getOutputFactor(), subTag, strategy.getTradingUnderlyingCode(),
                     strategy.getFactorName()), f)
    endTimeStamp = dt.datetime.timestamp(dt.datetime.now())
    print("Dump time: " + str(round((endTimeStamp - startTimeStamp) / 60, 2)) + " min")


def loadOutput(factorAddress, strategyName):
    startTimeStamp = dt.datetime.timestamp(dt.datetime.now())
    try:
        with open(factorAddress + strategyName) as f:
            print('Use local open')
            try:
                outputFactor = []
                outputSubTag = []
                outputFactor2, outputSubTag2, tradingUnderlyingCode, factorName = pickle.load(f)
                outputFactor.append(outputFactor2)
                outputSubTag.append(outputSubTag2)
                print('Use local pickle')
            except Exception:
                outputFactor = []
                outputSubTag = []
                outputFactor2, outputSubTag2, tradingUnderlyingCode, factorName = Codec.decode(f)
                outputFactor.append(outputFactor2)
                outputSubTag.append(outputSubTag2)
                print('Use Xquant pickle')
    except Exception:
        from xquant.xqutils.xqfile import HDFSFile
        hf = HDFSFile()
        with hf.open(factorAddress + strategyName) as f:
            outputFactor = []
            outputSubTag = []
            outputFactor2, outputSubTag2, tradingUnderlyingCode, factorName = Codec.decode(f)
            outputFactor.append(outputFactor2)
            outputSubTag.append(outputSubTag2)

    endTimeStamp = dt.datetime.timestamp(dt.datetime.now())
    # print("Load time: " + str(round((endTimeStamp - startTimeStamp) / 60, 2)) + " min")
    return outputFactor, outputSubTag, tradingUnderlyingCode, factorName
