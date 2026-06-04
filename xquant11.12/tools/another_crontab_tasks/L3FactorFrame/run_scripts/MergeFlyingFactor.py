from xquant.factordata import FactorData
import polars as pl
import os
import ray
import time
import pandas as pd
from datetime import datetime


def func(symbol, year, save_base_dir):
    fa = FactorData()
    library_info = fa.get_library_info()
    if symbol.endswith("SH"):
        lib = "HFMM_Factor_Library_PV0_SH_IT"
    else:
        lib = "HFMM_Factor_Library_PV0_SZ_IT"
    factor_list = library_info[lib]
    try:
        os.makedirs("{}/{}".format(save_base_dir, symbol))
    except:
        pass
    dates = fa.tradingday(year+"0101", year+"1231")
    now_date = datetime.now().strftime("%Y%m%d")
    dates = [date for date in dates if now_date >= date and date>="20230101"]
    print(dates)
    base_dir = "/dfs/group/800657/library/l3_event/event_data/"
    for date in dates:
        file_name = "{}/{}-{}.pqt".format(symbol, symbol, date)
        if os.path.exists(os.path.join(base_dir, file_name)):
            try:
                old_df = fa.get_factor_value(lib, symbol, date, factor_list, compress = True)
                new_columns = old_df.columns
                new_columns = [col.replace("factor", "Fac") for col in new_columns]
                new_columns = [col.replace("Ask", "Sell") for col in new_columns]
                new_columns = [col.replace("Bid", "Buy") for col in new_columns]
                new_columns = [col.replace("Consistency", "Cons") for col in new_columns]
                new_columns = [col.replace("Ratio", "Pct") for col in new_columns]
                new_columns = [col.replace("Zscore", "ZS") for col in new_columns]
                for value in ["10", "20", "30", "40", "50", "60", "70", "80", "90", "100"]:
                    new_columns = [col.replace(value, value[:-1]) for col in new_columns]
                old_df.columns = new_columns
            except:
                print(symbol, date)
                continue
            try:
                old_df =pl.from_pandas(old_df.rename(columns = {"dataIndex":"SeqNo"}))
                flying_df = pl.read_parquet(os.path.join(base_dir, file_name))
                flying_df = flying_df.cast({"SeqNo": pl.Int64})
                ############# 去除重名列, 保留新列 ############
                merge_df = old_df.join(flying_df, on = "SeqNo",  suffix='_right')
                target_columns = [col for col in merge_df.columns if "_right" not in col]
                merge_df = merge_df.select(target_columns)
                if not len(merge_df)==0:
                    merge_df.write_parquet(os.path.join(save_base_dir, file_name))
            except Exception as e:
                print("warning: {} {} {} empty!".format(symbol, date, e))

if __name__=="__main__":
    ######################注意修改存储路径####################
    fa = FactorData()
    # symbols_all = fa.hset("INDEX", "20240130", "000688.SH")["stock"].tolist()
    # symbols = symbols_all
    # symbols = ["688032.SH", "688041.SH", "688256.SH","688111.SH", "688271.SH","688012.SH", "688981.SH"]
    # symbols = set(symbols_all) - set(symbols)
    symbols = pd.read_csv("kc50.csv", header=None)[0].tolist()
    # symbols = pd.read_csv("zz500.csv", header=None)[0].tolist()
    symbols = [symbol for symbol in symbols if symbol.endswith("SH")]
    # symbols = ["688041.SH"]
    save_base_dir = "/dfs/group/800657/library/l3_event/merge_event_data/"
    ray.init(num_cpus=25, local_mode = False)
    ######################注意修改存储路径####################

    t1 = time.time()
    tasks = []
    remote_func = ray.remote(func)
    for symbol in symbols:
        for year in ['2023', "2024"]:
            tasks.append(remote_func.remote(symbol, year, save_base_dir=save_base_dir))
    ray.get(tasks)
    print("耗时：", time.time() - t1)