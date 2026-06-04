import os
import calendar
import sys
import traceback
import time
start_time = time.time()
sys.path.append('../')
sys.path.append('./')
from web_entry.utils import Kafka_producer, record_error_info
from tquant.strategy.tick_factor_backtest.TickFactorBacktest import RunFactorBacktest
from tquant import PsFactorData

# 计算相关的环境变量
origin_start_date = os.environ.get('start_date')
origin_end_date = os.environ.get('end_date')
security_id = os.environ.get('security_id')
factor_name = os.environ.get('factor_name')
label = os.environ.get('label')

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

# 解析环境变量中传的起止时间 具体到日
origin_start_date = origin_start_date.split('/')
start_date = '{}{}{}'.format(origin_start_date[0], origin_start_date[1], '01')
origin_end_date = origin_end_date.split('/')
last_day_of_month = str(calendar.monthrange(int(origin_end_date[0]), int(origin_end_date[1]))[1])
end_date = '{}{}{}'.format(origin_end_date[0], origin_end_date[1], last_day_of_month)
scene = os.environ.get('scene')
# 解析环境变量中所传的筛选阈值

select_options_ori = dict()

label_corr_threshold = {i.split(':')[0]: i.split(':')[1] for i in
                        os.environ.get("label_corr_threshold").split(',')} if os.environ.get(
    "label_corr_threshold") else None
normal_ic_threshold = {i.split(':')[0]: i.split(':')[1] for i in
                       os.environ.get("normal_ic_threshold").split(',')} if os.environ.get(
    "normal_ic_threshold") else None
rank_ic_threshold = {i.split(':')[0]: i.split(':')[1] for i in
                     os.environ.get("rank_ic_threshold").split(',')} if os.environ.get(
    "rank_ic_threshold") else None
skew_threshold = {i.split(':')[0]: i.split(':')[1] for i in
                  os.environ.get("skew_threshold").split(',')} if os.environ.get(
    "skew_threshold") else None
kurt_threshold = {i.split(':')[0]: i.split(':')[1] for i in
                  os.environ.get("kurt_threshold").split(',')} if os.environ.get(
    "kurt_threshold") else None
long_return_threshold = {i.split(':')[0]: i.split(':')[1] for i in
                         os.environ.get("long_return_threshold").split(',')} if os.environ.get(
    "long_return_threshold") else None
short_return_threshold = {i.split(':')[0]: i.split(':')[1] for i in
                          os.environ.get("short_return_threshold").split(',')} if os.environ.get(
    "short_return_threshold") else None
long_pval_threshold = {i.split(':')[0]: i.split(':')[1] for i in
                       os.environ.get("long_pval_threshold").split(',')} if os.environ.get(
    "long_pval_threshold") else None
short_pval_threshold = {i.split(':')[0]: i.split(':')[1] for i in
                        os.environ.get("short_pval_threshold").split(',')} if os.environ.get(
    "short_pval_threshold") else None
autocorr_threshold_1min = {i.split(':')[0]: i.split(':')[1] for i in
                           os.environ.get("autocorr_threshold_1min").split(',')} if os.environ.get(
    "autocorr_threshold_1min") else None
autocorr_threshold_3min = {i.split(':')[0]: i.split(':')[1] for i in
                           os.environ.get("autocorr_threshold_3min").split(',')} if os.environ.get(
    "autocorr_threshold_3min") else None
autocorr_threshold_5min = {i.split(':')[0]: i.split(':')[1] for i in
                           os.environ.get("autocorr_threshold_5min").split(',')} if os.environ.get(
    "autocorr_threshold_5min") else None
select_options_ori.update({"corr": label_corr_threshold,
                           "normal_ic": normal_ic_threshold, "rank_ic": rank_ic_threshold,
                           "skew": skew_threshold, "kurt": kurt_threshold,
                           "trade_long_return": long_return_threshold, "trade_short_return": short_return_threshold,
                           "short_p_value": short_pval_threshold, "long_p_value": long_pval_threshold,
                           "auto_corr_1": autocorr_threshold_1min, "auto_corr_3": autocorr_threshold_3min,
                           "auto_corr_5": autocorr_threshold_5min})

# 将获得的筛选条件进一步解析，解析成如下格式 按照方案存储为字典
# select_options的格式如下
# {
# 'case1': {'corr_threshold': 0.005, 'rank_ic': 0.06},
# 'case2': {'factor_label_corr_threshold': 0.5, 'short_pval_threshold': 0.01},
# 'case3': {'normal_ic': 0.06, 'short_return_threshold': 0.00015, 'autocorr_threshold_1min': 0.85}
# }
select_options = {}
for target, val in select_options_ori.items():
    if not select_options_ori[target]:
        continue
    for case_name,threshold in val.items():
        if case_name not in select_options:
            select_options[case_name] = {target: float(threshold)}
        else:
            select_options[case_name].update({target: float(threshold)})

rfb = RunFactorBacktest(n_jobs=8)
tps = PsFactorData()
factor_list = os.environ.get('factor_name').split(',')

# 因子互相关性的筛选阈值，用户不传的话默认是1
factor_crosscorr_threshold = float(os.environ.get("factor_corr_threshold").split(',')[0].split(':')[1]) if os.environ.get(
    "factor_corr_threshold") else 1
print("##############获取因子所在的因子库名##############")
# 临时方案，解决后调整
library_name = None
for factor_name in factor_list:
    try:
        library_name = tps.get_library_name_by_factor(factor_name, 'research')
    except:
        pass
    if library_name:
        break
try:
    print("#####################开始回测##################")
    mes_data, _ = rfb.run_factors_backtest(start_date=start_date, end_date=end_date, factor_list=factor_list,
                                           security_id=security_id, label=label, library_name=library_name,
                                           percent_list=percent_list, rolling_window=rolling_window,
                                           stratified_list=stratified_list, metric_xx='pearson',
                                           select_options=select_options,
                                           factor_crosscorr_threshold=factor_crosscorr_threshold)
    print("###################发送kafka消息##################")
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
