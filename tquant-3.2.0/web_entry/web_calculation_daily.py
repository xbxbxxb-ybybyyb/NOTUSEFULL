import os
import time
from datetime import datetime
import sys
sys.path.append('../')
sys.path.append('./')
import traceback
from tquant.psfactor import PsFactorData
from SmartFactor.calculation.helper import get_docker_cpu, get_docker_memory
from web_entry.utils import web_calculation, Kafka_producer, record_error_info
from tquant import BasicData


now = datetime.now()
factor_id = os.environ.get('factor_id')
start_time = time.time()
factor_name = os.environ.get('factor_name')
psfactor = PsFactorData()
library_name = psfactor.get_library_name_by_factor(factor_name, 'release')

num_cpus = get_docker_cpu()
object_store_memory = get_docker_memory()
file_path = os.environ.get('file_path')
kafka = Kafka_producer('calc')

if 'DAY' in library_name:
    factor_type = 'day'
elif 'TICK' in library_name:
    factor_type = 'tick'
else:
    raise Exception('库名{}中不包含TICK或DAY'.format(library_name))

# 定时任务的时间 八点之前计算前一个交易日 八点之后计算当前交易日
# bd = BasicData()
# local_time = time.localtime()
# cur_time = time.strftime('%H:%M:%S', local_time)
# cur_date = time.strftime('%Y%m%d', local_time)
# if cur_time < '20:00:00':
#     calc_data = bd.get_trading_day(cur_date, -1)[0]
# else:
#     calc_date = cur_date

# 为了进行功能性测试 需要传一个历史时间作为任务
calc_date = '20191227'

json_msg = {
    "factorId": factor_id,
    "calcDate": calc_date,
    "createTime": now.strftime("%Y/%m/%d %H:%M:%S"),
    "calcjobStatus": "1"
}
kafka.send_json_data(json_msg)

status = '2'
try:
    web_calculation(factor_name, calc_date, calc_date, file_path, 'release',
                    mode='save')
except Exception as e:
    status = '3'
    record_error_info(factor_name, traceback.format_exc())
    raise e
finally:
    now = datetime.now()
    json_msg = {"factorId": factor_id,
                "calcDate":calc_date,
                "createTime": now.strftime("%Y/%m/%d %H:%M:%S"),
                "calcjobStatus": status}
    kafka.send_json_data(json_msg)
