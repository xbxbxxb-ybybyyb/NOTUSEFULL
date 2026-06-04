#from quanthbase import DataProvider
from dataprovider import DataProvider
import pandas as pd
import numpy as np
import time

compress_params = {
    "zlib": [1, 3, 9],
    "lzma": [1],
    "zstd": [1, 3, 10, 19, 22],
    "bz2": [1, 5, 9],
    # "protocol": [3, 4],
    # "optimize": [3, 4]
}


def round_test(dp, label, df_data, column_header, compress=None, level=0, jvm=False, cell_size=1):
    print("------------------------------------------------")
    library_name = "compresstest_0524_" + label + "_" + str(level)
    res = dp.create_factor_library(library_name)
    print("create library {} :{}".format(library_name, res))

    total_update_times = []
    total_get_times = []
    # for i in range(0, 100):
    t1 = time.time()
    if jvm:
        res = dp.update_factor_value_by_jvm(library_name, "symbol01", "20190329", df_data, cell_size=cell_size)
    else:
        res = dp.update_factor_value(library_name, "symbol01", "20190329", df_data, compress=compress, level=level)
    t2 = time.time()
    total_update_times.append(t2 - t1)
    print("update total time:{}".format(t2 - t1))
    res = dp.get_factor_value(library_name, "symbol01", "20190329", column_header, compress=compress)
    total_get_time = time.time() - t2
    total_get_times.append(total_get_time)
    print("get total time:{}".format(total_get_time))
        # if i != 99:
        #     res = dp.remove_factor_value(library_name, "symbol01", "20190329", high_list)
        #     res = dp.remove_factor(library_name, high_list)
    print("total update time mean:{} total get time mean:{}".format(np.mean(total_update_times), np.mean(total_get_times)))

# columns = 20000
# high_list = ["high1", "high2", "high3", "high4"]
# dates = pd.date_range('19010102', periods=columns)
# data = np.random.randint(0, columns, [columns, 4])
# df = pd.DataFrame(data, index=dates, columns=high_list)

origin_data = pd.read_csv("000001.SZ_20220518.csv")
columns_head = ['row'+str(i) for i in range(origin_data.shape[1])]
origin_data.columns = columns_head
dates = pd.date_range('19010102', periods=len(origin_data))

float64_data = origin_data.astype(np.float64)
float64_data['date'] = dates
float64_data = float64_data.set_index('date')

float32_data = origin_data.astype(np.float32)
float32_data['date'] = dates
float32_data = float32_data.set_index('date')

# check stream compress
dp = DataProvider()
for key, value in compress_params.items():
    for level in value:
        round_test(dp, key+"float64", float64_data, columns_head, key, level)
        round_test(dp, key+"float32", float32_data, columns_head, key, level)

#
# # check hbase compress
# # cell_size
# # SNAPPY
# round_test(dp, label="SNAPPY", df_data=float64_data, column_header=columns_head,)
# round_test(dp, label="SNAPPY_JVM_1", df_data=df, column_header=high_list, jvm=True, cell_size=1)
# round_test(dp, label="SNAPPY_JVM_5", df_data=df, column_header=high_list, jvm=True, cell_size=5)
# round_test(dp, label="SNAPPY_JVM_10", df_data=df, column_header=high_list, jvm=True, cell_size=10)
# round_test(dp, label="SNAPPY_JVM_20", df_data=df, column_header=high_list, jvm=True, cell_size=20)
# round_test(dp, label="SNAPPY_JVM_30", df_data=df, column_header=high_list, jvm=True, cell_size=30)
#
# # NONE
# dp_none = DataProvider(compression='NONE')
# round_test(dp_none, label="NONE", df_data=float64_data, column_header=columns_head,)
# round_test(dp_none, label="NONE_JVM_1", df_data=df, column_header=high_list, jvm=True, cell_size=1)
# round_test(dp_none, label="NONE_JVM_5", df_data=df, column_header=high_list, jvm=True, cell_size=5)
# round_test(dp_none, label="NONE_JVM_10", df_data=df, column_header=high_list, jvm=True, cell_size=10)
# round_test(dp_none, label="NONE_JVM_20", df_data=df, column_header=high_list, jvm=True, cell_size=20)
# round_test(dp_none, label="NONE_JVM_30", df_data=df, column_header=high_list, jvm=True, cell_size=30)
#
# # GZIP
# dp_gzip = DataProvider(compression='GZ')
# round_test(dp_gzip, label="GZ", df_data=float64_data, column_header=columns_head,)
# round_test(dp_gzip, label="GZ_JVM_1", df_data=df, column_header=high_list, jvm=True, cell_size=1)
# round_test(dp_gzip, label="GZ_JVM_5", df_data=df, column_header=high_list, jvm=True, cell_size=5)
# round_test(dp_gzip, label="GZ_JVM_10", df_data=df, column_header=high_list, jvm=True, cell_size=10)
# round_test(dp_gzip, label="GZ_JVM_20", df_data=df, column_header=high_list, jvm=True, cell_size=20)
# round_test(dp_gzip, label="GZ_JVM_30", df_data=df, column_header=high_list, jvm=True, cell_size=30)
#
# # LZ4
# dp_lz4 = DataProvider(compression='LZ4')
# round_test(dp_lz4, label="LZ4", df_data=float64_data, column_header=columns_head,)
# round_test(dp_lz4, label="LZ4_JVM_1", df_data=df, column_header=high_list, jvm=True, cell_size=1)
# round_test(dp_lz4, label="LZ4_JVM_5", df_data=df, column_header=high_list, jvm=True, cell_size=5)
# round_test(dp_lz4, label="LZ4_JVM_10", df_data=df, column_header=high_list, jvm=True, cell_size=10)
# round_test(dp_lz4, label="LZ4_JVM_20", df_data=df, column_header=high_list, jvm=True, cell_size=20)
# round_test(dp_lz4, label="LZ4_JVM_30", df_data=df, column_header=high_list, jvm=True, cell_size=30)

# test_float_32 64

# round_test(dp, "float64", float64_data, columns_head)
# round_test(dp, "float32", float32_data, columns_head)














