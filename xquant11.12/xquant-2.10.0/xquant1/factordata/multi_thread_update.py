import time
from factor import FactorData
fa = FactorData()
try:
    print(fa.create_factor_library("factor_update_test", "Alpha"))
    print(fa.add_factor("factor_update_test", ["open","close","high","low"]))
except:
    pass

days = fa.tradingday("20150101", "20191211")

if True:
    df = fa.get_factor_value("Basic_factor", [],days, ["open", "close", "high", "low"] )
    df = df.fillna('')

    t1 = time.time()
    # from perf import profile
    # func = profile(fa.update_factor_value)
    # func("factor_update_test", df, thread_num=10)
    #注：thread_num为并发更新因子的线程数，上限为mysql连接池的最大连接数，目前配置的最大连接数为20个，即最多有20个线程并发更新因子
    fa.update_factor_value("factor_update_test", df, thread_num = 10)

    print("update time:", time.time()-t1)

if True:
    stocks = fa.hset("MARKET", "20190701", "ALLA")["stock"].tolist()
    result_df = fa.get_factor_value("factor_update_test", stocks, days, ["open", "close", "high", "low"])
    print(result_df.head())
    print(result_df.shape)