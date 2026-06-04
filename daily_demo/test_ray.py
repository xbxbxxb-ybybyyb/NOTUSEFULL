# -*- coding: utf-8 -*-
import ray
from xquant.marketdata import MarketData
from xquant.factordata import FactorData
import sys

s = FactorData()
mdp = MarketData()

stock_list = s.hset("MARKET", "20180808","ALLA")["stock"]

ray.init(num_cpus=8, object_store_memory=15*1000000000)
@ray.remote
def ray_get_data(stock,date):
    mdp = MarketData()
    df = mdp.get_data_by_time_frame("Stock", stock,"20180301 093000000", "20180401 150000250",["3"], sort_by_receive_time=True)
    fa = FactorData()
    print(fa.get_factor_value("Basic_factor", [], ["20190701"], ["open"]))
    print(df.head())
    print("已结束")

    return "finish"

@ray.remote
def ray_get_factor(stock):
    from xquant.factordata import FactorData
    fa = FactorData()
    a = fa.hset("MARKET","20180808","ALLA")
    print(a.head())


@ray.remote
def ray_get_factor(stock):
    from xquant.factordata import FactorData
    fa = FactorData()
    a = fa.hset("MARKET","20180808","ALLA")
    print(a.head())

def main2():
    id_list = [ray_get_data.remote(stock, "20190701") for stock in stock_list[:]]
    #print(id_list)
    print(ray.get(id_list))


if __name__ == '__main__':
    main2()
