import os
import traceback
# 单因子回测的环境变量模拟
os.environ['start_date'] = '2019/01'
os.environ['end_date'] = '2019/02'
os.environ['file_path'] = './factors'
os.environ['scene'] = 'backtest'
os.environ['rolling_window'] = '20'
os.environ['percent01'] = '1'
os.environ['percent05'] = '1'
os.environ['stratified5'] = '1'
os.environ['stratified10'] = '1'

os.environ['DSWMAP_workspaceId'] = '4cf4b283246e4fa4824a9d4772fae'

if os.environ.get("exec_env") == 'prd':
    os.environ['file_path'] = './factors'
    os.environ['uuid'] = '84515e7c-8c04-4d95-a529-8bf2ef320987'
    os.environ['factor_id'] = '17'
    os.environ['factor_name'] = 'hfre_multi_sam'
    os.environ['space_id'] = '4cf4b283246e4fa4824a9d4772fae842'
    os.environ['project_id'] = 'd934130170e0435b85064fe21281ba0d'
    os.environ['developer'] = 'lhyj_lianghuaprd'
    os.environ['security_id'] = '000004.SZ'
    os.environ['label'] = 'label_multi_sam'
elif os.environ.get("exec_env") == 'sit-uat':
    os.environ['file_path'] = './factors'
    os.environ['uuid'] = '158bc340-01e9-4f5f-865a-8645c027e5e1'
    os.environ['factor_id'] = '76'
    os.environ['factor_name'] = 'fund15'
    os.environ['project_id'] = '563d085a96124a6b809b50d7bdd1c591'
    os.environ['space_id'] = '366097404e7f4bc8b21b1bdd5dc015d4'
    os.environ['developer'] = 'lhyj_lianghuauat'
    os.environ['security_id'] = '000001.SZ'
    os.environ['label'] = 'Label_test'

from tquant.strategy.tick_factor_backtest.TickFactorBacktest import RunFactorBacktest
import sys
sys.path.append('../')
sys.path.append('./')
from web_entry.utils import Kafka_producer
from tquant import PsFactorData
import calendar
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
# 调用高频回测的脚本
try:
    rfb = RunFactorBacktest(n_jobs=8)
    mes_data, _ = rfb.run_single_factor_backtest(start_date=start_date, end_date=end_date, security_id=security_id,
                                             library_name=library_name, factor_name=factor_name, label=label,
                                             percent_list=percent_list, rolling_window=rolling_window,
                                             stratified_list=stratified_list)
    print("=====发送kafka消息=======")
    print(mes_data)
except:
    traceback.print_exc()
finally:
    end_time = time.time()
    print('produceTime', end_time - start_time)

# 发送kafka消息
kafka = Kafka_producer(scene)
kafka.send_json_data(mes_data)
