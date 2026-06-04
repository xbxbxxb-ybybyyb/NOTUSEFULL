# -*- coding: utf-8 -*-
import pickle
import datetime as dt
from os import path
from System.DataBroadcast import DataBroadcast
from System import Utils
from System.RemotePrint import print as rp


def work(dfs, taskMeta, func, srcDir, dstDir, libraryName):
    """
    Executes the task specified by the taskMeta in the Spark Executors.

    :param dfs: HadoopFileSystem
    :param taskMeta: TaskMeta
    :param func: the UDF to process
    :param srcDir: str the source dir
    :param dstDir: str the destination dir
    """
    # dstDir0 = path.join(dstDir, '.tmp', str(taskMeta.getStrategyIndex()), str(taskMeta.getCodeGroupIndex()))
    # dstFile = path.join(dstDir0, str(taskMeta.getDayIndex()))
    # if dfs.exists(dstFile):
        # # 该任务之前已经完成（在有partition失效的情况下会发生），直接返回
        # return
    # tmpFile = path.join(dstDir0, '.tmp', '{}-{}'.format(taskMeta.getDayIndex(), Utils.randomFileName()))
    # dfs.mkdir(path.join(dstDir0, '.tmp'))
    # curDir = path.join(dstDir0, '.tmp')
    # for i in range(3):
        # dfs.chmod(curDir, 0o777)
        # curDir = path.dirname(curDir)
    # try:
        # with dfs.open(tmpFile, 'wb', buffer_size=1024) as writer:
            # broadcast = loadData(dfs, srcDir, taskMeta)
            # func(taskMeta.getStrategyBase().toStrategy(), broadcast, writer)
    # finally:
        # dfs.chmod(tmpFile, 0o666)
    # dfs.rename(tmpFile, dstFile)
    # t1 = dt.datetime.now()
    broadcast = loadData(dfs, srcDir, taskMeta)
    # t2 = dt.datetime.now()
    func(taskMeta, broadcast, libraryName)
    # t3 = dt.datetime.now()
    # rp("loadData time: {}, func time: {}".format((t2 - t1).total_seconds(), (t3 - t2).total_seconds()))


def loadData(dfs, srcDir, taskMeta):
    strategyBase = taskMeta.getStrategyBase()
    broadcast = DataBroadcast()
    broadcast.setTradingUnderlyingCode(taskMeta.getTradingUnderlyingCode())
    broadcast.setFactorUnderlyingCode(taskMeta.getFactorUnderlyingCode())
    broadcast.setStartDateTime(Utils.parseDateTime(strategyBase.getStartDateTime()))
    broadcast.setEndDateTime(Utils.parseDateTime(strategyBase.getEndDateTime()))
    daysStr = taskMeta.getDays()
    tradeDatesDT = [dt.datetime.strptime(date, '%Y/%m/%d').date() for date in daysStr]
    broadcast.setTradingDays(tradeDatesDT)
    broadcast.loadData(dfs, srcDir)
    return broadcast


def merge(dfs, dstDir, mergeMeta):
    strategyBase = mergeMeta.getStrategyBase()
    strategyIndex = mergeMeta.getStrategyIndex()
    codeGroupIndex = mergeMeta.getCodeGroupIndex()
    TradingUnderlyingCode = mergeMeta.getStrategyBase().getTradingUnderlyingCode()
    srcDir = path.join(dstDir, '.tmp', str(strategyIndex), str(codeGroupIndex))
    dstFile = path.join(dstDir, '{}-{}-{}-{}.pickle'.format(strategyBase.getStrategyName(), TradingUnderlyingCode[codeGroupIndex][0], str(strategyBase.getStartDateTime()), str(strategyBase.getEndDateTime())))
    if dfs.exists(dstFile):
        # 该任务之前已经完成（在有partition失效的情况下会发生），直接返回
        return
    tmpFile = path.join(dstDir, '.tmp', '{}-{}-{}'.format(strategyIndex, codeGroupIndex, Utils.randomFileName()))
    try:
        with dfs.open(tmpFile, 'wb', buffer_size=1024) as writer:
            for i in range(mergeMeta.getNumIntervals()):
                srcFile = path.join(srcDir, str(i))
                with dfs.open(srcFile, 'rb', buffer_size=1024) as reader:
                    while True:
                        s = reader.read(1024)
                        if s == b'':
                            break
                        writer.write(s)
    finally:
        dfs.chmod(tmpFile, 0o666)
    dfs.rename(tmpFile, dstFile)
