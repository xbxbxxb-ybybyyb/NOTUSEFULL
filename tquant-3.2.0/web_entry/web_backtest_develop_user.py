import os
import sys
import time
sys.path.append('../')
sys.path.append('./')
from web_entry.utils import get_psfactor_data, date_parser, Kafka_producer, record_error_info, backtest_params_parser
from tquant.strategy.day_factor_backtest_new.FactorBacktest import DayFactorBacktest
import traceback

def backtest_develop():
    start_time = time.time()
    msg_type = "backtest_user"
    result_folder = '/home/appadmin/'
    industry_type = os.environ.get('industry_type')
    start_date = os.environ.get('start_date')
    end_date = os.environ.get('end_date')
    factor_name = os.environ.get('factor_name', 'ZaoYinTrader')
    universe = os.environ.get('universe')
    benchmark = os.environ.get('benchmark')
    transaction_cost = float(os.environ.get('transaction_cost', 0.0))
    holding_period = int(os.environ.get('holding_period'))
    segment_number = int(os.environ.get('segment_number'))
    median = bool(int(os.environ.get('median')))
    standard = bool(int(os.environ.get('standard')))
    fillna = bool(int(os.environ.get('fillna')))
    seg_by_industry = bool(int(os.environ.get('seg_by_industry')))
    neutralize = bool(int(os.environ.get('neutralize')))
    ret_stability = bool(int(os.environ.get('ret_stability'))) if os.environ.get('ret_stability') else True
    segment_switch = bool(int(os.environ.get('segment_switch'))) if os.environ.get('segment_switch') else True
    scene = os.environ.get('scene')

    backtest_report_module = backtest_params_parser(segment_switch, seg_by_industry, ret_stability)
    if industry_type != "CITIC_I":
        industry_type = 'CITIC_I'
    kafka = Kafka_producer(scene)
    # # ----------
    # import pandas as pd
    # factor_data = pd.read_pickle('ZaoYinTrader.pkl')
    # factor_data = factor_data[
    #     (factor_data.index >= pd.Timestamp(str(start_date))) & (factor_data.index <= pd.Timestamp(str(end_date)))]
    # # -------------
    start_date, end_date = date_parser(start_date, end_date)
    library_type = "research"
    factor_data = get_psfactor_data(start_date, end_date, factor_name, library_type)
    try:
        mes_data = DayFactorBacktest(start_date, end_date, factor_name, factor_data, result_folder, universe=universe,
                                 benchmark=benchmark, transaction_cost=transaction_cost, holding_period=holding_period,
                                 segment_number=segment_number, median=median, standard=standard, fillna=fillna,
                                 seg_by_industry=seg_by_industry, industry_type=industry_type, msg_type=msg_type,
                                 neutralize = neutralize, module=backtest_report_module)
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
    backtest_develop()
