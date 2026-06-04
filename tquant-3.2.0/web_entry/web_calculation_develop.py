import os
import time
import sys
import calendar
import traceback
sys.path.append('../')
sys.path.append('./')

# from FactorProvider.conf.TDubboConf import get_jurisdictionData
from web_entry.utils import web_calculation, send_personal_factor_trace, record_error_info
start_time = time.time()
factor_name = os.environ.get('factor_name')
origin_start_date = os.environ.get('start_date')
origin_end_date = os.environ.get('end_date')
file_path = os.environ.get('file_path')
sample_inner_startdate = os.environ.get('sample_inner_startdate')
sample_inner_enddate = os.environ.get('sample_inner_enddate')

if sample_inner_startdate and sample_inner_enddate:
    origin_start_date_tmp = origin_start_date.split('/')
    start_date = '{}{}{}'.format(origin_start_date_tmp[0], origin_start_date_tmp[1],
                                 '01')
    origin_end_date_tmp = origin_end_date.split('/')
    last_day_of_month = str(
        calendar.monthrange(int(origin_end_date_tmp[0]), int(origin_end_date_tmp[1]))[
            1])
    end_date = '{}{}{}'.format(origin_end_date_tmp[0], origin_end_date_tmp[1],
                               last_day_of_month)
    sample_inner_startdate = sample_inner_startdate.replace('/', '') + '01'
    sample_inner_enddate = sample_inner_enddate.replace('/', '') + '31'
    if start_date < sample_inner_startdate:
        raise Exception('开始时间{}小于样本内起始时间{}'.format(start_date, sample_inner_startdate))
    if end_date > sample_inner_enddate:
        raise Exception('结束时间{}大于样本内结束时间{}'.format(end_date, sample_inner_enddate))
else:
    print('环境变量sample_inner_startdate或sample_inner_enddate不存在')

try:
    web_calculation(factor_name, origin_start_date, origin_end_date, file_path, 'research', mode='save')
except Exception as e:
    record_error_info(factor_name, traceback.format_exc())
    raise e
finally:
    send_personal_factor_trace('web_calculation_release', factor_name,
                               origin_start_date, origin_end_date,
                               calc_env='research')
    end_time = time.time()
    print('Calc Task Interval: {}--{}'.format(origin_start_date, origin_end_date))
    print('produceTime', end_time - start_time)
