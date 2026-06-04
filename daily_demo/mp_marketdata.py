#from xquant.marketdata import MarketData
from MDCDataProvider.DataProvider import DataProvider as MarketData
#from MDCDataProvider.HBaseProvider import HBaseProvider as MarketData
import multiprocessing
from xquant.factordata import FactorData
from xquant.futuredata import FutureData
fd = FactorData()
stocks = fd.hset("MARKET", "20190701","ALLA")["stock"]
#ma = MarketData()

def get_tick_data1(j):
    #fa = FactorData()
    #print(fa)
    
    #ma = MarketData()
    #df = ma.get_data_by_date("Transaction",j, "20200818", sort_by_receive_time=True)
    #print(df.shape)
    #fd = FutureData()
    #result = fd.get_change_date('IC','20200309','ZL00')
    #print(result)

    #print(time.time())a
    with open("a.txt", 'a') as f:
        print(j)
        f.writelines(str(j)+"\n")
    return None

def call_back(j):
    print(j)

if __name__=="__main__":

    lines = multiprocessing.cpu_count()-1
    lines = 10
    pool = multiprocessing.Pool(processes=lines)
    print('start')
    pool_apply_async = {}
    for j in stocks:
        pool.apply_async(get_tick_data1, (j,), callback=call_back)

    pool.close()
    print('wait%sprocess to finish...' % lines)
    pool.join()
    print('finish!')

