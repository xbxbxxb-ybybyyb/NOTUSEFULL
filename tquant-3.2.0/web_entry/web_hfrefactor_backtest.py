from tquant.strategy.tick_factor_backtest.TickFactorBacktest import RunFactorBacktest
import sys

sys.path.append('../')
sys.path.append('./')
from web_entry.utils import Kafka_producer, record_error_info
from tquant import PsFactorData
import os
import calendar
import traceback
import time

start_time = time.time()

# 获取单因子回测时的环境变量
origin_start_date = os.environ.get('start_date')
origin_end_date = os.environ.get('end_date')
security_id = os.environ.get('security_id')
factor_name = os.environ.get('factor_name')
label = os.environ.get('label')
scene = os.environ.get('scene')
percent01 = bool(int(os.environ.get('percent01')))
percent05 = bool(int(os.environ.get('percent05')))
stratified5 = bool(int(os.environ.get('stratified5')))
stratified10 = bool(int(os.environ.get('stratified10')))
percent_list = []
if percent01: percent_list.append(0.1)
if percent05: percent_list.append(0.5)
stratified_list = []
if stratified5: stratified_list.append(5)
if stratified10: stratified_list.append(10)
rolling_window = int(os.environ.get('rolling_window'))

origin_start_date = origin_start_date.split('/')
start_date = '{}{}{}'.format(origin_start_date[0], origin_start_date[1], '01')
origin_end_date = origin_end_date.split('/')
last_day_of_month = str(calendar.monthrange(int(origin_end_date[0]), int(origin_end_date[1]))[1])
end_date = '{}{}{}'.format(origin_end_date[0], origin_end_date[1], last_day_of_month)
tps = PsFactorData()
library_name = tps.get_library_name_by_factor(os.environ.get('factor_name').split(',')[0], 'research')
try:
    rfb = RunFactorBacktest(n_jobs=8)
    mes_data, _ = rfb.run_single_factor_backtest(start_date=start_date, end_date=end_date, security_id=security_id,
                                                 library_name=library_name, factor_name=factor_name, label=label,
                                                 percent_list=percent_list, rolling_window=rolling_window,
                                                 stratified_list=stratified_list)
    print("=====发送kafka消息=======")
    print(mes_data)
    kafka = Kafka_producer(scene)
    kafka.send_json_data(mes_data)
except Exception as e:
    traceback.print_exc()
    record_error_info(factor_name, traceback.format_exc())
    raise e

finally:
    end_time = time.time()
    print('produceTime', end_time - start_time)
