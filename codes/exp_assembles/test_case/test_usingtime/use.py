import sys
import os
import pandas as pd
from datetime import datetime

current_file_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(current_file_path)
sys.path.append(parent_directory)
from save import MongoDB
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

mdb = MongoDB()
exp_id = "test_exp"
version_alias = "test"
symbol = "00001.SZ"
evaluation_type = "123"
condition = {
    "test1": 1,
    "test2": "abc",
    "test3": ["q", "w", "e"],
}
create_time = "2023-10-30"
datetime1 = datetime.now()
metrics = pd.read_parquet('new_th_eva.parquet')
mdb.signal_evaluation_data_todb(exp_id, version_alias, symbol, evaluation_type, condition, metrics,
                                create_time)
usetime = datetime.now() - datetime1
print("方案一，其余字段插入metrics中，批量插入，接口总耗时")
print(usetime)

datetime2 = datetime.now()
mdb.signal_evaluation_data_todb2(exp_id, version_alias, symbol, evaluation_type, condition, metrics,
                                 create_time)
usetime2 = datetime.now() - datetime2
print("方案二，metrics读成列表，一条条插入，接口总耗时")
print(usetime)

datetime3 = datetime.now()
for i in range(1, 982):
    metrics2 = pd.read_parquet('th_eva.parquet')
    mdb.signal_evaluation_data_todb(exp_id, version_alias, symbol, evaluation_type, condition, metrics2,
                                    create_time)
usetime3 = datetime.now() - datetime3
print("方案三，每个parquet100*9，整体放到一个数组中，一条条插入，每条包含一天的数据，接口总耗时")
print(usetime3)
