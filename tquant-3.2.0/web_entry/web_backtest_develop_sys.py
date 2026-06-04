import os
import sys
import pandas as pd
import time
import datetime as dt
sys.path.append('../')
sys.path.append('./')
from web_entry.utils import web_calculation, Kafka_producer, trans_enddate, record_error_info
from tquant.strategy.day_factor_backtest_new.FactorBacktest import DayFactorBacktest
import traceback

def backtest_release():
    start_time = time.time()
    msg_type = "backtest_system"
    start_date = os.environ.get('start_date')
    end_date = os.environ.get('end_date')
    result_folder = '/home/appadmin/'
    file_path = os.environ.get('file_path')
    factor_name = os.environ.get('factor_name')
    universe = os.environ.get('universe')
    benchmark = os.environ.get('benchmark')
    transaction_cost = float(os.environ.get('transaction_cost', 0.0))
    holding_period = int(os.environ.get('holding_period'))
    segment_number = int(os.environ.get('segment_number'))
    median = bool(int(os.environ.get('median')))
    standard = bool(int(os.environ.get('standard')))
    fillna = bool(int(os.environ.get('fillna')))
    seg_by_industry = bool(int(os.environ.get('seg_by_industry')))
    industry_type = os.environ.get('industry_type')
    neutralize = bool(int(os.environ.get('neutralize')))
    if industry_type != "CITIC_I":
        industry_type = 'CITIC_I'

    scene = os.environ.get('scene')
    kafka = Kafka_producer(scene)
    end_date = trans_enddate(end_date)
    try:
        start_date = dt.datetime.strptime(start_date, '%Y/%m/%d').strftime('%Y%m%d')
    except:
        pass
    try:
        end_date = dt.datetime.strptime(end_date, '%Y/%m/%d').strftime('%Y%m%d')
    except:
        pass

    factor_data = web_calculation(factor_name, start_date, end_date, file_path, calc_env='research', mode='show')[
        factor_name]
    # factor_data.drop('Factor', axis=1, inplace=True)
    # factor_data.index = pd.DatetimeIndex(factor_data.index)
    try:
        mes_data = DayFactorBacktest(start_date, end_date, factor_name, factor_data, result_folder, universe=universe,
                                     benchmark=benchmark, transaction_cost=transaction_cost, holding_period=holding_period,
                                     segment_number=segment_number, median=median, standard=standard, fillna=fillna,
                                     seg_by_industry=seg_by_industry, industry_type=industry_type, msg_type=msg_type,
                                     neutralize=neutralize)
        kafka.send_json_data(mes_data)
        print("kafka消息发送成功！内容如下：")
        print(mes_data)
    except Exception as e:
        traceback.print_exc()
        record_error_info(factor_name, traceback.format_exc())
        raise e
    finally:
        end_time = time.time()
        print('produceTime', end_time - start_time)


if __name__ == '__main__':
    backtest_release()
