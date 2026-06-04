import ray
from xquant.factordata import FactorData
fa = FactorData()
import time 
import pandas as pd
import os


@ray.remote
def install_dolphin_depend_pkgs():
    #print("start install dolphindb")
    try: 
        os.system("pip install --no-cache-dir --no-deps /data/user/013150/tick_data/dol_pre_install_pkgs/pandas-0.25.1-cp36-cp36m-manylinux1_x86_64.whl >> out.log")
        os.system("pip install --no-cache-dir --no-deps /data/user/013150/tick_data/dol_pre_install_pkgs/dolphindb-1.30.0.12-cp36-cp36m-manylinux2010_x86_64.whl >> out.log")
    except:
        print("the pakgs have been installed!!!")
    #print("finish install dolphindb")
    return


@ray.remote        
def gen_stock_tick_data(date, stock):
    os.system("pip install --no-cache-dir --no-deps /data/user/013150/tick_data/dol_pre_install_pkgs/pandas-0.25.1-cp36-cp36m-manylinux1_x86_64.whl >> out.log")
    os.system("pip install --no-cache-dir --no-deps /data/user/013150/tick_data/dol_pre_install_pkgs/dolphindb-1.30.0.12-cp36-cp36m-manylinux2010_x86_64.whl >> out.log")

    import dolphindb as ddb
    print("=====================DolphinDB=========================")
    sites = ["168.17.249.123:8901", "168.17.249.124:8901"]
    s = ddb.session()
    print("Start connect")
    s.connect(host="168.17.249.123", port=8901, userid="admin", password="123456", highAvailability=True,
                highAvailabilitySites=sites)
    # s.connect(host="168.17.249.124", port=8901, userid="admin", password="123456")
    print("dolphindb connected !")
    date_dol = '.'.join([date[:4],date[4:6],date[6:]])
    res = s.run("""select * from loadTable("dfs://tick_stock", `outTable_tickStock) where date(timestamp)={date_dol}, symbol =='{stock}' """\
        .format(date_dol=date_dol, stock=stock))
    print(res.head())
    if len(res)==0:
            print('>'*50)
            print(stock)

    #res = s.run("""select * from tickdata""") 

    return res.head()


def main(date):
    stock_list = fa.hset("MARKET",date,"SZA")['stock'].to_list()
    # 和并发数保持一致
    #stock = '000001.SZ'
    #res_list = ray.get([gen_stock_tick_data.remote(date,stock) for _ in range(4)])

    # 一次只取一只标的
    res_list = ray.get([gen_stock_tick_data.remote(date,stock) for stock in stock_list])
    return res_list

if __name__ == '__main__':
    # ray.init('auto')
    ray.init(address='auto')
    date = '20211102'
    start = time.time()
    res = main(date)

    #print(res)
    print("finish time cost: {}".format(time.time()-start))