# -*- coding: utf-8 -*-
"""
Created on Thu Aug 22 17:28:51 2019

@author: 013150
"""
import unittest
from version_control import version_number

if version_number == 0:
    from xquant.marketdata import MarketData
else:
    from xquant.thirdpartydata.marketdata import MarketData

import multiprocessing
from xquant.factordata import FactorData
fd = FactorData()

def multiprocess(func):

    lines = multiprocessing.cpu_count() - 1
    lines = 4
    pool = multiprocessing.Pool(processes=lines)
    print('start')
    pool_apply_async = {}
    for j in range(lines):
        pool.apply_async(func, (j,))

    pool.close()
    print('wait%sprocess to finish...' % lines)
    pool.join()
    print('finish!')
    return pool_apply_async

def get_tick_data(j):
    print("pid:"+str(j))
    ma = MarketData()
    df = ma.getMDSecurityTickDataFrame("601688.SH","20171201090000","20171201100000",0)
    print(df.head())
    
def get_tick_data1(j):
    print("pid:"+str(j))
    if version_number == 1:
        from xquant.marketdata import MarketData
    else:
        from MDCDataProvider import DataProvider as MarketData
    ma = MarketData()
    df = ma.get_data_by_date("Stock", "000001.SZ", "20180301", ["3"], sort_by_receive_time=True)
    print(df.head())

def test():
    fd = FactorData()
    df1 = fd.get_factor_value('Basic_factor', ['300161.SZ', '300135.SZ'], ['20180808', '20180809'], ['pre_close', 'open', 'high'])
    print(df1.head())
    return df1

class TestMultiProcessFactorData(unittest.TestCase):
    def test_mul_fac(self):
        a = test()
        pool_apply_async = multiprocess(get_tick_data)
    
    def test_mul_fac1(self):
        a = test()
        pool_apply_async = multiprocess(get_tick_data1)
