import os

os.environ['exec_env'] = 'sit-prd'
os.environ['scene'] = 'trace'
os.environ['uuid'] = '1aa47395-41bf-4c55-bdc0-d5690b617ea5'
os.environ['factor_name'] = 'ceshi615'
os.environ['start_date'] = '2019/01/01'
os.environ['end_date'] = '2019/06/30'
os.environ['file_path'] = '/app/mount/code/test0914/'
os.environ['space_id'] = '366097404e7f4bc8b21b1bdd5dc015d4'
os.environ['developer'] = 'lhkj_default'
os.environ['shared_factor'] = 'lhkj_ceshi615'
os.environ['shared_library'] = '3'



import time
import sys
sys.path.append('../')
sys.path.append('./')

from web_entry.utils import web_calculation, Kafka_producer

start_time = time.time()
factor_name = os.environ.get('factor_name')
origin_start_date = os.environ.get('start_date')
origin_end_date = os.environ.get('end_date')
file_path = os.environ.get('file_path')
shared_factor = os.environ.get('shared_factor')
shared_library = os.environ.get('shared_library')
factor_type = 'system' if shared_factor and str(shared_library) == '3' else 'space' # 判断是否是空间因子
save_mode = 'sql' if factor_type == 'system' else 'parquet'

# kp = Kafka_producer(topic='HTSC-QUANT-FACTOR-DATASYNC', scene='date_range')
# kp.send_data_range(origin_start_date, origin_end_date, factor_name, shared_library, 'start')
# try:
#     web_calculation(factor_name, origin_start_date, origin_end_date, file_path, mode='save', save_mode=save_mode)
#     task_status = '2'
# except Exception as e:
#     task_status = '4'
#     raise e
# finally:
#     kp.send_data_range(origin_start_date, origin_end_date, factor_name,
#                        shared_library, 'stop', task_status=task_status)
#     end_time = time.time()
#     print('produceTime', end_time - start_time)
# 系统因子的脚本要在补数之后 计算回测指标
if shared_library == '3' and shared_factor:
    from tquant.strategy.market_factor_backtest.market_factor_entry_daily import backtest_factor_by_params_his
    from tquant import StockData, BasicData
    sd = StockData()
    bd = BasicData()
    origin_start_date = origin_start_date.replace("/","")
    origin_end_date = origin_end_date.replace("/","")
    date_list = bd.get_trading_day(origin_start_date, origin_end_date)
    factor_df = sd.get_factor_characteristic(factor_list=[shared_factor], date_list=date_list, sort=True)
    print(factor_df)
    backtest_factor_by_params_his(factor_df=factor_df, start_date=origin_start_date, end_date=origin_end_date, factor_name=shared_factor)

