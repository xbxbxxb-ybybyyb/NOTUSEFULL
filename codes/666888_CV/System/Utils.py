# -*- coding: utf-8 -*-
import sys
import datetime as dt
import struct
import pickle
import time
import random


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

