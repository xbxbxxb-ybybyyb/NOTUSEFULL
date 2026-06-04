import os
import time
import sys
import traceback
sys.path.append('../')
sys.path.append('./')

from web_entry.utils import web_calculation, Kafka_producer, send_personal_factor_trace, trans_enddate, record_error_info

start_time = time.time()
factor_name = os.environ.get('factor_name')
origin_start_date = os.environ.get('start_date')
origin_end_date = os.environ.get('end_date')

# origin_end_date 为td格式需要转换一下
origin_end_date = trans_enddate(origin_end_date)

file_path = os.environ.get('file_path')
shared_factor = os.environ.get('shared_factor')
shared_library = os.environ.get('shared_library')

factor_type = 'system' if shared_factor and str(shared_library) == '3' else 'space' # 判断是否是空间因子
save_mode = 'parquet'
if factor_type == 'system':
    save_mode = os.environ.get('save_mode')
    if save_mode == 'mysql':
        save_mode = 'sql'
    elif save_mode == 'nas':
        save_mode = 'parquet'
    elif save_mode not in ['mysql', 'nas', 'both']:
        raise Exception("环境变量save_mode有误，不识别：{}".format(save_mode))
if shared_library == '3' and shared_factor:
    kp = Kafka_producer(scene='date_range', topic='HTSC-QUANT-FACTOR-DATASYNC')
    kp.send_data_range(origin_start_date, origin_end_date, shared_factor, shared_library, 'start')

try:
    web_calculation(factor_name, origin_start_date, origin_end_date, file_path, mode='save', save_mode=save_mode)
    task_status = '2'
except Exception as e:
    task_status = '4'
    record_error_info(factor_name, traceback.format_exc())
    raise e
finally:
    if shared_library == '3' and shared_factor:
        kp.send_data_range(origin_start_date, origin_end_date, shared_factor, shared_library, 'stop', task_status=task_status)
    send_personal_factor_trace('web_calculation_release', factor_name, origin_start_date, origin_end_date)
    end_time = time.time()
    print('produceTime', end_time - start_time)

# 系统因子的脚本要在补数之后 计算回测指标
if shared_library == '3' and shared_factor:
    from tquant.strategy.market_factor_backtest.market_factor_entry_daily import backtest_factor_by_params_his
    from tquant import StockData, BasicData
    sd = StockData()
    bd = BasicData()
    origin_start_date = origin_start_date.replace("/", "")
    origin_end_date = origin_end_date.replace("/", "")
    date_list = bd.get_trading_day(origin_start_date, origin_end_date)
    print("============加载系统因子数据==================")
    factor_df = sd.get_factor_characteristic(factor_list=[shared_factor], date_list=date_list, sort=True)
    print("============开始计算回测指标并入库===============")
    backtest_factor_by_params_his(factor_df=factor_df, start_date=origin_start_date, end_date=origin_end_date,
                                  factor_name=shared_factor)

