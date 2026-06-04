# -*- coding: utf-8 -*-
import sys
import datetime as dt
import struct
import pickle
import time
import random
import pandas as pd
from xquant.factordata import FactorData
from System.RemotePrint import print

def parseDate(time):
    year = time // 10000000000
    month = (time - year * 10000000000) // 100000000
    day = (time - year * 10000000000 - month * 100000000) // 1000000
    return dt.date(year, month, day)


def parseDateTime(time):
    year = time // 10000000000
    month = (time - year * 10000000000) // 100000000
    day = (time - year * 10000000000 - month * 100000000) // 1000000
    hour = (time - year * 10000000000 - month * 100000000 - day * 1000000) // 10000
    minute = (time - year * 10000000000 - month * 100000000 - day * 1000000 - hour * 10000) // 100
    second = time - year * 10000000000 - month * 100000000 - day * 1000000 - hour * 10000 - minute * 100
    return dt.datetime(year, month, day, hour, minute, second)


def randomFileName():
    # 保证线程安全
    threadRandom = random.Random()
    threadRandom.seed(time.time())
    return str(threadRandom.randint(0, sys.maxsize))


def encodeOutputs(factors, subTags, tradingUnderlyingCode, factorName, writer):
    dump = pickle.dumps((factors, subTags, tradingUnderlyingCode, factorName))
    size = len(dump)
    writer.write(struct.pack('!I', size))
    writer.write(dump)

def output2HBase(factors, subTags, tradingUnderlyingCode, factorName, libraryName, taskMeta):
    date = taskMeta.getDays()[-1].replace('/', '')
    factor_data = FactorData()
    timestamps = {"timestamp": []}
    tags = {}
    tag_names = []
    for name in subTags[0].keys():
        tags[name] = []
        tag_names.append(name)

    for index in range(len(subTags)):
        timestamp = subTags[index][tag_names[0]].startTimeStamp
        timestamps["timestamp"].append(timestamp)
        for name in tag_names:
            tags[name].append(subTags[index][name].returnRate)

    tag_df = pd.DataFrame(tags).rename(
        columns={
            "1minLong": "tag1minLong",
            "1minShort": "tag1minShort",
            "2minLong": "tag2minLong",
            "2minShort": "tag2minShort",
            "5minLong": "tag5minLong",
            "5minShort": "tag5minShort",
            "10minLong": "tag10minLong",
            "10minShort": "tag10minShort"
        }
    )
    time_df = pd.DataFrame(timestamps)
    factor_df = pd.DataFrame(data=factors, columns=factorName)

    out_df = pd.concat([time_df, factor_df, tag_df], axis=1)
    factor_data.update_factor_value(libraryName, out_df, tradingUnderlyingCode[0], date)
    # print("update finish!")