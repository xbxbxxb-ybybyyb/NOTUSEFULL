import os
import ray
from xquant.factordata import FactorData
import time
import sys
import pandas as pd
from datetime import datetime
from stock_pool import get_stock_pool

@ray.remote(max_calls=5)
def UpdateL3Data(stock_code, trade_date, overwrite = True):
    try:
        base_dir = "/dfs/group/800657/library/l3_data"
        if not overwrite and os.path.exists(os.path.join(base_dir, "{}/{}_{}.parquet".format(stock_code, stock_code, trade_date))):
            print(1111)
            return []
        from trade_mocker_rust import trade_mocker_rust as tmr
        tmk = tmr.trade_mocker_instance("L2P", trade_date, True)
        try:
            tmk.presist_l3_data(stock_code)
        except:
            return [(stock_code, trade_date)]
        import shutil
        try:
            if not os.path.exists(os.path.join(base_dir, stock_code)):
                os.mkdir(os.path.join(base_dir, stock_code))
        except Exception as e:
            print(e)
        shutil.move("{}_{}.parquet".format(stock_code, trade_date),
                    os.path.join(base_dir, "{}/{}_{}.parquet".format(stock_code, stock_code, trade_date)))
        return []
    except Exception as e:
        print(stock_code, trade_date, e)


if __name__ == "__main__":
    local_mode = False
    if local_mode:
        symbol = sys.argv[1]
        date = sys.argv[2]
        UpdateL3Data.remote(symbol, date)
    else:
        date = sys.argv[1]
        ray.init(num_cpus = 30)
        fa = FactorData()
        symbols = get_stock_pool("ALL")
        dates = fa.tradingday(date)
        now_date = datetime.now().strftime("%Y%m%d")
        dates = [date for date in dates if now_date>=date]
        tasks = []
        remote_func = UpdateL3Data
        for symbol in symbols:
            for date in dates[::-1]:
                tasks.append(remote_func.remote(symbol, date))
        error_date = ray.get(tasks)
        error_date = [i for i in error_date if not len(i)==0]
        print("error_date:", error_date)


