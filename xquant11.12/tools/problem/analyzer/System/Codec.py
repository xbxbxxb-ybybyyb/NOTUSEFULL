# -*- coding: utf-8 -*-
import struct
import pickle


def decode(reader):
    """
    Decodes (factors, subTags, tradingUnderlyingCode, factorNames) from the reader.

    :param reader: the file reader
    :return: the decoded tuple
    """
    factors = []
    subTags = []
    tradingUnderlyingCode = None
    factorNames = []
    while True:
        sizeStr = reader.read(4)
        if (sizeStr == b''):
            break
        if len(sizeStr) != 4:
            raise Exception('Length of size string is {}, which should be 4'.format(len(sizeStr)))
        size = struct.unpack('!I', sizeStr)[0]
        dump = reader.read(size)
        curFactors, curSubTags, curCode, curFactorNames = pickle.loads(dump)
        factors.extend(curFactors)
        subTags.extend(curSubTags)
        if not tradingUnderlyingCode:
            tradingUnderlyingCode = curCode
        elif tradingUnderlyingCode != curCode:
            raise Exception('TradingUnderlyingCode inconsistent: {} {}'.format(tradingUnderlyingCode, curCode))
        if factorNames.__len__() == 0:
            factorNames = curFactorNames
        elif curFactorNames.__len__() > 0 and factorNames != curFactorNames:
            raise Exception('FactorNames inconsistent: {} {}'.format(factorNames, curFactorNames))
    if not tradingUnderlyingCode:
        raise Exception('No tradingUnderlyingCode')
    if factorNames.__len__() == 0:
        raise Exception('No factorNames')
    return (factors, subTags, tradingUnderlyingCode, factorNames)
