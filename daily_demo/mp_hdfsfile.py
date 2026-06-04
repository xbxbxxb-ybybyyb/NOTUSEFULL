import multiprocessing
from xquant.factordata import FactorData
from xquant.xqutils.xqfile import HDFSFile
#hdfsfile = HDFSFile()


def get_tick_data1(j):
    hdfsfile = HDFSFile()
    with hdfsfile.open("t0.json","rb") as f:
        print(1)
        print(f.read()[:10])
    return None

def call_back(j):
    print(j)

if __name__=="__main__":

    lines = multiprocessing.cpu_count()-1
    lines = 10
    pool = multiprocessing.Pool(processes=lines)
    print('start')
    pool_apply_async = {}
    for j in range(1000):
        pool.apply_async(get_tick_data1, (j,), callback=call_back)

    pool.close()
    print('wait%sprocess to finish...' % lines)
    pool.join()
    print('finish!')

